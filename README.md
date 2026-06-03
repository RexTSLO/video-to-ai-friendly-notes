# video-to-ai-friendly-notes

**English** | [繁體中文](README.zh-TW.md)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests Passed](https://img.shields.io/badge/tests-25%20passed-success.svg)](#unit--integration-testing)

`video-to-ai-friendly-notes` is a modular, lightweight, and efficient Python tool. Simply provide a YouTube URL or a local video file, and it will automatically **download the video, extract slide frames, transcribe the speech, and align them**. The result is a **structured PDF study guide optimized for both human reading and AI/RAG (such as Google NotebookLM) ingestion**.

---

## 🚀 Core Features

1. **Automated Slide Capture (Slide Detector)**: Automatically detects when a slide changes and captures keyframes, filtering out transitional blur, animations, and black/blank screens. Supports **Animation Consolidation Mode** (`--slide-mode`) to merge incremental slide animations into a single finished slide, capturing complete content without creating duplicate pages.
2. **Audio Transcription (Whisper Transcriber)**: Directly integrates the `faster-whisper` CTranslate2 inference engine without relying on external CLI wrappers.
3. **Aligned Multi-modal Layout (AI & Human Friendly)**:
   * **CJK/Chinese Support**: Automatically registers CJK fonts on first run to eliminate empty square characters (glyph errors) in generated PDFs.
   * **Structured Pairing**: Pairs each slide image side-by-side with its chronological speech transcript on a page-by-page basis for easy reference.
4. **Optimized for NotebookLM & RAG (AI-Ready)**:
    * The output PDF is chunked naturally page-by-page based on slide transitions (`Slide X [MM:SS]`). This acts as native **Semantic Chunking** for LLMs/RAG, enabling models like NotebookLM to retrieve answers, cite timestamps and page numbers, and reduce input token overhead.
5. **Smart Directory Dispatching**: Downloaded YouTube videos are saved under the `inputs/` directory, while all generated outputs are automatically cataloged and dispatched to dedicated subdirectories under `outputs/` (`pdf/`, `subtitles/`, and `slides/`).

---

## 🎬 Showcase

Below are showcases demonstrating how `video-to-ai-friendly-notes` processes different subtitle flows to generate structured notes. Placeholders are set up below for your actual video assets and generated PDFs:

### 1. Processing Official YouTube Subtitles (YT Manual Subtitles)
Designed for long-form lecture videos (e.g., 1+ hour courses). Directly downloads officially curated and proofread Traditional Chinese subtitles via `--subs-from-yt zh-TW`. **Skips local AI inference time**, delivering fast compilation with semantic structure and alignment.
*   **Best Suited For**: Long-form academic lectures, major developer conferences (e.g., Google I/O, WWDC), or online courses (Coursera, edX) that come with high-quality, pre-uploaded official subtitles.
*   **Video Source**: <!-- [Insert YouTube video link or title here] -->
*   **Generated PDF**: <!-- [Insert link to generated PDF notes here] -->
*   **Visual Comparison**:
    | Original Video Frame | Structured Slide & Synced Subtitles |
    | :---: | :---: |
    | ![Original Video Frame](<!-- [Insert original frame screenshot path here] -->) | ![Generated PDF Page](<!-- [Insert generated PDF preview image path here] -->) |

### 2. Processing YouTube Auto-Generated Subtitles (YT Auto-generated Subtitles)
For videos without pre-uploaded manual subtitles, this flow seamlessly downloads and processes auto-translated/auto-generated subtitles provided by the YouTube platform to synthesize structural slide-notes on the fly.
*   **Best Suited For**: Time-sensitive daily news, financial/market analysis commentaries, talk shows with supporting slides/infographics, where no official subtitles are uploaded.
*   **Video Source**: <!-- [Insert YouTube video link or title here] -->
*   **Generated PDF**: <!-- [Insert link to generated PDF notes here] -->
*   **Visual Comparison**:
    | Original Video Frame | Structured Slide & Synced Subtitles |
    | :---: | :---: |
    | ![Original Video Frame](<!-- [Insert original frame screenshot path here] -->) | ![Generated PDF Page](<!-- [Insert generated PDF preview image path here] -->) |

### 3. Local AI Speech-to-Text Transcription (Local AI Transcription)
For local video uploads or YouTube videos completely lacking online subtitles. Uses the local `faster-whisper` CTranslate2 inference engine. When Mandarin audio is detected, it **automatically injects a Traditional Chinese guiding prompt** to output offline Traditional Chinese SRT subtitles.
*   **Best Suited For**: Locally recorded classes/meetings (MP4), lecture recordings without any online subtitles, personal programming tutorials (e.g., self-made coding tutorials on YouTube), or field recordings.
*   **Video Source**: <!-- [Insert YouTube video link or title here] -->
*   **Generated PDF**: <!-- [Insert link to generated PDF notes here] -->
*   **Visual Comparison**:
    | Original Video Frame | Structured Slide & Synced Subtitles |
    | :---: | :---: |
    | ![Original Video Frame](<!-- [Insert original frame screenshot path here] -->) | ![Generated PDF Page](<!-- [Insert generated PDF preview image path here] -->) |
---

## 💡 Why generated PDFs are useful for NotebookLM & AI/RAG ingestion?

When importing learning resources into Google NotebookLM or other RAG/LLM knowledge bases, pasting raw YouTube links or uploading plain transcripts often yields sub-optimal responses. The PDFs generated by this utility provide key structural advantages for AI-generated outputs:

1. **Multimodal Semantic Alignment**
   * **The Problem**: Giving AI text-only subtitles denies it visual context (e.g., architecture diagrams, code blocks, slide metrics). Giving it raw video presents high processing latency and alignment issues.
   * **The Solution**: The output PDF places the key slide screenshot and the speaker's synchronized explanation in the exact same visual block. Multimodal models (like Gemini 1.5 / 2.0 Pro inside NotebookLM) read both graphics and text simultaneously, capturing context.

2. **Precise Pagination & Chunking Anchors**
   * **The Problem**: Long speech transcript sheets lack structural boundaries. RAG vector search engines suffer from "context drift", retrieving fragments across unrelated topics and leading to AI hallucinations.
   * **The Solution**: The PDF organizes pages explicitly by individual slide changes (`Slide X [MM:SS]`). This creates natural semantic chunking boundaries, helping the AI quote time-stamped sources and page numbers.

3. **Filtering Noise & Maximizing Token Efficiency**
   * **The Problem**: Uploading whole raw videos wastes inputs/token counts on duplicate static slides and filler audio/redundancy.
   * **The Solution**: Automatically filters transition animations and duplicates to preserve only high-value slides and clear transcript sections, saving cost and improving response speeds.

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

### 1. List Available Subtitles from YouTube
```bash
python3 -m src.main -u "https://www.youtube.com/watch?v=xxx" --list-subs
```

### 2. Process from YouTube Video URL
```bash
python3 -m src.main -u "https://www.youtube.com/watch?v=xxx" -o lecture_notes.pdf --subs-from-yt zh-TW
```

### 3. Process from Local Video File
```bash
python3 -m src.main -i "path/to/lecture.mp4" -o output_notes.pdf -m medium -l zh
```

> [!NOTE]  
> Upon successful completion, the script automatically saves both the `.pdf` formatted notes and a companion `.srt` subtitle file under the **`outputs/`** directory to keep your root directory clean.

---

## 🎛️ CLI Argument Options

| Short | Long | Default | Description |
| :--- | :--- | :--- | :--- |
| `-u` | `--url` | *None* | YouTube lecture video URL to download (mutually exclusive with `-i`). |
| `-i` | `--input` | *None* | Path to a local video file (mutually exclusive with `-u`). |
| *None* | `--list-subs` | *None* | List available subtitles (manual and automatic) on YouTube for the URL and exit (only works with `-u/--url`). |
| `-o` | `--output` | `outputs/lecture_notes.pdf` | Destination path for the final PDF note (and companion `.srt` subtitles, directory will be created automatically if missing). |
| `-m` | `--model` | `medium` | Whisper model size (`tiny`, `base`, `small`, `medium`, `large-v3`). |
| `-l` | `--lang` | `zh` | Language code (default `zh` triggers Traditional Chinese prompt). |
| `-t` | `--threshold`| `auto` | OpenCV slide detection sensitivity threshold (float value, or `"auto"` to dynamically compute optimal threshold using MAD outlier statistics). |
| `-d` | `--device` | `cpu` | Target computation inference device (`cpu` or `cuda`). |
| *None* | `--subs-from-yt` | *None* | Directly download specified subtitle language from YouTube (e.g. `zh-TW`), bypassing local Whisper. Errors out if missing. |
| *None* | `--max-res` | `720` | Maximum height resolution for downloaded YouTube video (e.g., `480`, `720`, `1080`) to optimize download and OpenCV performance. |
| *None* | `--time-range` | *None* | Specific section of the video to download and process in `HH:MM:SS-HH:MM:SS` format. |
| *None* | `--srt` | *None* | Path to a local `.srt` or `.vtt` file to use, completely bypassing Whisper transcribing and YouTube subtitle downloading. |
| *None* | `--min-duration` | `1.0` | Minimum slide duration cooldown in seconds between two slide transitions (lower = more keyframes for rapid slide changes). |
| *None* | `--slide-mode` | `final` | Slide animation capture strategy (`final` to keep only the completed slide, `all` to capture all stages, `first` to keep only the initial state). |



---

## 📂 Repository File Tree

```text
video-to-ai-friendly-notes/
├── LICENSE             # MIT License
├── requirements.txt    # Project Python packages
├── inputs/             # Successfully downloaded videos
├── outputs/            # Isolated and typeset project outputs
│   ├── pdf/            # Formatted PDF notes
│   ├── subtitles/      # Synchronization .srt subtitles
│   └── slides/         # OpenCV typeset slide images
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

The codebase includes high-fidelity unit and integration tests (total of 25 test cases). Tests run completely offline without downloading model parameters or video binaries:

```bash
PYTHONPATH=. ./venv/bin/pytest -v
```

**Expected Output**:
```text
============================== 25 passed in 1.94s ==============================
```

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
