import os
import sys
import subprocess
from unittest.mock import patch, MagicMock
import pytest

from src.main import main

def test_cli_help_flag():
    """Test that running the entrypoint command with help flag returns success and usage instructions."""
    result = subprocess.run(
        [sys.executable, "-m", "src.main", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "video-to-ai-friendly-notes" in result.stdout or "usage:" in result.stdout


def test_orchestration_pipeline_mocked(tmp_path):
    """Test the complete orchestration pipeline with mocked subsystems."""
    output_pdf = str(tmp_path / "final_output.pdf")
    expected_srt = str(tmp_path / "final_output.srt")
    
    # Custom CLI arguments
    test_args = [
        "src.main",
        "--url", "https://www.youtube.com/watch?v=mocked",
        "--output", output_pdf,
        "--model", "tiny",
        "--lang", "zh",
        "--threshold", "12.0",
        "--device", "cpu"
    ]

    with patch("sys.argv", test_args), \
         patch("src.main.tempfile.mkdtemp") as mock_mkdtemp, \
         patch("src.main.shutil.rmtree") as mock_rmtree, \
         patch("src.main.VideoDownloader") as mock_downloader_class, \
         patch("src.main.SubtitleTranscriber") as mock_transcriber_class, \
         patch("src.main.SlideDetector") as mock_detector_class, \
         patch("src.main.PDFGenerator") as mock_generator_class:

        # Mock workspace directory
        mock_temp_dir = str(tmp_path / "mock_workspace")
        mock_mkdtemp.return_value = mock_temp_dir

        # Mock Downloader
        mock_downloader_instance = MagicMock()
        mock_downloader_class.return_value = mock_downloader_instance
        downloaded_video = os.path.join(mock_temp_dir, "lecture.mp4")
        mock_downloader_instance.download.return_value = downloaded_video

        # Create dummy file to satisfy os.path.exists checks for downloaded video
        os.makedirs(mock_temp_dir, exist_ok=True)
        with open(downloaded_video, "w") as f:
            f.write("dummy video data")

        # Mock Transcriber
        mock_transcriber_instance = MagicMock()
        mock_transcriber_class.return_value = mock_transcriber_instance
        dummy_subs = [{"start": 0.0, "end": 2.0, "text": "transcription text"}]
        mock_transcriber_instance.transcribe.return_value = dummy_subs

        # Mock Detector
        mock_detector_instance = MagicMock()
        mock_detector_class.return_value = mock_detector_instance
        dummy_slides = [{"timestamp": 0.0, "image_path": "slide.jpg"}]
        mock_detector_instance.detect_slides.return_value = dummy_slides

        # Mock Generator
        mock_generator_instance = MagicMock()
        mock_generator_class.return_value = mock_generator_instance

        # Act
        main()

        # Assertions
        # 1. VideoDownloader called with temp dir and download runs
        mock_downloader_class.assert_called_once_with(output_dir=mock_temp_dir)
        mock_downloader_instance.download.assert_called_once_with("https://www.youtube.com/watch?v=mocked")

        # 2. SubtitleTranscriber called and transcribe executed
        mock_transcriber_class.assert_called_once_with(model_size="tiny", device="cpu")
        mock_transcriber_instance.transcribe.assert_called_once_with(downloaded_video, lang="zh")
        
        # 3. Intermediate srt was written next to the output pdf path
        mock_transcriber_instance.write_srt.assert_called_once_with(dummy_subs, expected_srt)

        # 4. SlideDetector called and detect_slides executed with custom threshold
        mock_detector_class.assert_called_once_with(threshold=12.0)
        expected_frames_dir = os.path.join(mock_temp_dir, "frames")
        mock_detector_instance.detect_slides.assert_called_once_with(downloaded_video, expected_frames_dir)

        # 5. PDFGenerator called and generate executed
        mock_generator_class.assert_called_once()
        mock_generator_instance.generate.assert_called_once_with(dummy_slides, dummy_subs, output_pdf)

        # 6. Finally block sweeps directories cleanly
        mock_rmtree.assert_called_once_with(mock_temp_dir)


def test_orchestration_default_output_mocked(tmp_path):
    """Test orchestration pipeline using default output directory creation."""
    test_args = [
        "src.main",
        "--input", "dummy_video_path.mp4"
    ]
    
    with patch("sys.argv", test_args), \
         patch("os.path.exists") as mock_exists, \
         patch("os.makedirs") as mock_makedirs, \
         patch("src.main.tempfile.mkdtemp") as mock_mkdtemp, \
         patch("src.main.shutil.rmtree") as mock_rmtree, \
         patch("src.main.SubtitleTranscriber") as mock_transcriber_class, \
         patch("src.main.SlideDetector") as mock_detector_class, \
         patch("src.main.PDFGenerator") as mock_generator_class:

        mock_exists.side_effect = lambda path: True
        mock_mkdtemp.return_value = "dummy_temp"

        mock_transcriber_instance = MagicMock()
        mock_transcriber_class.return_value = mock_transcriber_instance
        mock_transcriber_instance.transcribe.return_value = []

        mock_detector_instance = MagicMock()
        mock_detector_class.return_value = mock_detector_instance
        mock_detector_instance.detect_slides.return_value = []

        mock_generator_instance = MagicMock()
        mock_generator_class.return_value = mock_generator_instance

        # Act
        main()

        # Assert
        expected_output_dir = os.path.dirname(os.path.abspath("outputs/lecture_notes.pdf"))
        mock_makedirs.assert_any_call(expected_output_dir, exist_ok=True)
        
        expected_pdf = "outputs/lecture_notes.pdf"
        expected_srt = "outputs/lecture_notes.srt"
        mock_transcriber_instance.write_srt.assert_called_once_with([], expected_srt)
        mock_generator_instance.generate.assert_called_once_with([], [], expected_pdf)
