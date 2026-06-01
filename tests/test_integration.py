import os
import sys
import subprocess
import shutil
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
    """Test the complete orchestration pipeline with mocked subsystems and isolated directory dispatcher."""
    # Custom input directory target
    output_pdf = str(tmp_path / "final_output.pdf")
    
    # Expected isolated paths from Smart Directory Dispatcher
    expected_pdf = os.path.abspath(str(tmp_path / "pdf" / "final_output.pdf"))
    expected_srt = os.path.abspath(str(tmp_path / "subtitles" / "final_output.srt"))
    expected_slides_dir = os.path.abspath(str(tmp_path / "slides" / "final_output"))
    
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
         patch("src.main.shutil.move") as mock_move, \
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
        mock_downloader_instance.download.return_value = (downloaded_video, None)

        # Setup side effect for mock_move to securely simulate video transfer
        def mock_move_side_effect(src, dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "w") as f:
                f.write("moved dummy video")
        mock_move.side_effect = mock_move_side_effect

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
        # 1. VideoDownloader called in mock temp sandbox, then safely moved to inputs/
        mock_downloader_class.assert_called_once_with(
            output_dir=mock_temp_dir,
            max_res=720,
            subs_from_yt=None,
            time_range=None
        )
        mock_downloader_instance.download.assert_called_once_with("https://www.youtube.com/watch?v=mocked")
        expected_final_video = os.path.abspath(os.path.join("inputs", "lecture.mp4"))
        mock_move.assert_called_once_with(downloaded_video, expected_final_video)

        # 2. SubtitleTranscriber called and transcribe executed
        mock_transcriber_class.assert_called_once_with(model_size="tiny", device="cpu")
        
        # 3. Intermediate srt was written inside the isolated subtitles/ namespace
        mock_transcriber_instance.write_srt.assert_called_once_with(dummy_subs, expected_srt)

        # 4. SlideDetector called and detect_slides executed with custom threshold
        mock_detector_class.assert_called_once_with(threshold=12.0)
        mock_detector_instance.detect_slides.assert_called_once_with(expected_final_video, expected_slides_dir)

        # 5. PDFGenerator called and generate executed in the isolated pdf/ namespace
        mock_generator_class.assert_called_once()
        mock_generator_instance.generate.assert_called_once_with(dummy_slides, dummy_subs, expected_pdf)

        # 6. Finally block sweeps sandbox directory cleanly
        mock_rmtree.assert_called_once_with(mock_temp_dir)

        # Cleanup mock final video
        if os.path.exists(expected_final_video):
            os.remove(expected_final_video)


def test_orchestration_default_output_mocked(tmp_path):
    """Test orchestration pipeline using default output directory creation and isolated sub-directories."""
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
        # Verify makedirs was triggered for outputs/pdf/, outputs/subtitles/ and outputs/slides/ namespaces
        expected_pdf_dir = os.path.abspath("outputs/pdf")
        expected_srt_dir = os.path.abspath("outputs/subtitles")
        expected_slides_dir = os.path.abspath("outputs/slides/lecture_notes")
        
        mock_makedirs.assert_any_call(expected_pdf_dir, exist_ok=True)
        mock_makedirs.assert_any_call(expected_srt_dir, exist_ok=True)
        mock_makedirs.assert_any_call(expected_slides_dir, exist_ok=True)
        
        expected_pdf = os.path.abspath("outputs/pdf/lecture_notes.pdf")
        expected_srt = os.path.abspath("outputs/subtitles/lecture_notes.srt")
        mock_transcriber_instance.write_srt.assert_called_once_with([], expected_srt)
        mock_generator_instance.generate.assert_called_once_with([], [], expected_pdf)


def test_subs_from_yt_success(tmp_path):
    """Test that --subs-from-yt successfully bypasses Whisper transcribe and parses download subtitles instead."""
    output_pdf = str(tmp_path / "final_output.pdf")
    expected_srt = os.path.abspath(str(tmp_path / "subtitles" / "final_output.srt"))
    
    test_args = [
        "src.main",
        "--url", "https://www.youtube.com/watch?v=mocked",
        "--output", output_pdf,
        "--subs-from-yt", "zh-TW"
    ]

    with patch("sys.argv", test_args), \
         patch("src.main.tempfile.mkdtemp") as mock_mkdtemp, \
         patch("src.main.shutil.rmtree") as mock_rmtree, \
         patch("src.main.shutil.move") as mock_move, \
         patch("src.main.VideoDownloader") as mock_downloader_class, \
         patch("src.main.SubtitleTranscriber") as mock_transcriber_class, \
         patch("src.main.SlideDetector") as mock_detector_class, \
         patch("src.main.PDFGenerator") as mock_generator_class:

        mock_temp_dir = str(tmp_path / "mock_workspace")
        mock_mkdtemp.return_value = mock_temp_dir

        mock_downloader_instance = MagicMock()
        mock_downloader_class.return_value = mock_downloader_instance
        downloaded_video = os.path.join(mock_temp_dir, "lecture.mp4")
        downloaded_srt = os.path.join(mock_temp_dir, "lecture.zh-TW.srt")
        mock_downloader_instance.download.return_value = (downloaded_video, downloaded_srt)

        # Create dummy downloaded files in sandbox
        os.makedirs(mock_temp_dir, exist_ok=True)
        with open(downloaded_video, "w") as f:
            f.write("dummy video data")
        with open(downloaded_srt, "w") as f:
            f.write("dummy srt data")

        # Mock transcriber parse_srt
        mock_transcriber_instance = MagicMock()
        mock_transcriber_class.return_value = mock_transcriber_instance
        dummy_subs = [{"start": 0.0, "end": 2.0, "text": "parsed text"}]
        mock_transcriber_class.parse_srt.return_value = dummy_subs

        # Mock detector and generator
        mock_detector_instance = MagicMock()
        mock_detector_class.return_value = mock_detector_instance
        mock_detector_instance.detect_slides.return_value = []
        mock_generator_instance = MagicMock()
        mock_generator_class.return_value = mock_generator_instance

        # Setup side effect for mock_move to securely simulate video transfer
        expected_final_video = os.path.abspath(os.path.join("inputs", "lecture.mp4"))
        def mock_move_side_effect(src, dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "w") as f:
                f.write("moved dummy video")
        mock_move.side_effect = mock_move_side_effect

        # Act
        main()

        # Assertions
        # 1. Downloader called with correct parameter
        mock_downloader_class.assert_called_once_with(
            output_dir=mock_temp_dir,
            max_res=720,
            subs_from_yt="zh-TW",
            time_range=None
        )
        
        # 2. Whisper transcription is BYPASSED
        mock_transcriber_instance.transcribe.assert_not_called()
        
        # 3. parse_srt is called instead on downloaded subtitle
        mock_transcriber_class.parse_srt.assert_called_once_with(downloaded_srt)
        
        # 4. parsed subtitles are written to srt_out_path
        mock_transcriber_instance.write_srt.assert_called_once_with(dummy_subs, expected_srt)

        # Cleanup mock final video
        if os.path.exists(expected_final_video):
            os.remove(expected_final_video)


def test_subs_from_yt_failure(tmp_path):
    """Test that --subs-from-yt fails immediately if no subtitle file is returned by VideoDownloader."""
    output_pdf = str(tmp_path / "final_output.pdf")
    
    test_args = [
        "src.main",
        "--url", "https://www.youtube.com/watch?v=mocked",
        "--output", output_pdf,
        "--subs-from-yt", "zh-TW"
    ]

    with patch("sys.argv", test_args), \
         patch("src.main.tempfile.mkdtemp") as mock_mkdtemp, \
         patch("src.main.shutil.rmtree") as mock_rmtree, \
         patch("src.main.shutil.move") as mock_move, \
         patch("src.main.VideoDownloader") as mock_downloader_class, \
         patch("src.main.SubtitleTranscriber") as mock_transcriber_class:

        mock_temp_dir = str(tmp_path / "mock_workspace")
        mock_mkdtemp.return_value = mock_temp_dir

        mock_downloader_instance = MagicMock()
        mock_downloader_class.return_value = mock_downloader_instance
        downloaded_video = os.path.join(mock_temp_dir, "lecture.mp4")
        # Subtitle file is None (not found)
        mock_downloader_instance.download.return_value = (downloaded_video, None)

        os.makedirs(mock_temp_dir, exist_ok=True)
        with open(downloaded_video, "w") as f:
            f.write("dummy video data")

        # Setup side effect for mock_move to securely simulate video transfer
        expected_final_video = os.path.abspath(os.path.join("inputs", "lecture.mp4"))
        def mock_move_side_effect(src, dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "w") as f:
                f.write("moved dummy video")
        mock_move.side_effect = mock_move_side_effect

        mock_transcriber_instance = MagicMock()
        mock_transcriber_class.return_value = mock_transcriber_instance

        # Act & Assert
        # If no subtitle, it must raise ValueError or another fatal error to terminate
        with pytest.raises((ValueError, SystemExit, RuntimeError)):
            main()

        # Cleanup mock final video
        if os.path.exists(expected_final_video):
            os.remove(expected_final_video)


def test_max_res_and_time_range_passed(tmp_path):
    """Test that max_res and time_range parameters are correctly passed to VideoDownloader."""
    output_pdf = str(tmp_path / "final_output.pdf")
    
    test_args = [
        "src.main",
        "--url", "https://www.youtube.com/watch?v=mocked",
        "--output", output_pdf,
        "--max-res", "480",
        "--time-range", "00:10:00-00:20:30"
    ]

    with patch("sys.argv", test_args), \
         patch("src.main.tempfile.mkdtemp") as mock_mkdtemp, \
         patch("src.main.shutil.rmtree") as mock_rmtree, \
         patch("src.main.shutil.move") as mock_move, \
         patch("src.main.VideoDownloader") as mock_downloader_class, \
         patch("src.main.SubtitleTranscriber") as mock_transcriber_class, \
         patch("src.main.SlideDetector") as mock_detector_class, \
         patch("src.main.PDFGenerator") as mock_generator_class:

        mock_temp_dir = str(tmp_path / "mock_workspace")
        mock_mkdtemp.return_value = mock_temp_dir

        mock_downloader_instance = MagicMock()
        mock_downloader_class.return_value = mock_downloader_instance
        downloaded_video = os.path.join(mock_temp_dir, "lecture.mp4")
        mock_downloader_instance.download.return_value = (downloaded_video, None)

        os.makedirs(mock_temp_dir, exist_ok=True)
        with open(downloaded_video, "w") as f:
            f.write("dummy video data")

        # Setup side effect for mock_move to securely simulate video transfer
        expected_final_video = os.path.abspath(os.path.join("inputs", "lecture.mp4"))
        def mock_move_side_effect(src, dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "w") as f:
                f.write("moved dummy video")
        mock_move.side_effect = mock_move_side_effect

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
        # Downloader receives 480 for max_res and '00:10:00-00:20:30' for time_range
        mock_downloader_class.assert_called_once_with(
            output_dir=mock_temp_dir,
            max_res=480,
            subs_from_yt=None,
            time_range="00:10:00-00:20:30"
        )

        # Cleanup mock final video
        if os.path.exists(expected_final_video):
            os.remove(expected_final_video)


def test_local_srt_success(tmp_path):
    """Test that specifying --srt correctly reads the local srt file and bypasses Whisper/YT downloads."""
    output_pdf = str(tmp_path / "final_output.pdf")
    expected_srt = os.path.abspath(str(tmp_path / "subtitles" / "final_output.srt"))
    local_srt_path = str(tmp_path / "my_local.srt")
    
    # Create the local srt file
    with open(local_srt_path, "w") as f:
        f.write("1\n00:00:00,000 --> 00:00:02,000\nLocal srt content\n\n")

    test_args = [
        "src.main",
        "--url", "https://www.youtube.com/watch?v=mocked",
        "--output", output_pdf,
        "--srt", local_srt_path
    ]

    with patch("sys.argv", test_args), \
         patch("src.main.tempfile.mkdtemp") as mock_mkdtemp, \
         patch("src.main.shutil.rmtree") as mock_rmtree, \
         patch("src.main.shutil.move") as mock_move, \
         patch("src.main.VideoDownloader") as mock_downloader_class, \
         patch("src.main.SubtitleTranscriber") as mock_transcriber_class, \
         patch("src.main.SlideDetector") as mock_detector_class, \
         patch("src.main.PDFGenerator") as mock_generator_class:

        mock_temp_dir = str(tmp_path / "mock_workspace")
        mock_mkdtemp.return_value = mock_temp_dir

        mock_downloader_instance = MagicMock()
        mock_downloader_class.return_value = mock_downloader_instance
        downloaded_video = os.path.join(mock_temp_dir, "lecture.mp4")
        mock_downloader_instance.download.return_value = (downloaded_video, None)

        os.makedirs(mock_temp_dir, exist_ok=True)
        with open(downloaded_video, "w") as f:
            f.write("dummy video data")

        # Mock transcriber parse_srt
        mock_transcriber_instance = MagicMock()
        mock_transcriber_class.return_value = mock_transcriber_instance
        dummy_subs = [{"start": 0.0, "end": 2.0, "text": "local parsed text"}]
        mock_transcriber_class.parse_srt.return_value = dummy_subs

        # Mock detector and generator
        mock_detector_instance = MagicMock()
        mock_detector_class.return_value = mock_detector_instance
        mock_detector_instance.detect_slides.return_value = []
        mock_generator_instance = MagicMock()
        mock_generator_class.return_value = mock_generator_instance

        # Setup side effect for mock_move to securely simulate video transfer
        expected_final_video = os.path.abspath(os.path.join("inputs", "lecture.mp4"))
        def mock_move_side_effect(src, dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "w") as f:
                f.write("moved dummy video")
        mock_move.side_effect = mock_move_side_effect

        # Act
        main()

        # Assertions
        # 1. Downloader called without subtitle parameter
        mock_downloader_class.assert_called_once_with(
            output_dir=mock_temp_dir,
            max_res=720,
            subs_from_yt=None,
            time_range=None
        )
        
        # 2. Whisper transcription is BYPASSED
        mock_transcriber_instance.transcribe.assert_not_called()
        
        # 3. parse_srt is called on the local srt file
        mock_transcriber_class.parse_srt.assert_called_once_with(local_srt_path)
        
        # 4. parsed subtitles are written to srt_out_path
        mock_transcriber_instance.write_srt.assert_called_once_with(dummy_subs, expected_srt)

        # Cleanup mock final video
        if os.path.exists(expected_final_video):
            os.remove(expected_final_video)


def test_local_srt_failure(tmp_path):
    """Test that specifying a non-existent --srt file fails immediately."""
    output_pdf = str(tmp_path / "final_output.pdf")
    non_existent_srt = str(tmp_path / "does_not_exist.srt")
    
    test_args = [
        "src.main",
        "--url", "https://www.youtube.com/watch?v=mocked",
        "--output", output_pdf,
        "--srt", non_existent_srt
    ]

    with patch("sys.argv", test_args), \
         patch("src.main.tempfile.mkdtemp") as mock_mkdtemp, \
         patch("src.main.shutil.rmtree") as mock_rmtree, \
         patch("src.main.VideoDownloader") as mock_downloader_class, \
         patch("src.main.SubtitleTranscriber") as mock_transcriber_class:

        mock_temp_dir = str(tmp_path / "mock_workspace")
        mock_mkdtemp.return_value = mock_temp_dir

        # Act & Assert
        # If no subtitle, it must raise ValueError/FileNotFoundError to terminate
        with pytest.raises((ValueError, FileNotFoundError, SystemExit, RuntimeError)):
            main()



