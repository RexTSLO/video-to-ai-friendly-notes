import os
from src.downloader import VideoDownloader

def test_download_video(tmp_path):
    downloader = VideoDownloader(output_dir=str(tmp_path))
    # A tiny, extremely reliable and short public video for testing
    test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
    output_path = downloader.download(test_url)
    assert os.path.exists(output_path)
    assert output_path.endswith(".mp4")
