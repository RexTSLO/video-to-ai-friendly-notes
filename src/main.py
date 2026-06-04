import os
import sys
import argparse
import shutil
import tempfile

from src.downloader import VideoDownloader, VideoDownloadError
from src.transcriber import SubtitleTranscriber
from src.detector import SlideDetector
from src.generator import PDFGenerator

def main() -> None:
    """The master orchestrator CLI entrypoint for the video-slide-notes pipeline.

    Manages parameters parsing, setting up sandbox environments, sequential pipeline execution,
    and automatic cleanup of intermediate workspaces.
    """
    parser = argparse.ArgumentParser(
        prog="video-slide-notes",
        description="video-slide-notes: Transform any lecture video into highly structured, "
                    "AI-friendly PDFs containing synchronized slides and transcripts."
    )
    
    # Mode Options
    mode_group = parser.add_argument_group(
        "Mode Options",
        "Select the primary operation mode. If --list-subs is specified, the pipeline will only list available subtitles on YouTube and exit."
    )
    mode_group.add_argument(
        "--list-subs",
        action="store_true",
        help="List available subtitles (manual and automatic) for the YouTube video URL and exit."
    )

    # Input Options
    input_group = parser.add_argument_group("Input Options (Select one of the following)")
    ex_group = input_group.add_mutually_exclusive_group(required=True)
    ex_group.add_argument("-u", "--url", help="YouTube video URL to download.")
    ex_group.add_argument("-i", "--input", help="Local video file path.")

    # Pipeline Options
    pipeline_group = parser.add_argument_group(
        "Pipeline Options (Effective only in non --list-subs mode)",
        "Configure the slide detection, Whisper transcription, and PDF compilation settings."
    )
    pipeline_group.add_argument("-o", "--output", default="outputs/pdf/lecture_notes.pdf", help="Output destination PDF path.")
    pipeline_group.add_argument("-m", "--model", default="medium", help="Whisper model size (tiny, base, small, medium, large-v3).")
    pipeline_group.add_argument("-l", "--lang", default="zh", help="Language code (e.g. zh, en).")
    pipeline_group.add_argument("-t", "--threshold", default="auto", help="Slide change detection MAE threshold (float value, or 'auto' for dynamic thresholding).")
    pipeline_group.add_argument("-d", "--device", default="cpu", help="Computation device to use ('cpu' or 'cuda').")
    pipeline_group.add_argument("--subs-from-yt", default=None, help="Download specified subtitle language from YouTube directly (e.g., zh-TW), skipping Whisper.")
    pipeline_group.add_argument("--max-res", type=int, default=720, help="Maximum video resolution height to download (e.g., 480, 720, 1080).")
    pipeline_group.add_argument("--time-range", default=None, help="Download a specific section of the video in HH:MM:SS-HH:MM:SS format.")
    pipeline_group.add_argument("--srt", default=None, help="Path to a local .srt or .vtt subtitle file, skipping Whisper and YouTube subtitle downloads.")
    pipeline_group.add_argument("--min-duration", type=float, default=1.0, help="Minimum slide duration cooldown in seconds between two slide transitions (default: 1.0).")
    pipeline_group.add_argument("--slide-mode", default="final", choices=["final", "all", "first"], help="Slide animation capture strategy (default: final).")
    pipeline_group.add_argument(
        "--skip-talking-heads",
        action="store_true",
        help="Skip capturing duplicate speaker talking head frames by only keeping the first one until the next slide."
    )

    # Authentication Options
    auth_group = parser.add_argument_group(
        "Authentication Options (Optional, used to bypass 429 rate limits)",
        "Configure cookie sources to bypass YouTube rate limits (429 errors)."
    )

    auth_group.add_argument(
        "--cookies",
        default=None,
        help="Path to a cookies file in Netscape format."
    )

    args = parser.parse_args()

    # Clean up shell-escaping backslashes in YouTube URL if provided
    if args.url:
        import re
        args.url = re.sub(r'\\(.)', r'\1', args.url.strip("'\""))

    # Basic validation & foolproofing for --list-subs mode
    if args.list_subs:
        if not args.url:
            parser.error("--list-subs is only supported with a YouTube URL (-u/--url), not a local video file (-i/--input).")
        
        print(f"[*] Fetching available subtitles for YouTube URL: {args.url}...")
        try:
            subs_kwargs = {}

            if args.cookies:
                subs_kwargs['cookiefile'] = args.cookies
            subs = VideoDownloader.list_subtitles(args.url, **subs_kwargs)
            manual_subs = subs.get("manual", {})
            auto_subs = subs.get("auto", {})
            
            print("\n==================================================")
            print("Available Subtitles / Captions")
            print("==================================================")
            
            print("\n[Manual Subtitles]")
            if manual_subs:
                for lang_code, lang_name in sorted(manual_subs.items()):
                    print(f"  - {lang_code}: {lang_name}")
            else:
                print("  None")
                
            print("\n[Automatic Captions]")
            if auto_subs:
                for lang_code, lang_name in sorted(auto_subs.items()):
                    print(f"  - {lang_code}: {lang_name}")
            else:
                print("  None")
            print("==================================================\n")
            sys.exit(0)
        except VideoDownloadError as e:
            print(f"[-] Error listing subtitles: {str(e)}", file=sys.stderr)
            sys.exit(1)


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

        is_auto_sub = False
        video_path = args.input

        # 1. Download video if URL is provided (using temp_dir as sandbox to avoid corrupt partial files)
        if args.url:
            # If subs_from_yt is enabled, check availability on YouTube first before downloading
            if args.subs_from_yt and not args.srt:
                print(f"[*] Checking if subtitle '{args.subs_from_yt}' is available on YouTube...")
                try:
                    subs_kwargs = {}

                    if args.cookies:
                        subs_kwargs['cookiefile'] = args.cookies
                    subs = VideoDownloader.list_subtitles(args.url, **subs_kwargs)
                    manual_langs = subs.get("manual", {})
                    auto_langs = subs.get("auto", {})
                    if args.subs_from_yt not in manual_langs and args.subs_from_yt not in auto_langs:
                        raise ValueError(
                            f"Requested subtitle language '{args.subs_from_yt}' is not available on YouTube. "
                            f"Use --list-subs to check available subtitles."
                        )
                    is_auto_sub = (args.subs_from_yt not in manual_langs)
                    print(f"[+] Subtitle '{args.subs_from_yt}' is available (Auto-generated: {is_auto_sub}). Proceeding to download video.")
                except VideoDownloadError as e:
                    raise ValueError(f"Failed to check subtitle availability: {str(e)}") from e

            print(f"[*] Downloading video from {args.url}...")
            downloader_kwargs = {
                "output_dir": temp_dir,
                "max_res": args.max_res,
                "subs_from_yt": None if args.srt else args.subs_from_yt,
                "time_range": args.time_range
            }

            if args.cookies:
                downloader_kwargs["cookiefile"] = args.cookies

            downloader = VideoDownloader(**downloader_kwargs)
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
            subtitles = SubtitleTranscriber.parse_srt(temp_srt_path, deduplicate=is_auto_sub)
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
        detector = SlideDetector(
            threshold=args.threshold,
            min_slide_duration=args.min_duration,
            slide_mode=args.slide_mode,
            skip_talking_heads=args.skip_talking_heads
        )
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
