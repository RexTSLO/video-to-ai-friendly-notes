# video-to-ai-friendly-notes

[English](README.md) | **繁體中文**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests Passed](https://img.shields.io/badge/tests-13%20passed-success.svg)](#單元與整合測試)

`video-to-ai-friendly-notes` 是一個模組化、輕量且高效的 Python 工具。它能夠一鍵下載 YouTube 課程影片（或讀取本地影片），自動偵測投影片切換畫面，整合語音轉文字（Speech-to-Text）生成精準字幕，最終編排輸出成**對 AI / LLM / RAG 極度友善的高結構化 PDF 講義筆記**（且完美支援繁體中文）。

---

## 🚀 核心特色

1.  **影格變更自動偵測 (Slide Detector)**：使用 OpenCV 進行相鄰影格的 MAE（Mean Absolute Error）差異演算。透過 1 FPS 降採樣、縮圖 `(160, 90)` 灰階優化，以極低的 CPU 開銷快速捕捉投影片切換時的關鍵畫面。
2.  **極速語音轉字幕 (Whisper Transcriber)**：直接整合 `faster-whisper` CTranslate2 推理引擎，不依賴額外的 CLI 包裝。當偵測語系為 `zh` 且無提供 initial prompt 時，**自動帶入繁體中文引導 prompt**，確保精準的繁體中文 SRT 字幕輸出。
3.  **對 AI / RAG 極友善的 PDF 講義編排**：
    *   **繁體中文支援**：首次執行時會自動下載並註冊 `NotoSansCJKtc` 字型，徹底防止中文字元在 PDF 中變成空白方塊（Glyph Error），並具備優雅的 system font fallback 機制。
    *   **高結構化 layout**：每頁包含明確的 `Slide X (Timestamp)` 標記區塊、投影片縮圖，以及與時間軸精準對齊的字幕筆記文字（`[MM:SS] 文字`），利於各類多模態大模型（VLM）與 RAG 系統直接高精確度解析。
4.  **強健的沙盒機制**：自動管理 `tempfile` 臨時資料夾。下載的影片與 OpenCV 擷取的暫存影格，在 Pipeline 處理完畢（或發生非預期錯誤）時，均保證在 `finally` 區塊中被**完美清理乾淨**。
5.  **100% 離線 CI-safe 測試**：本專案採用嚴格的 TDD 設計，所有重型與網路依賴元件（`yt-dlp`、`faster-whisper`、`cv2`、`urllib`、`fpdf2`）皆有對應的 mock 測試，使 13 個單元與整合測試案例能在 2 秒內於無 GPU、無連網環境下秒過。

---

## 🛠️ 系統依賴要求

本專案依賴 `ffmpeg` 來處理音訊流與影片轉譯。在開始前請確認您的系統中已安裝 `ffmpeg`：

*   **macOS** (使用 Homebrew):
    ```bash
    brew install ffmpeg
    ```
*   **Ubuntu / Debian**:
    ```bash
    sudo apt update
    sudo apt install ffmpeg
    ```

---

## ⚙️ 安裝說明

1.  **複製儲存庫**：
    ```bash
    git clone https://github.com/rextslo/video-to-ai-friendly-notes.git
    cd video-to-ai-friendly-notes
    ```

2.  **建立並啟用虛擬環境**：
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **安裝依賴套件**：
    ```bash
    pip install -r requirements.txt
    ```

---

## 📖 使用方法

您可以使用 CLI 整合工具一鍵完成整個轉譯與講義生成流程。

### 查看 CLI 幫助與參數說明
```bash
python3 -m src.main --help
```

### 1. 使用 YouTube 影片 URL 生成講義
```bash
python3 -m src.main -u "https://www.youtube.com/watch?v=aqz-KE-bpKQ" -o lecture_notes.pdf -m tiny -l zh
```

### 2. 使用本地影片檔案生成講義
```bash
python3 -m src.main -i "path/to/lecture.mp4" -o output_notes.pdf -t 15.0
```

> [!NOTE]  
> 執行完畢後，除了會在指定路徑生成 `.pdf` 講義外，亦會在同目錄下自動產生同名的 `.srt` 字幕檔案供您留存參考。

---

## 🎛️ CLI 參數說明

| 參數短寫 | 參數長寫 | 預設值 | 說明 |
| :--- | :--- | :--- | :--- |
| `-u` | `--url` | *None* | YouTube 課程影片的 URL（與 `-i` 互斥，兩者必填其一） |
| `-i` | `--input` | *None* | 本地影片的檔案路徑（與 `-u` 互斥，兩者必填其一） |
| `-o` | `--output` | `lecture_notes.pdf` | 生成的 PDF 講義路徑（同名 `.srt` 字幕亦會隨之輸出） |
| `-m` | `--model` | `medium` | `faster-whisper` 的模型大小（支援 `tiny`, `base`, `small`, `medium`, `large-v3`） |
| `-l` | `--lang` | `zh` | 語音轉譯的語系代碼（預設 `zh` 會自動帶入繁體中文優化 prompt） |
| `-t` | `--threshold`| `15.0` | 投影片切換偵測的 MAE 敏感度閾值（越低越敏感） |
| `-d` | `--device` | `cpu` | 計算推理硬體載體（`cpu` 或 `cuda`） |

---

## 📂 專案目錄結構

```text
video-to-ai-friendly-notes/
├── LICENSE             # MIT 授權條款
├── requirements.txt    # 專案依賴描述
├── src/
│   ├── __init__.py
│   ├── main.py         # 總入口與 CLI 沙盒協調器
│   ├── downloader.py   # yt-dlp 影片下載模組
│   ├── transcriber.py  # faster-whisper 轉譯與 SRT 輸出模組
│   ├── detector.py     # OpenCV 投影片變更偵測模組
│   └── generator.py    # CJK 講義排版與 PDF 渲染模組
└── tests/
    ├── __init__.py
    ├── test_downloader.py
    ├── test_transcriber.py
    ├── test_detector.py
    ├── test_generator.py
    └── test_integration.py
```

---

## 🧪 單元與整合測試

本專案擁有 100% 覆蓋核心 API 的測試套件。執行測試完全不消耗外部網路流量、不讀寫真實影片，保證 CI-safe：

```bash
PYTHONPATH=. ./venv/bin/pytest -v
```

**期望輸出**：
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

## 📄 授權條款

本專案採用 [MIT License](LICENSE) 授權條款開源發布。
