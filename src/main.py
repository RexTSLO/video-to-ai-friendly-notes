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

    parser.add_argument("-o", "--output", default="outputs/lecture_notes.pdf", help="Output destination PDF path.")
    parser.add_argument("-m", "--model", default="medium", help="Whisper model size (tiny, base, small, medium, large-v3).")
    parser.add_argument("-l", "--lang", default="zh", help="Language code (e.g. zh, en).")
    parser.add_argument("-t", "--threshold", type=float, default=15.0, help="Slide change detection MAE threshold (lower = more sensitive).")
    parser.add_argument("-d", "--device", default="cpu", help="Computation device to use ('cpu' or 'cuda').")

    args = parser.parse_args()

    # Setup sandbox temporary working workspace
    temp_dir = tempfile.mkdtemp(prefix="vid2notes_")
    temp_img_dir = os.path.join(temp_dir, "frames")

    try:
        # Ensure the destination directory exists securely
        output_dir = os.path.dirname(os.path.abspath(args.output))
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        video_path = args.input

        # 1. Download video if URL is provided
        if args.url:
            print(f"[*] Downloading video from {args.url}...")
            downloader = VideoDownloader(output_dir=temp_dir)
            video_path = downloader.download(args.url)
            print(f"[+] Downloaded: {video_path}")

        if not video_path or not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at: {video_path}")

        # 2. Transcribe media audio to subtitle segments
        print(f"[*] Initializing transcription engine ({args.model} on {args.device})...")
        transcriber = SubtitleTranscriber(model_size=args.model, device=args.device)

        print("[*] Transcribing speech to subtitle segments...")
        subtitles = transcriber.transcribe(video_path, lang=args.lang)

        # Write intermediate .srt file alongside the PDF for reference
        srt_path = args.output.rsplit(".", 1)[0] + ".srt"
        transcriber.write_srt(subtitles, srt_path)
        print(f"[+] Subtitles generated and saved to: {srt_path}")

        # 3. Detect slide transition keyframes
        print("[*] Extracting slide transition frames...")
        detector = SlideDetector(threshold=args.threshold)
        keyframes = detector.detect_slides(video_path, temp_img_dir)
        print(f"[+] Extracted {len(keyframes)} slide frames.")

        # 4. Generate synchronized CJK PDF notes
        print("[*] Generating AI-friendly structured PDF notes...")
        generator = PDFGenerator()
        generator.generate(keyframes, subtitles, args.output)
        print(f"[++] SUCCESS: PDF lecture notes created at: {args.output}")

    except Exception as e:
        print(f"[-] ERROR occurred during pipeline processing: {str(e)}", file=sys.stderr)
        raise e
    finally:
        # Guarantee intermediate sandbox is cleanly purged from disk
        if os.path.exists(temp_dir):
            print("[*] Cleaning up temporary workspaces...")
            shutil.rmtree(temp_dir)
            print("[+] Workspace cleaned.")

if __name__ == "__main__":
    main()
