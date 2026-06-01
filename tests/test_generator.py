import os
from unittest.mock import patch, MagicMock
import pytest

from src.generator import PDFGenerator

def test_bind_subtitles_to_keyframes():
    """Test pairing subtitles to slides chronologically based on start time mapping."""
    generator = PDFGenerator(font_dir="dummy_fonts")

    keyframes = [
        {"timestamp": 0.0, "image_path": "slide_0.jpg"},
        {"timestamp": 10.0, "image_path": "slide_10.jpg"}
    ]
    subtitles = [
        {"start": 1.0, "end": 4.0, "text": "Hello, welcome to class."},
        {"start": 9.5, "end": 10.5, "text": "Transitioning now."},
        {"start": 12.0, "end": 14.5, "text": "Here is the next slide."}
    ]

    bound = generator._bind_subtitles_to_keyframes(keyframes, subtitles)

    assert len(bound) == 2
    # Slide 1 (0.0s to 10.0s) should have subtitle 1 and 2
    assert len(bound[0]["subtitles"]) == 2
    assert bound[0]["subtitles"][0]["text"] == "Hello, welcome to class."
    assert bound[0]["subtitles"][1]["text"] == "Transitioning now."

    # Slide 2 (10.0s onwards) should have subtitle 3
    assert len(bound[1]["subtitles"]) == 1
    assert bound[1]["subtitles"][0]["text"] == "Here is the next slide."


def test_pdf_generation_mocked(tmp_path):
    """Test generating PDF with complete mocking of urllib download and FPDF generation."""
    font_dir = str(tmp_path / "fonts")
    generator = PDFGenerator(font_dir=font_dir)

    keyframes = [
        {"timestamp": 0.0, "image_path": str(tmp_path / "slide_0.jpg")},
        {"timestamp": 5.0, "image_path": str(tmp_path / "slide_5.jpg")}
    ]
    subtitles = [
        {"start": 1.0, "end": 3.0, "text": "Slide 0 subtitle"}
    ]

    # Create dummy images to satisfy existence check
    for kf in keyframes:
        with open(kf["image_path"], "w") as f:
            f.write("dummy image")

    output_pdf = str(tmp_path / "notes.pdf")

    with patch("urllib.request.urlretrieve") as mock_download, \
         patch("src.generator.FPDF") as mock_fpdf_class:

        def mock_download_side_effect(url, filepath):
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w") as f:
                f.write("dummy font")
        mock_download.side_effect = mock_download_side_effect

        mock_fpdf_instance = MagicMock()
        mock_fpdf_class.return_value = mock_fpdf_instance

        # Act
        generator.generate(keyframes, subtitles, output_pdf)

        # Assert
        # 1. Download font is triggered (or check directory setup)
        # Note: since the file NotoSansCJKtc-Regular.ttf doesn't exist,
        # ensure_font_exists was called and triggered urlretrieve.
        mock_download.assert_called_once()

        # 2. FPDF object is initialized and page actions are taken
        mock_fpdf_class.assert_called_once()
        assert mock_fpdf_instance.add_page.call_count == 2
        
        # 3. Font and images are registered
        mock_fpdf_instance.add_font.assert_called_once_with(
            "NotoSans", "", generator.font_path, uni=True
        )
        assert mock_fpdf_instance.image.call_count == 2
        
        # 4. output was persisted successfully
        mock_fpdf_instance.output.assert_called_once_with(output_pdf)
