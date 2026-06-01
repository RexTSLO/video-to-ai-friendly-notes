import os
from faster_whisper import WhisperModel

class SubtitleTranscriber:
    """A transcription module that handles transcribing video/audio media files using faster-whisper

    and outputting standard, high-compatibility .srt files.
    """

    def __init__(self, model_size: str = "medium", device: str = "cpu") -> None:
        """Initialize the SubtitleTranscriber with a whisper model size and computing device.

        Args:
            model_size: Size of the whisper model to load (e.g. tiny, base, small, medium, large-v3).
            device: Device to use for computation ("cpu" or "cuda").
        """
        self.model = WhisperModel(model_size, device=device, compute_type="float32")

    def transcribe(self, media_path: str, lang: str = "zh", initial_prompt: str = None) -> list[dict]:
        """Transcribe the speech in the media file and return structured segment details.

        Args:
            media_path: The absolute or relative path to the media file.
            lang: Language code (default "zh" for Chinese).
            initial_prompt: Optional initial prompt to guide whisper's style/vocab.

        Returns:
            A list of segment dictionaries, e.g., [{"start": 0.0, "end": 2.5, "text": "哈囉"}]

        Raises:
            FileNotFoundError: If the media_path does not exist.
        """
        if not os.path.exists(media_path):
            raise FileNotFoundError(f"Media file not found at: {os.path.abspath(media_path)}")

        # Optimize output for Traditional Chinese if lang is "zh" and no prompt is provided.
        if lang == "zh" and initial_prompt is None:
            initial_prompt = "這是一個繁體中文的字幕。請用繁體中文輸出接下來的內容。"

        segments_generator, _ = self.model.transcribe(
            media_path,
            language=lang,
            initial_prompt=initial_prompt
        )

        # Convert generator to structured list of dicts
        segments = []
        for seg in segments_generator:
            segments.append({
                "start": float(seg.start),
                "end": float(seg.end),
                "text": str(seg.text)
            })

        return segments

    def write_srt(self, segments: list[dict], srt_filepath: str) -> None:
        """Write the transcribed segments to a file in standard .srt subtitle format.

        Args:
            segments: List of segment dictionaries containing 'start', 'end', and 'text'.
            srt_filepath: Destination path for the .srt file.
        """
        def format_time(seconds: float) -> str:
            # Avoid floating point precision issues by converting to total milliseconds
            total_ms = int(round(seconds * 1000))
            hrs = total_ms // 3600000
            total_ms %= 3600000
            mins = total_ms // 60000
            total_ms %= 60000
            secs = total_ms // 1000
            ms = total_ms % 1000
            return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"

        with open(srt_filepath, "w", encoding="utf-8") as f:
            for idx, seg in enumerate(segments, 1):
                f.write(f"{idx}\n")
                f.write(f"{format_time(seg['start'])} --> {format_time(seg['end'])}\n")
                f.write(f"{seg['text'].strip()}\n\n")

    @staticmethod
    def parse_srt(srt_filepath: str) -> list[dict]:
        """Parse a standard .srt or .vtt subtitle file into a list of segment dictionaries.

        Args:
            srt_filepath: Path to the .srt or .vtt file.

        Returns:
            A list of segment dictionaries containing 'start', 'end', and 'text'.
        """
        if not os.path.exists(srt_filepath):
            raise FileNotFoundError(f"Subtitle file not found at: {os.path.abspath(srt_filepath)}")

        def parse_time(time_str: str) -> float:
            time_str = time_str.replace(",", ".").strip()
            parts = time_str.split(":")
            if len(parts) == 3:
                hrs = int(parts[0])
                mins = int(parts[1])
                secs = float(parts[2])
                return hrs * 3600.0 + mins * 60.0 + secs
            elif len(parts) == 2:
                mins = int(parts[0])
                secs = float(parts[1])
                return mins * 60.0 + secs
            return float(time_str) if time_str else 0.0

        segments = []
        with open(srt_filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            
            # Normalize line endings and split by empty line separating blocks
            blocks = content.replace("\r\n", "\n").split("\n\n")
            for block in blocks:
                lines = [line.strip() for line in block.split("\n") if line.strip()]
                # Find the timing line that contains "-->"
                time_idx = -1
                for idx, line in enumerate(lines):
                    if "-->" in line:
                        time_idx = idx
                        break
                
                if time_idx != -1 and time_idx + 1 < len(lines):
                    time_line = lines[time_idx]
                    time_parts = time_line.split("-->")
                    start_sec = parse_time(time_parts[0])
                    end_sec = parse_time(time_parts[1])
                    
                    # Text is all lines after the timing line
                    text = " ".join(lines[time_idx + 1:])
                    
                    # Strip VTT style/tag sequences (e.g. <c.traditional>, <b>)
                    import re
                    text = re.sub(r"<[^>]+>", "", text)
                    
                    segments.append({
                        "start": start_sec,
                        "end": end_sec,
                        "text": text
                    })
        return segments

