# video-to-ai-friendly-notes

**English** | [繁體中文](README.zh-TW.md)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests Passed](https://img.shields.io/badge/tests-13%20passed-success.svg)](#unit--integration-testing)

`video-to-ai-friendly-notes` is a modular, lightweight, and highly efficient Python command-line utility. It automates downloading lecture videos from YouTube (or processing local video files), detects slide changes, generates precise synchronized speech-to-text transcripts, and ultimately exports them into **beautifully typeset, highly structured, AI-friendly PDF study notes** (with robust out-of-the-box Traditional Chinese support).

---

## 🚀 Core Features

1.  **Slide Transition Detection (OpenCV)**: Evaluates frame difference using Mean Absolute Error (MAE) algorithms. Implements 1 FPS downsampling, frame downscaling `(160, 90)`, and grayscale conversions to keep CPU overhead exceptionally low during video parsing.
2.  **Fast Whisper Transcription (faster-whisper)**: Integrates `faster-whisper` using CTranslate2 engine directly for fast local inference. When transcribing in Chinese (`zh`), it **automatically injects a Traditional Chinese prompt** to guide translation output without simplified character leakage.
3.  **VLM & RAG Optimized PDF Layout**:
    *   **Chinese & CJK Glyphs Support**: Proactively downloads and caches CJK fonts (`NotoSansCJKtc`) on first launch to eliminate empty block characters (Glyph errors), while offering an elegant defensive Helvetica font fallback.
    *   **High Semantic Structure**: Each page contains explicit `Slide X (Timestamp)` delimiters, a centered slide image, and chronological, multi-line auto-wrapped transcripts (`[MM:SS] Subtitles`). This layout is highly optimized for parsing by Multimodal Large Language Models (VLMs) and RAG parsers.
4.  **Sandbox Workspace Isolation**: Safely partitions downloads and OpenCV frames in temporary folders using `tempfile`. Pure folder isolation is guaranteed; temporary workspaces are **securely wiped** inside the `finally` block even if unexpected pipe failures occur.
5.  **100% Offline CI-safe Mocks**: Features offline testing where all network or heavy external engines (`yt-dlp`, `faster-whisper`, `cv2`, `urllib`, `FPDF`) are mock decoupled. Run the entire suite of 13 tests in less than 2 seconds completely offline.

---

## 🛠️ System Prerequisites

This project utilizes `ffmpeg` for extracting and processing audio streams. Please ensure `ffmpeg` is installed on your local machine:

*   **macOS** (via Homebrew):
    ```bash
    brew install ffmpeg
    ```
*   **Ubuntu / Debian**:
    ```bash
    sudo apt update
    sudo apt install ffmpeg
    ```

---

## ⚙️ Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/rextslo/video-to-ai-friendly-notes.git
    cd video-to-ai-friendly-notes
    ```

2.  **Create and Activate Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Required Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

---

## 📖 Usage

Run the master orchestrator CLI script to execute the entire pipeline with a single command.

### Access Help Instructions
```bash
python3 -m src.main --help
```

### 1. Process from YouTube Video URL
```bash
python3 -m src.main -u "https://www.youtube.com/watch?v=aqz-KE-bpKQ" -o lecture_notes.pdf -m tiny -l zh
```

### 2. Process from Local Video File
```bash
python3 -m src.main -i "path/to/lecture.mp4" -o output_notes.pdf -t 15.0
```

> [!NOTE]  
> Upon successful completion, the script saves both the `.pdf` formatted notes and a companion `.srt` subtitle file under your target output folder.

---

## 🎛️ CLI Argument Options

| Short | Long | Default | Description |
| :--- | :--- | :--- | :--- |
| `-u` | `--url` | *None* | YouTube lecture video URL to download (mutually exclusive with `-i`). |
| `-i` | `--input` | *None* | Path to a local video file (mutually exclusive with `-u`). |
| `-o` | `--output` | `lecture_notes.pdf` | Destination path for the final PDF note (and companion `.srt` subtitles). |
| `-m` | `--model` | `medium` | Whisper model size (`tiny`, `base`, `small`, `medium`, `large-v3`). |
| `-l` | `--lang` | `zh` | Language code (default `zh` triggers Traditional Chinese prompt). |
| `-t` | `--threshold`| `15.0` | OpenCV slide detection sensitivity threshold (lower = more keyframes). |
| `-d` | `--device` | `cpu` | Target computation inference device (`cpu` or `cuda`). |

---

## 📂 Repository File Tree

```text
video-to-ai-friendly-notes/
├── LICENSE             # MIT License
├── requirements.txt    # Project Python packages
├── src/
│   ├── __init__.py
│   ├── main.py         # Entrypoint orchestrator and CLI parser
│   ├── downloader.py   # yt-dlp downloading module
│   ├── transcriber.py  # faster-whisper transcribing and SRT exporter
│   ├── detector.py     # OpenCV slide change detector
│   └── generator.py    # CJK layout and PDF compiler
└── tests/
    ├── __init__.py
    ├── test_downloader.py
    ├── test_transcriber.py
    ├── test_detector.py
    ├── test_generator.py
    └── test_integration.py
```

---

## 🧪 Unit & Integration Testing

The codebase includes high-fidelity unit and integration tests. Tests run completely offline without downloading model parameters or video binaries:

```bash
PYTHONPATH=. ./venv/bin/pytest -v
```

**Expected Output**:
```text
tests/test_detector.py::test_calculate_diff PASSED                       [  7%]
tests/test_detector.py::test_detect_slides_failure PASSED                [ 15%]
tests/test_detector.py::test_detect_slides_success PASSED                [ 23%]
tests/test_downloader.py::test_download_video PASSED                     [ 30%]
tests/test_downloader.py::test_download_failure PASSED                   [ 38%]
tests/test_generator.py::test_bind_subtitles_to_keyframes PASSED         [ 46%]
tests/test_generator.py::test_pdf_generation_mocked PASSED               [ 53%]
tests/test_integration.py::test_cli_help_flag PASSED                     [ 61%]
tests/test_integration.py::test_orchestration_pipeline_mocked PASSED     [ 69%]
tests/test_transcriber.py::test_transcribe_success_zh_default_prompt PASSED [ 76%]
tests/test_transcriber.py::test_transcribe_success_custom_prompt PASSED  [ 84%]
tests/test_transcriber.py::test_transcribe_file_not_found PASSED         [ 92%]
tests/test_transcriber.py::test_write_srt PASSED                         [100%]

============================== 13 passed in 1.66s ==============================
```

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
