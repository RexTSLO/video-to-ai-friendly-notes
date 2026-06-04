# video-slide-notes

### 🤖 AI-friendly Video Lecture Notes Generator

**English** | [繁體中文](README.zh-TW.md)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests Passed](https://img.shields.io/badge/tests-25%20passed-success.svg)](#unit--integration-testing)

`video-slide-notes` is an AI-friendly, modular, lightweight, and efficient Python tool. Simply provide a YouTube URL or a local video file, and it will automatically **download the video, extract slide frames, transcribe the speech, and align them**. The result is a **structured PDF study guide optimized for both human reading and AI/RAG (such as Google NotebookLM) ingestion**.

---

## 🚀 Core Features

1. **Automated Slide Capture (Slide Detector)**: Automatically detects when a slide changes and captures keyframes, filtering out transitional blur, animations, and black/blank screens. Supports **Animation Consolidation Mode** (`--slide-mode`) to merge incremental slide animations into a single finished slide, capturing complete content without creating duplicate pages.
2. **Audio Transcription (Whisper Transcriber)**: Directly integrates the `faster-whisper` CTranslate2 inference engine without relying on external CLI wrappers.
3. **Aligned Multi-modal Layout (AI & Human Friendly)**:
   * **CJK/Chinese Support**: Automatically registers CJK fonts on first run to eliminate empty square characters (glyph errors) in generated PDFs.
   * **Structured Pairing**: Pairs each slide image side-by-side with its chronological speech transcript on a page-by-page basis for easy reference.
4. **Optimized for NotebookLM & RAG (AI-Ready)**:
    * **Multimodal Semantic Alignment**: Pairs slide screenshots side-by-side with synchronized speech transcripts, enabling multimodal models (like Gemini Pro in NotebookLM) to ingest text and graphics simultaneously and retain deep technical context.
    * **Precise Pagination & Chunking Anchors**: Organizes the PDF page-by-page based on slide transitions. This serves as native semantic chunking boundaries, avoiding context drift during vector search and enabling precise citations of timestamps and page numbers.
    * **Noise Filtering & Token Efficiency**: Eliminates transition animations, duplicate keyframes, and speech filler noise, leaving only high-value slides and clean transcripts to minimize token consumption and speed up query processing.

---

## 🎬 Showcase

Below are showcases demonstrating how `video-slide-notes` processes different subtitle flows to generate structured notes. Placeholders are set up below for your actual video assets and generated PDFs:

### 1. Processing Official YouTube Subtitles (YT Manual Subtitles)
Designed for long-form lecture videos (e.g., 1+ hour courses). Directly downloads officially curated and proofread Traditional Chinese subtitles via `--subs-from-yt zh-TW`. **Skips local AI inference time**, delivering fast compilation with semantic structure and alignment.
*   **Best Suited For**: Long-form academic lectures, major developer conferences (e.g., Google I/O, WWDC), or online courses (Coursera, edX) that come with high-quality, pre-uploaded official subtitles.
*   **Video Source**: [Harness Engineering: Sometimes language models are not unintelligent, they just lack proper human guidance](https://www.youtube.com/watch?v=R6fZR_9kmIw)
*   **Generated PDF**: [v0.1.0_assets_1.pdf](https://github.com/RexTSLO/video-slide-notes/releases/download/v0.1.0/v0.1.0_assets_1.pdf)
*   **Visual Comparison**:
    | Original Video Frame | Structured Slide & Synced Subtitles |
    | :---: | :---: |
    | ![Original Video Frame](https://github.com/user-attachments/assets/f3982f21-2192-4e56-95d1-73eb7e4e6dcd) | ![Generated PDF Page](https://github.com/user-attachments/assets/9f308811-4f78-43b9-8d65-d49bae24a736) |
#### 📊 NotebookLM Response Comparison

| ❌ YouTube Link / Text-only Transcript (AI lacks visual context, leading to generalized answers) |
| :---: |
| ![NotebookLM Text Limitation](https://github.com/user-attachments/assets/ceac5b69-f380-4951-843e-cfeacbe68e42) |

| 🚀 PDF Slides Notes from this Project (Multimodal alignment, leading to precise answers) |
| :---: |
| ![NotebookLM Multimodal Precise Answer](https://github.com/user-attachments/assets/a2b1d739-5ccc-4100-acb3-a7a0c1c5c230) |
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
    git clone https://github.com/rextslo/video-slide-notes.git
    cd video-slide-notes
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
> **Smart Directory Dispatching**: Downloaded YouTube videos are saved under the `inputs/` directory, while all generated outputs (PDF notes, companion `.srt` subtitles, and slide images) are automatically cataloged and dispatched to dedicated subdirectories under `outputs/` (`pdf/`, `subtitles/`, and `slides/`).

### 🔑 YouTube Authentication (Bypassing 429 Rate Limits)

To prevent `HTTP Error 429: Too Many Requests` or to download private/age-restricted videos, you can provide a Netscape cookies file using the `--cookies` parameter.

#### 🛡️ Best Security Practice (Minimalist Export)
For maximum privacy, the `--cookies-from-browser` feature of `yt-dlp` is currently not supported. Instead, it is highly recommended to **manually export** a Netscape format cookies file and filter it to keep only the essential cookies for YouTube:

1. Log in to YouTube in your browser.
2. Export your cookies in **Netscape** format using a browser extension (such as [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc?hl=en)).
3. Edit the exported text file and delete all lines **except** the following two essential cookies:
   * **`LOGIN_INFO`**: Handles the YouTube-specific login authentication.
   * **`VISITOR_INFO1_LIVE`**: Used by YouTube to recognize your visitor session (necessary to bypass anti-bot 429 rate limits).
4. Run the tool with:
   ```bash
   python3 -m src.main -u "https://www.youtube.com/watch?v=xxx" --cookies downloads/your_youtube_cookies.txt
   ```

---

## 🎛️ CLI Argument Options

| Short | Long | Default | Description |
| :--- | :--- | :--- | :--- |
| `-u` | `--url` | *None* | YouTube lecture video URL to download (mutually exclusive with `-i`). |
| `-i` | `--input` | *None* | Path to a local video file (mutually exclusive with `-u`). |
| *None* | `--list-subs` | *None* | List available subtitles (manual and automatic) on YouTube for the URL and exit (only works with `-u/--url`). |
| `-o` | `--output` | `outputs/lecture_notes.pdf` | Destination path for the final PDF note (and companion `.srt` subtitles, directory will be created automatically if missing). |
| `-m` | `--model` | `medium` | Whisper model size (`tiny`, `base`, `small`, `medium`, `large-v3`). |
| `-l` | `--lang` | `zh` | Language code (default `zh`). |
| `-t` | `--threshold`| `auto` | OpenCV slide detection sensitivity threshold (float value, or `"auto"` to dynamically compute optimal threshold using MAD outlier statistics). |
| `-d` | `--device` | `cpu` | Target computation inference device (`cpu` or `cuda`). |
| *None* | `--subs-from-yt` | *None* | Directly download specified subtitle language from YouTube (e.g. `zh-TW`), bypassing local Whisper. Errors out if missing. |
| *None* | `--max-res` | `720` | Maximum height resolution for downloaded YouTube video (e.g., `480`, `720`, `1080`) to optimize download and OpenCV performance. |
| *None* | `--time-range` | *None* | Specific section of the video to download and process in `HH:MM:SS-HH:MM:SS` format. |
| *None* | `--srt` | *None* | Path to a local `.srt` or `.vtt` file to use, completely bypassing Whisper transcribing and YouTube subtitle downloading. |
| *None* | `--cookies` | *None* | Path to a cookies file in Netscape format (useful to bypass 429 rate limit errors). |
| *None* | `--min-duration` | `1.0` | Minimum slide duration cooldown in seconds between two slide transitions (lower = more keyframes for rapid slide changes). |
| *None* | `--slide-mode` | `final` | Slide animation capture strategy (`final` to keep only the completed slide, `all` to capture all stages, `first` to keep only the initial state). |
| *None* | `--skip-talking-heads` | `False` | Skip duplicate speaker talking head frames by keeping only the first one until the next slide is detected (uses YuNet CNN face detector). |




---

## 📂 Repository File Tree

```text
video-slide-notes/
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

---

## ⚖️ Disclaimer

* **Purpose**: This project is intended solely for educational, academic research, and technical exchange purposes.
* **Copyright Compliance**: When downloading/transcribing videos and compiling notes, users are solely responsible for ensuring compliance with local copyright laws. Generated PDF notes must not be used for commercial reproduction, public redistribution, or any other activities infringing upon the intellectual property of original content creators.
* **Third-Party Terms**: This utility uses `yt-dlp` to retrieve public YouTube assets. Users assume all responsibility for any account restrictions resulting from violations of YouTube's Terms of Service. The project authors assume no liability for user activities.
