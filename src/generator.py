import os
import urllib.request
from fpdf import FPDF

class PDFGenerator:
    """A PDF generation module that orchestrates layout rendering, CJK Chinese font registration,

    and sequential slide-transcript pairing into a clean PDF document.
    """

    def __init__(self, font_dir: str = "fonts") -> None:
        """Initialize the PDFGenerator with a directory to cache high-quality CJK fonts.

        Args:
            font_dir: Directory where the TrueType Chinese font will be saved.
        """
        self.font_dir = font_dir
        self.font_path = os.path.abspath(os.path.join(self.font_dir, "NotoSansCJKtc-Regular.ttf"))

    def _ensure_font_exists(self) -> bool:
        """Securely fetch CJK traditional Chinese font to display glyphs correctly.

        Returns:
            True if the font exists or was downloaded successfully, False otherwise.
        """
        if not os.path.exists(self.font_path):
            os.makedirs(self.font_dir, exist_ok=True)
            # Reliable source for Noto Sans CJK TC VF (Traditional Chinese variable font)
            url = "https://github.com/notofonts/noto-cjk/raw/main/Sans/Variable/TTF/NotoSansCJKtc-VF.ttf"
            try:
                print(f"[*] Downloading CJK font for Chinese PDF support from {url}...")
                # Download font securely
                urllib.request.urlretrieve(url, self.font_path)
                print("[+] Font downloaded successfully and cached.")
                return True
            except Exception as e:
                print(f"[-] WARNING: Failed to download Chinese font: {str(e)}.")
                print("[-] Fallback to default PDF standard Latin fonts. Chinese characters might not render correctly.")
                return False
        return True

    def _bind_subtitles_to_keyframes(self, keyframes: list[dict], subtitles: list[dict]) -> list[dict]:
        """Pair subtitles onto their chronologically corresponding slide images.

        A subtitle belongs to a slide if its start timestamp falls within [slide_start, next_slide_start).

        Args:
            keyframes: List of slide keyframe descriptors.
            subtitles: List of segment dictionaries.

        Returns:
            A bound list of slide pages containing pairing segments.
        """
        bound = []
        for idx, kf in enumerate(keyframes):
            start_time = float(kf["timestamp"])
            # The next slide's timestamp marks the end of the current slide's active frame
            end_time = float(keyframes[idx + 1]["timestamp"]) if idx + 1 < len(keyframes) else float('inf')

            slide_subs = []
            for sub in subtitles:
                sub_start = float(sub["start"])
                if start_time <= sub_start < end_time:
                    slide_subs.append(sub)

            bound.append({
                "timestamp": start_time,
                "image_path": kf["image_path"],
                "subtitles": slide_subs
            })
        return bound

    def generate(self, keyframes: list[dict], subtitles: list[dict], output_pdf: str, doc_title: str = "AI Lecture Notes") -> None:
        """Compile slides and transcription segments and render the final highly-structured PDF notes.

        Args:
            keyframes: List of slide transition descriptors.
            subtitles: List of transcribed speech segments.
            output_pdf: Destination file path for the final PDF.
            doc_title: Document title headers.
        """
        bound_slides = self._bind_subtitles_to_keyframes(keyframes, subtitles)

        # Initialize FPDF object with Portrait mode and millimeter scaling
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=15)

        # Defensive fallback setup for font registration
        font_available = self._ensure_font_exists()
        if font_available and os.path.exists(self.font_path):
            pdf.add_font("NotoSans", "", self.font_path, uni=True)
            font_family = "NotoSans"
        else:
            font_family = "Helvetica"

        for idx, slide in enumerate(bound_slides, 1):
            pdf.add_page()

            # 1. Slide Image Rendering (with safety dimensions preserving aspect ratio)
            if os.path.exists(slide["image_path"]):
                # Scale width to fit nicely within printable page A4 borders (210 - 15 - 15 = 180)
                # Drawing without explicit X offset allows FPDF2 to safely advance the cursor Y.
                pdf.image(slide["image_path"], w=180)
                pdf.ln(8)

            # 2. Transcribed text content mapping
            pdf.set_font(font_family, "", 10)
            if not slide["subtitles"]:
                pdf.multi_cell(0, 7, "[No vocal lecture speech recorded during this slide duration.]", new_x="LMARGIN", new_y="NEXT")
            else:
                # Concatenate all subtitles into a single continuous block without timestamps or segment wrap newlines
                combined_text = " ".join(sub["text"].strip() for sub in slide["subtitles"])
                pdf.multi_cell(0, 7, combined_text, new_x="LMARGIN", new_y="NEXT")

            pdf.ln(10)

        # Save to disk
        pdf.output(output_pdf)
        print(f"[++] PDF note generation completed successfully: {output_pdf}")
