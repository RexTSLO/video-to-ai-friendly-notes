import os
from unittest.mock import patch, MagicMock
import pytest
import yt_dlp

from src.downloader import VideoDownloader, VideoDownloadError

def test_download_success(tmp_path):
    """Test successful video download with directory creation, correct options, and absolute path return."""
    output_dir = str(tmp_path / "custom_downloads")
    downloader = VideoDownloader(output_dir=output_dir)
    test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"

    # We mock yt_dlp.YoutubeDL
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        # Mock instance of YoutubeDL
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        
        # Define returned info
        mock_info = {"title": "Test Video", "ext": "mp4"}
        mock_ydl_instance.extract_info.return_value = mock_info
        
        # Mock prepare_filename to return the filename
        expected_filename = os.path.join(output_dir, "Test Video.mp4")
        mock_ydl_instance.prepare_filename.return_value = expected_filename

        # Act
        result_path = downloader.download(test_url)

        # Assertions
        # 1. VideoDownloader creates the directory
        assert os.path.exists(output_dir)
        
        # 2. yt_dlp.YoutubeDL is instantiated with the correct options
        expected_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'noplaylist': True,
        }
        mock_ydl_class.assert_called_once_with(expected_opts)
        
        # 3. extract_info is called with the correct URL
        mock_ydl_instance.extract_info.assert_called_once_with(test_url, download=True)
        
        # 4. download returns the absolute path correctly
        assert result_path == os.path.abspath(expected_filename)

def test_download_failure(tmp_path):
    """Test that VideoDownloadError is raised if a DownloadError occurs during extraction."""
    output_dir = str(tmp_path / "custom_downloads")
    downloader = VideoDownloader(output_dir=output_dir)
    test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"

    # We mock yt_dlp.YoutubeDL to raise DownloadError
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        
        # Raise DownloadError
        mock_ydl_instance.extract_info.side_effect = yt_dlp.utils.DownloadError("Some error message")

        # Act & Assert
        # 5. If a DownloadError occurs, the class properly raises VideoDownloadError
        with pytest.raises(VideoDownloadError) as exc_info:
            downloader.download(test_url)
        
        assert "Failed to download video from" in str(exc_info.value)
