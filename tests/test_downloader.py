import os
from unittest.mock import patch, MagicMock
import pytest
import yt_dlp

from src.downloader import VideoDownloader, VideoDownloadError

def test_download_video_default(tmp_path):
    """Test successful default video download returning (video_path, None)."""
    output_dir = str(tmp_path / "custom_downloads")
    downloader = VideoDownloader(output_dir=output_dir)
    test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        
        mock_info = {"title": "Test Video", "ext": "mp4"}
        mock_ydl_instance.extract_info.return_value = mock_info
        
        expected_filename = os.path.join(output_dir, "Test Video.mp4")
        mock_ydl_instance.prepare_filename.return_value = expected_filename

        os.makedirs(output_dir, exist_ok=True)
        with open(expected_filename, "w") as f:
            f.write("dummy")

        video_path, subtitle_path = downloader.download(test_url)

        assert os.path.exists(video_path)
        assert video_path.endswith(".mp4")
        assert subtitle_path is None
        
        expected_opts = {
            'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'noplaylist': True,
        }
        mock_ydl_class.assert_called_once_with(expected_opts)
        mock_ydl_instance.extract_info.assert_called_once_with(test_url, download=True)
        assert video_path == os.path.abspath(expected_filename)

def test_download_video_with_opts(tmp_path):
    """Test video download with all features enabled (subtitles, custom max_res, time_range)."""
    output_dir = str(tmp_path / "custom_downloads_opts")
    downloader = VideoDownloader(
        output_dir=output_dir,
        max_res=480,
        subs_from_yt="zh-TW",
        time_range="00:10:00-00:20:30"
    )
    test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        
        mock_info = {"title": "Test Video", "ext": "mp4"}
        mock_ydl_instance.extract_info.return_value = mock_info
        
        expected_video_filename = os.path.join(output_dir, "Test Video.mp4")
        expected_srt_filename = os.path.join(output_dir, "Test Video.zh-TW.srt")
        mock_ydl_instance.prepare_filename.return_value = expected_video_filename

        os.makedirs(output_dir, exist_ok=True)
        with open(expected_video_filename, "w") as f:
            f.write("dummy video")
        with open(expected_srt_filename, "w") as f:
            f.write("dummy srt")

        video_path, subtitle_path = downloader.download(test_url)

        assert os.path.exists(video_path)
        assert os.path.exists(subtitle_path)
        assert subtitle_path.endswith(".zh-TW.srt")
        
        # Verify ydl_opts contents
        called_args, called_kwargs = mock_ydl_class.call_args
        opts = called_args[0]
        
        # 1. format respects max_res = 480
        assert "height<=480" in opts['format']
        # 2. subs_from_yt set
        assert opts['writesubtitles'] is True
        assert opts['writeautomaticsub'] is True
        assert opts['subtitleslangs'] == ["zh-TW"]
        # 3. convertsubtitles set
        assert opts['convertsubtitles'] == 'srt'
        # 4. time_range download_ranges set
        assert 'download_ranges' in opts

def test_download_failure(tmp_path):
    """Test that VideoDownloadError is raised if a DownloadError occurs."""
    output_dir = str(tmp_path / "custom_downloads_fail")
    downloader = VideoDownloader(output_dir=output_dir)
    test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.side_effect = yt_dlp.utils.DownloadError("Some error message")

        with pytest.raises(VideoDownloadError) as exc_info:
            downloader.download(test_url)
        
        assert "Failed to download video from" in str(exc_info.value)

def test_list_subtitles_success():
    """Test successful retrieval and formatting of available subtitles."""
    test_url = "https://www.youtube.com/watch?v=mocked"
    
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        
        # Structure matching yt-dlp response
        mock_info = {
            "subtitles": {
                "en": [{"ext": "vtt", "name": "English"}],
                "zh-TW": [{"ext": "srv3", "name": "Chinese (Traditional)"}]
            },
            "automatic_captions": {
                "en": [{"ext": "json3", "name": "English (auto-generated)"}]
            }
        }
        mock_ydl_instance.extract_info.return_value = mock_info
        
        res = VideoDownloader.list_subtitles(test_url)
        
        assert res == {
            "manual": {
                "en": "English",
                "zh-TW": "Chinese (Traditional)"
            },
            "auto": {
                "en": "English (auto-generated)"
            }
        }
        mock_ydl_instance.extract_info.assert_called_once_with(test_url, download=False)

def test_list_subtitles_failure():
    """Test that VideoDownloadError is raised if list_subtitles fails."""
    test_url = "https://www.youtube.com/watch?v=mocked"
    
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.side_effect = Exception("Some extraction error")
        
        with pytest.raises(VideoDownloadError) as exc_info:
            VideoDownloader.list_subtitles(test_url)
            
        assert "Failed to retrieve subtitles list" in str(exc_info.value)

