import os
import sys
import argparse
import shutil
import tempfile

from src.downloader import VideoDownloader
from src.transcriber import SubtitleTranscriber
from src.detector import SlideDetector
from src.generator import PDFGenerator

def main() -> None:
    """The master orchestrator CLI entrypoint for the video-to-ai-friendly-notes pipeline.

    Manages parameters parsing, setting up sandbox environments, sequential pipeline execution,
    and automatic cleanup of intermediate workspaces.
    """
    parser = argparse.ArgumentParser(
        prog="video-to-ai-friendly-notes",
        description="video-to-ai-friendly-notes: Transform any lecture video into highly structured, "
                    "AI-friendly PDFs containing synchronized slides and transcripts."
    )
    # Mutually exclusive group: requires either a YouTube URL or a Local Video path
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-u", "--url", help="YouTube video URL to download.")
    group.add_argument("-i", "--input", help="Local video file path.")

    parser.add_argument("-o", "--output", default="outputs/pdf/lecture_notes.pdf", help="Output destination PDF path.")
    parser.add_argument("-m", "--model", default="medium", help="Whisper model size (tiny, base, small, medium, large-v3).")
    parser.add_argument("-l", "--lang", default="zh", help="Language code (e.g. zh, en).")
    parser.add_argument("-t", "--threshold", type=float, default=15.0, help="Slide change detection MAE threshold (lower = more sensitive).")
    parser.add_argument("-d", "--device", default="cpu", help="Computation device to use ('cpu' or 'cuda').")

    args = parser.parse_args()

    # Smart Directory Dispatcher: Isolate output files based on types under outputs/ namespace
    target_output = args.output
    basename = os.path.basename(target_output).rsplit(".", 1)[0]
    parent_dir = os.path.dirname(target_output)

    if os.path.basename(parent_dir) == "pdf":
        base_out_dir = os.path.dirname(parent_dir)
    else:
        base_out_dir = parent_dir if parent_dir else "outputs"

    pdf_out_path = os.path.abspath(os.path.join(base_out_dir, "pdf", f"{basename}.pdf"))
    srt_out_path = os.path.abspath(os.path.join(base_out_dir, "subtitles", f"{basename}.srt"))
    slides_out_dir = os.path.abspath(os.path.join(base_out_dir, "slides", basename))

    # Setup sandbox temporary working workspace for secure downloading
    temp_dir = tempfile.mkdtemp(prefix="vid2notes_")

    try:
        # Defensively ensure all isolated output directories exist before writing
        os.makedirs(os.path.dirname(pdf_out_path), exist_ok=True)
        os.makedirs(os.path.dirname(srt_out_path), exist_ok=True)
        os.makedirs(slides_out_dir, exist_ok=True)
        os.makedirs("inputs", exist_ok=True)

        video_path = args.input

        # 1. Download video if URL is provided (using temp_dir as sandbox to avoid corrupt partial files)
        if args.url:
            print(f"[*] Downloading video from {args.url}...")
            downloader = VideoDownloader(output_dir=temp_dir)
            temp_video_path = downloader.download(args.url)
            
            # Safe Transfer: Move only successfully merged complete video to inputs/ directory
            video_filename = os.path.basename(temp_video_path)
            video_path = os.path.abspath(os.path.join("inputs", video_filename))
            shutil.move(temp_video_path, video_path)
            print(f"[+] Downloaded and safely stored at: {video_path}")

        if not video_path or not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at: {video_path}")

        # 2. Transcribe media audio to subtitle segments
        print(f"[*] Initializing transcription engine ({args.model} on {args.device})...")
        transcriber = SubtitleTranscriber(model_size=args.model, device=args.device)

        print("[*] Transcribing speech to subtitle segments...")
        subtitles = transcriber.transcribe(video_path, lang=args.lang)

        # Write srt file inside the isolated subtitles/ namespace
        transcriber.write_srt(subtitles, srt_out_path)
        print(f"[+] Subtitles generated and saved to: {srt_out_path}")

        # 3. Detect slide transition keyframes (directly save JPEGs inside slides/ namespace)
        print("[*] Extracting slide transition frames...")
        detector = SlideDetector(threshold=args.threshold)
        keyframes = detector.detect_slides(video_path, slides_out_dir)
        print(f"[+] Extracted {len(keyframes)} slide frames saved at: {slides_out_dir}")

        # 4. Generate CJK PDF lecture notes inside the isolated pdf/ namespace
        print("[*] Generating AI-friendly structured PDF notes...")
        generator = PDFGenerator()
        generator.generate(keyframes, subtitles, pdf_out_path)
        print(f"[++] SUCCESS: PDF lecture notes created at: {pdf_out_path}")

    except Exception as e:
        print(f"[-] ERROR occurred during pipeline processing: {str(e)}", file=sys.stderr)
        raise e
    finally:
        # Purge sandbox temp directory securely
        if os.path.exists(temp_dir):
            print("[*] Cleaning up temporary workspaces...")
            shutil.rmtree(temp_dir)
            print("[+] Workspace cleaned.")

if __name__ == "__main__":
    main()
