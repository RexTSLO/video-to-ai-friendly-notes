import os
from unittest.mock import patch, MagicMock
import pytest

from src.transcriber import SubtitleTranscriber

def test_transcribe_success_zh_default_prompt(tmp_path):
    """Test successful transcription for Chinese using the default prompt."""
    # Setup dummy media file path to satisfy existence check
    dummy_media = str(tmp_path / "dummy_audio.mp4")
    with open(dummy_media, "w") as f:
        f.write("dummy media data")

    with patch("src.transcriber.WhisperModel") as mock_whisper_class:
        # Mock WhisperModel instance
        mock_model_instance = MagicMock()
        mock_whisper_class.return_value = mock_model_instance

        # Mock segment objects returned by the model
        mock_seg1 = MagicMock()
        mock_seg1.start = 0.0
        mock_seg1.end = 2.5
        mock_seg1.text = "哈囉世界"

        mock_seg2 = MagicMock()
        mock_seg2.start = 3.0
        mock_seg2.end = 5.5
        mock_seg2.text = "歡迎來到AI課堂"

        # Mock transcribe return value: (generator of segments, info)
        mock_model_instance.transcribe.return_value = (
            [mock_seg1, mock_seg2],
            MagicMock()
        )

        # Act
        transcriber = SubtitleTranscriber(model_size="tiny", device="cpu")
        segments = transcriber.transcribe(dummy_media, lang="zh")

        # Assert
        # 1. Result should be list of dicts with precise keys
        assert len(segments) == 2
        assert segments[0] == {"start": 0.0, "end": 2.5, "text": "哈囉世界"}
        assert segments[1] == {"start": 3.0, "end": 5.5, "text": "歡迎來到AI課堂"}

        # 2. WhisperModel was initialized correctly
        mock_whisper_class.assert_called_once_with("tiny", device="cpu", compute_type="float32")

        # 3. model.transcribe was called with the correct Chinese prompt
        expected_prompt = "這是一個繁體中文的字幕。請用繁體中文輸出接下來的內容。"
        mock_model_instance.transcribe.assert_called_once_with(
            dummy_media,
            language="zh",
            initial_prompt=expected_prompt
        )


def test_transcribe_success_custom_prompt(tmp_path):
    """Test successful transcription with a custom prompt."""
    dummy_media = str(tmp_path / "dummy_audio.mp4")
    with open(dummy_media, "w") as f:
        f.write("dummy media data")

    with patch("src.transcriber.WhisperModel") as mock_whisper_class:
        mock_model_instance = MagicMock()
        mock_whisper_class.return_value = mock_model_instance

        mock_model_instance.transcribe.return_value = (
            [],
            MagicMock()
        )

        transcriber = SubtitleTranscriber(model_size="tiny", device="cpu")
        transcriber.transcribe(dummy_media, lang="en", initial_prompt="Some English prompt")

        # model.transcribe was called with the custom prompt
        mock_model_instance.transcribe.assert_called_once_with(
            dummy_media,
            language="en",
            initial_prompt="Some English prompt"
        )


def test_transcribe_file_not_found():
    """Test that FileNotFoundError is raised when the media path does not exist."""
    transcriber = SubtitleTranscriber(model_size="tiny", device="cpu")
    with pytest.raises(FileNotFoundError):
        transcriber.transcribe("non_existent_file.mp4")


def test_write_srt(tmp_path):
    """Test generating standard SRT file from segments."""
    segments = [
        {"start": 0.0, "end": 2.5, "text": "Hello World"},
        {"start": 3.125, "end": 5.002, "text": "Welcome to Python class"}
    ]
    output_srt = str(tmp_path / "subtitles.srt")

    transcriber = SubtitleTranscriber(model_size="tiny", device="cpu")
    # write_srt is offline and shouldn't trigger model transcription
    transcriber.write_srt(segments, output_srt)

    assert os.path.exists(output_srt)
    with open(output_srt, "r", encoding="utf-8") as f:
        content = f.read()

    expected_content = (
        "1\n"
        "00:00:00,000 --> 00:00:02,500\n"
        "Hello World\n\n"
        "2\n"
        "00:00:03,125 --> 00:00:05,002\n"
        "Welcome to Python class\n\n"
    )
    assert content == expected_content


def test_parse_srt(tmp_path):
    """Test parsing a valid standard SRT file into segments list of dicts."""
    srt_content = (
        "1\n"
        "00:00:00,000 --> 00:00:02,500\n"
        "Hello World\n\n"
        "2\n"
        "00:00:03,125 --> 00:00:05,002\n"
        "Welcome to Python class\n\n"
    )
    srt_file = tmp_path / "test.srt"
    srt_file.write_text(srt_content, encoding="utf-8")

    segments = SubtitleTranscriber.parse_srt(str(srt_file))

    assert len(segments) == 2
    assert segments[0] == {"start": 0.0, "end": 2.5, "text": "Hello World"}
    assert segments[1] == {"start": 3.125, "end": 5.002, "text": "Welcome to Python class"}


def test_parse_srt_invalid(tmp_path):
    """Test parsing an invalid or non-existent SRT file."""
    # Test non-existent file
    with pytest.raises(FileNotFoundError):
        SubtitleTranscriber.parse_srt(str(tmp_path / "non_existent.srt"))

    # Test empty file
    empty_file = tmp_path / "empty.srt"
    empty_file.write_text("", encoding="utf-8")
    assert SubtitleTranscriber.parse_srt(str(empty_file)) == []


def test_parse_vtt(tmp_path):
    """Test parsing a valid VTT file with standard headers, lack of block numbers, and tags."""
    vtt_content = (
        "WEBVTT\n\n"
        "00:00:00.000 --> 00:00:02.500\n"
        "Hello <c.traditional>World</c>\n\n"
        "00:00:03.125 --> 00:00:05.002\n"
        "<b>Welcome to VTT parsing</b>\n\n"
    )
    vtt_file = tmp_path / "test.vtt"
    vtt_file.write_text(vtt_content, encoding="utf-8")

    segments = SubtitleTranscriber.parse_srt(str(vtt_file))

    assert len(segments) == 2
    assert segments[0] == {"start": 0.0, "end": 2.5, "text": "Hello World"}
    assert segments[1] == {"start": 3.125, "end": 5.002, "text": "Welcome to VTT parsing"}

