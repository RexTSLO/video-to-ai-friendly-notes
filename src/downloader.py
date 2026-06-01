import os
import yt_dlp

class VideoDownloadError(Exception):
    """Custom exception raised when video download fails."""
    pass


class VideoDownloader:
    """A downloader module that handles downloading high-quality compatible .mp4 videos from YouTube using yt-dlp."""

    def __init__(
        self,
        output_dir: str = "downloads",
        max_res: int = 720,
        subs_from_yt: str = None,
        time_range: str = None
    ) -> None:
        """Initialize the VideoDownloader with download configurations.

        Args:
            output_dir: The directory where the downloaded video will be saved.
            max_res: Maximum height resolution for the video (e.g., 480, 720, 1080).
            subs_from_yt: Target language code to download subtitles from YouTube (e.g. "zh-TW").
            time_range: Time range section to download in "HH:MM:SS-HH:MM:SS" format.
        """
        self.output_dir = output_dir
        self.max_res = max_res
        self.subs_from_yt = subs_from_yt
        self.time_range = time_range

    def download(self, url: str) -> tuple[str, str | None]:
        """Download the video from the given URL with options and return (video_path, subtitle_path).

        Args:
            url: The YouTube video URL to download.

        Returns:
            A tuple of (absolute_video_path, absolute_subtitle_path).
            absolute_subtitle_path is None if no subtitle was downloaded.

        Raises:
            VideoDownloadError: If the download, extraction, or time-range parsing fails.
        """
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Dynamic format based on max_res
        ydl_opts = {
            'format': f'bestvideo[height<={self.max_res}][ext=mp4]+bestaudio[ext=m4a]/best[height<={self.max_res}][ext=mp4]/best',
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            'noplaylist': True,
        }

        # Subtitles configuration
        if self.subs_from_yt:
            ydl_opts['writesubtitles'] = True
            ydl_opts['writeautomaticsub'] = True
            ydl_opts['subtitleslangs'] = [self.subs_from_yt]
            ydl_opts['convertsubtitles'] = 'srt'

        # Time range section configuration
        if self.time_range:
            def parse_time_to_seconds(time_str: str) -> float:
                parts = time_str.strip().split(":")
                if len(parts) == 3:
                    hrs = int(parts[0])
                    mins = int(parts[1])
                    secs = float(parts[2])
                    return hrs * 3600.0 + mins * 60.0 + secs
                elif len(parts) == 2:
                    mins = int(parts[0])
                    secs = float(parts[1])
                    return mins * 60.0 + secs
                else:
                    return float(parts[0])

            try:
                start_str, end_str = self.time_range.split("-")
                start_sec = parse_time_to_seconds(start_str)
                end_sec = parse_time_to_seconds(end_str)
                from yt_dlp.utils import download_range_func
                ydl_opts['download_ranges'] = download_range_func(None, [(start_sec, end_sec)])
                ydl_opts['force_keyframes_at_cuts'] = True
            except Exception as e:
                raise VideoDownloadError(
                    f"Invalid time range format: '{self.time_range}'. "
                    f"Expected 'HH:MM:SS-HH:MM:SS'. Error: {str(e)}"
                ) from e

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                video_path = os.path.abspath(filename)

                # Scan for the generated srt file in self.output_dir
                subtitle_path = None
                if self.subs_from_yt:
                    base_video_name = os.path.splitext(os.path.basename(video_path))[0]
                    expected_srt = os.path.join(self.output_dir, f"{base_video_name}.{self.subs_from_yt}.srt")
                    if os.path.exists(expected_srt):
                        subtitle_path = os.path.abspath(expected_srt)
                    else:
                        # Fallback search for .srt
                        for f in os.listdir(self.output_dir):
                            if f.endswith(".srt") and base_video_name in f:
                                subtitle_path = os.path.abspath(os.path.join(self.output_dir, f))
                                break
                    
                    # If no .srt found, look for .vtt and convert using FFmpeg
                    if not subtitle_path:
                        expected_vtt = os.path.join(self.output_dir, f"{base_video_name}.{self.subs_from_yt}.vtt")
                        vtt_path = None
                        if os.path.exists(expected_vtt):
                            vtt_path = os.path.abspath(expected_vtt)
                        else:
                            for f in os.listdir(self.output_dir):
                                if f.endswith(".vtt") and base_video_name in f:
                                    vtt_path = os.path.abspath(os.path.join(self.output_dir, f))
                                    break
                        if vtt_path:
                            srt_path = os.path.splitext(vtt_path)[0] + ".srt"
                            try:
                                import subprocess
                                subprocess.run(["ffmpeg", "-y", "-i", vtt_path, srt_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                                if os.path.exists(srt_path):
                                    subtitle_path = srt_path
                            except Exception as ffmpeg_err:
                                print(f"[-] WARNING: FFmpeg VTT to SRT conversion failed: {ffmpeg_err}")

                return video_path, subtitle_path
        except yt_dlp.utils.DownloadError as e:
            raise VideoDownloadError(f"Failed to download video from {url}: {str(e)}") from e
