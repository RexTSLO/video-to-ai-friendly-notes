import os
import yt_dlp

class VideoDownloadError(Exception):
    """Custom exception raised when video download fails."""
    pass


class VideoDownloader:
    """A downloader module that handles downloading high-quality compatible .mp4 videos from YouTube using yt-dlp."""

    def __init__(self, output_dir: str = "downloads") -> None:
        """Initialize the VideoDownloader with an output directory.

        Args:
            output_dir: The directory where the downloaded video will be saved.
        """
        self.output_dir = output_dir

    def download(self, url: str) -> str:
        """Download the video from the given URL and return its absolute path.

        Args:
            url: The YouTube video URL to download.

        Returns:
            The absolute path to the downloaded video file.

        Raises:
            VideoDownloadError: If the download or extraction fails.
        """
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Config for downloading highest quality mp4 merged video/audio
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            'noplaylist': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return os.path.abspath(filename)
        except yt_dlp.utils.DownloadError as e:
            raise VideoDownloadError(f"Failed to download video from {url}: {str(e)}") from e

