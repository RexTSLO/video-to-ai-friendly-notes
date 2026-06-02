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
    parser.add_argument("-t", "--threshold", default="auto", help="Slide change detection MAE threshold (float value, or 'auto' for dynamic thresholding).")
    parser.add_argument("-d", "--device", default="cpu", help="Computation device to use ('cpu' or 'cuda').")
    parser.add_argument("--subs-from-yt", default=None, help="Download specified subtitle language from YouTube directly (e.g., zh-TW), skipping Whisper.")
    parser.add_argument("--max-res", type=int, default=720, help="Maximum video resolution height to download (e.g., 480, 720, 1080).")
    parser.add_argument("--time-range", default=None, help="Download a specific section of the video in HH:MM:SS-HH:MM:SS format.")
    parser.add_argument("--srt", default=None, help="Path to a local .srt or .vtt subtitle file, skipping Whisper and YouTube subtitle downloads.")
    parser.add_argument("--min-duration", type=float, default=1.0, help="Minimum slide duration cooldown in seconds between two slide transitions (default: 1.0).")

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
    temp_srt_path = None

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
            downloader = VideoDownloader(
                output_dir=temp_dir,
                max_res=args.max_res,
                subs_from_yt=None if args.srt else args.subs_from_yt,
                time_range=args.time_range
            )
            temp_video_path, temp_srt_path = downloader.download(args.url)
            
            # Safe Transfer: Move only successfully merged complete video to inputs/ directory
            video_filename = os.path.basename(temp_video_path)
            video_path = os.path.abspath(os.path.join("inputs", video_filename))
            shutil.move(temp_video_path, video_path)
            print(f"[+] Downloaded and safely stored at: {video_path}")

        if not video_path or not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at: {video_path}")

        # 2. Transcribe media audio to subtitle segments or parse downloaded subtitles
        transcriber = SubtitleTranscriber(model_size=args.model, device=args.device)

        if args.srt:
            if not os.path.exists(args.srt):
                raise FileNotFoundError(
                    f"Specified local subtitle file not found at: {os.path.abspath(args.srt)}"
                )
            print(f"[*] Parsing specified local subtitles: {args.srt}...")
            subtitles = SubtitleTranscriber.parse_srt(args.srt)
            print(f"[+] Bypassed Whisper transcription & YouTube download. Subtitles loaded from local subtitle file successfully.")
        elif args.subs_from_yt:
            if not temp_srt_path or not os.path.exists(temp_srt_path):
                raise ValueError(
                    f"Requested subtitle language '{args.subs_from_yt}' could not be downloaded from YouTube."
                )
            print(f"[*] Parsing downloaded YouTube subtitles: {temp_srt_path}...")
            subtitles = SubtitleTranscriber.parse_srt(temp_srt_path)
            print(f"[+] Bypassed Whisper transcription. Subtitles loaded successfully.")
        else:
            print(f"[*] Initializing transcription engine ({args.model} on {args.device})...")
            print("[*] Transcribing speech to subtitle segments...")
            subtitles = transcriber.transcribe(video_path, lang=args.lang)

        # Write srt file inside the isolated subtitles/ namespace
        transcriber.write_srt(subtitles, srt_out_path)
        print(f"[+] Subtitles generated and saved to: {srt_out_path}")

        # 3. Detect slide transition keyframes (directly save JPEGs inside slides/ namespace)
        print("[*] Extracting slide transition frames...")
        detector = SlideDetector(threshold=args.threshold, min_slide_duration=args.min_duration)
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
