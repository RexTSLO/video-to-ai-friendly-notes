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
            'remote_components': {'ejs:github'},
            'js_runtimes': {'deno': {}, 'node': {}},
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


def test_download_time_ranges_formats(tmp_path):
    """Test valid time range formats of length 2 and 1."""
    output_dir = str(tmp_path / "time_ranges_formats")
    test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
    os.makedirs(output_dir, exist_ok=True)

    # 1. format MM:SS
    downloader = VideoDownloader(output_dir=output_dir, time_range="05:30-10:15")
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        
        mock_info = {"title": "Test Video", "ext": "mp4"}
        mock_ydl_instance.extract_info.return_value = mock_info
        expected_filename = os.path.join(output_dir, "Test Video.mp4")
        mock_ydl_instance.prepare_filename.return_value = expected_filename
        with open(expected_filename, "w") as f:
            f.write("dummy")

        downloader.download(test_url)
        called_args, _ = mock_ydl_class.call_args
        opts = called_args[0]
        assert 'download_ranges' in opts

    # 2. format SS
    downloader = VideoDownloader(output_dir=output_dir, time_range="30-90")
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        
        mock_info = {"title": "Test Video", "ext": "mp4"}
        mock_ydl_instance.extract_info.return_value = mock_info
        expected_filename = os.path.join(output_dir, "Test Video.mp4")
        mock_ydl_instance.prepare_filename.return_value = expected_filename
        with open(expected_filename, "w") as f:
            f.write("dummy")

        downloader.download(test_url)
        called_args, _ = mock_ydl_class.call_args
        opts = called_args[0]
        assert 'download_ranges' in opts


def test_download_invalid_time_range_format(tmp_path):
    """Test that VideoDownloadError is raised if time range format is invalid."""
    output_dir = str(tmp_path / "invalid_time_range")
    downloader = VideoDownloader(output_dir=output_dir, time_range="invalid_range")
    test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"

    with pytest.raises(VideoDownloadError) as exc_info:
        downloader.download(test_url)
    assert "Invalid time range format" in str(exc_info.value)


def test_download_subtitle_fallback_srt(tmp_path):
    """Test subtitle path fallback when expected exact srt name is not found but another matching srt is."""
    output_dir = str(tmp_path / "fallback_srt")
    downloader = VideoDownloader(output_dir=output_dir, subs_from_yt="zh-TW")
    test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        
        mock_info = {"title": "Test Video", "ext": "mp4"}
        mock_ydl_instance.extract_info.return_value = mock_info
        
        expected_video_filename = os.path.join(output_dir, "Test Video.mp4")
        fallback_srt_filename = os.path.join(output_dir, "Test Video.some_random_suffix.srt")
        mock_ydl_instance.prepare_filename.return_value = expected_video_filename

        os.makedirs(output_dir, exist_ok=True)
        with open(expected_video_filename, "w") as f:
            f.write("dummy video")
        with open(fallback_srt_filename, "w") as f:
            f.write("dummy fallback srt")

        video_path, subtitle_path = downloader.download(test_url)

        assert subtitle_path == os.path.abspath(fallback_srt_filename)


def test_download_subtitle_vtt_conversion_success(tmp_path):
    """Test subtitle path conversion from VTT to SRT when FFmpeg succeeds."""
    output_dir = str(tmp_path / "vtt_conv")
    downloader = VideoDownloader(output_dir=output_dir, subs_from_yt="zh-TW")
    test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class, \
         patch("subprocess.run") as mock_run:
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        
        mock_info = {"title": "Test Video", "ext": "mp4"}
        mock_ydl_instance.extract_info.return_value = mock_info
        
        expected_video_filename = os.path.join(output_dir, "Test Video.mp4")
        expected_vtt_filename = os.path.join(output_dir, "Test Video.zh-TW.vtt")
        expected_srt_filename = os.path.join(output_dir, "Test Video.zh-TW.srt")
        mock_ydl_instance.prepare_filename.return_value = expected_video_filename

        os.makedirs(output_dir, exist_ok=True)
        with open(expected_video_filename, "w") as f:
            f.write("dummy video")
        with open(expected_vtt_filename, "w") as f:
            f.write("dummy vtt")

        def mock_subprocess_side_effect(*args, **kwargs):
            with open(expected_srt_filename, "w") as f:
                f.write("converted srt")
            return MagicMock(returncode=0)
        
        mock_run.side_effect = mock_subprocess_side_effect

        video_path, subtitle_path = downloader.download(test_url)

        assert subtitle_path == os.path.abspath(expected_srt_filename)
        assert os.path.exists(expected_srt_filename)
        mock_run.assert_called_once()


def test_download_subtitle_fallback_vtt_conversion_success(tmp_path):
    """Test subtitle path conversion from fallback VTT when exact name VTT is not found."""
    output_dir = str(tmp_path / "fallback_vtt_conv")
    downloader = VideoDownloader(output_dir=output_dir, subs_from_yt="zh-TW")
    test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class, \
         patch("subprocess.run") as mock_run:
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        
        mock_info = {"title": "Test Video", "ext": "mp4"}
        mock_ydl_instance.extract_info.return_value = mock_info
        
        expected_video_filename = os.path.join(output_dir, "Test Video.mp4")
        fallback_vtt_filename = os.path.join(output_dir, "Test Video.custom_suffix.vtt")
        expected_srt_filename = os.path.join(output_dir, "Test Video.custom_suffix.srt")
        mock_ydl_instance.prepare_filename.return_value = expected_video_filename

        os.makedirs(output_dir, exist_ok=True)
        with open(expected_video_filename, "w") as f:
            f.write("dummy video")
        with open(fallback_vtt_filename, "w") as f:
            f.write("dummy vtt")

        def mock_subprocess_side_effect(*args, **kwargs):
            with open(expected_srt_filename, "w") as f:
                f.write("converted srt")
            return MagicMock(returncode=0)
        
        mock_run.side_effect = mock_subprocess_side_effect

        video_path, subtitle_path = downloader.download(test_url)

        assert subtitle_path == os.path.abspath(expected_srt_filename)
        assert os.path.exists(expected_srt_filename)
        mock_run.assert_called_once()


def test_download_subtitle_vtt_conversion_failure(tmp_path):
    """Test subtitle path conversion failure from VTT to SRT when FFmpeg fails."""
    output_dir = str(tmp_path / "vtt_conv_fail")
    downloader = VideoDownloader(output_dir=output_dir, subs_from_yt="zh-TW")
    test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class, \
         patch("subprocess.run") as mock_run:
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        
        mock_info = {"title": "Test Video", "ext": "mp4"}
        mock_ydl_instance.extract_info.return_value = mock_info
        
        expected_video_filename = os.path.join(output_dir, "Test Video.mp4")
        expected_vtt_filename = os.path.join(output_dir, "Test Video.zh-TW.vtt")
        mock_ydl_instance.prepare_filename.return_value = expected_video_filename

        os.makedirs(output_dir, exist_ok=True)
        with open(expected_video_filename, "w") as f:
            f.write("dummy video")
        with open(expected_vtt_filename, "w") as f:
            f.write("dummy vtt")

        mock_run.side_effect = Exception("FFmpeg command not found or failed")

        video_path, subtitle_path = downloader.download(test_url)

        assert subtitle_path is None


def test_list_subtitles_missing_name():
    """Test subtitle formatting when name is missing or empty in yt-dlp metadata."""
    test_url = "https://www.youtube.com/watch?v=mocked"
    
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        
        mock_info = {
            "subtitles": {
                "en": [{"ext": "vtt"}],
                "zh-TW": []
            },
            "automatic_captions": {
                "fr": [{"ext": "json3", "name": ""}]
            }
        }
        mock_ydl_instance.extract_info.return_value = mock_info
        
        res = VideoDownloader.list_subtitles(test_url)
        
        assert res == {
            "manual": {
                "en": "en",
                "zh-TW": "zh-TW"
            },
            "auto": {
                "fr": "fr"
            }
        }


def test_download_video_with_cookies(tmp_path):
    """Test that cookiefile is passed to ydl_opts during download."""
    output_dir = str(tmp_path / "cookies_download")
    downloader = VideoDownloader(
        output_dir=output_dir,
        cookiefile="dummy_cookies.txt"
    )
    test_url = "https://www.youtube.com/watch?v=mocked"

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

        # Verify ydl_opts contains cookies keys
        called_args, called_kwargs = mock_ydl_class.call_args
        opts = called_args[0]
        assert opts['cookiefile'] == "dummy_cookies.txt"


def test_list_subtitles_with_cookies():
    """Test that cookiefile is passed to ydl_opts during list_subtitles."""
    test_url = "https://www.youtube.com/watch?v=mocked"
    
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {}

        VideoDownloader.list_subtitles(
            test_url,
            cookiefile="custom_cookies.txt"
        )
        
        called_args, called_kwargs = mock_ydl_class.call_args
        opts = called_args[0]
        assert opts['cookiefile'] == "custom_cookies.txt"



