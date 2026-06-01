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
