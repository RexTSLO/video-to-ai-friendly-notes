# video-to-ai-friendly-notes

[English](README.md) | **繁體中文**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests Passed](https://img.shields.io/badge/tests-25%20passed-success.svg)](#單元與整合測試)

`video-to-ai-friendly-notes` 是一個模組化、輕量且高效的 Python 工具。只需輸入一個 YouTube 連結或本地影片，它就能自動**下載影片、擷取投影片畫面、將語音轉為逐字稿，並將圖文對齊編排**。最終為您生成一份**適合人類閱讀與 AI/RAG（如 Google NotebookLM）解析的結構化 PDF 講義筆記**。

---

## 🚀 核心功能

1. **投影片畫面自動擷取 (Slide Detector)**：自動偵測並擷取投影片切換的關鍵影格，過濾切換過程中的模糊動畫與黑白屏。特別支援**動畫整合模式** (`--slide-mode`)，能將逐步疊加（Build-up）的投影片動畫合併為最終完成版，既保留完整簡報內容，又不會產生多餘的重複頁面。
2. **極速語音轉字幕 (Whisper Transcriber)**：直接整合 `faster-whisper` CTranslate2 推理引擎，不依賴額外的 CLI 包裝。
3. **對齊的圖文講義排版 (AI & Human Friendly Layout)**：
   * **繁體中文支援**：首次執行時會自動下載並註冊中文字型，徹底防止中文字元在 PDF 中變成空白方塊（豆腐字）。
   * **高結構化排版**：每頁講義皆將「投影片關鍵影格」與「該時間區段的口述逐字稿」排版在同一個視覺區塊中，方便快速對照。
4. **針對 AI 與 RAG 讀取優化 (AI-Ready)**：
   * 產出的 PDF 講義以每張投影片為單位（`Slide X [MM:SS]`）進行分頁與排版。這對 AI 來說是「知識分塊 (Semantic Chunking)」，讓 NotebookLM 等大模型在解讀或檢索時，能夠定位到具體的時間戳記與投影片頁碼，提高回答準確度並減少 Token 消耗。
5. **目錄分流 (Smart Output Dispatcher)**：Youtube下載影片會存放於 `inputs/` 目錄下；所有產出則會自動分門別類存放於 `outputs/` 目錄下（PDF 講義存放於 `pdf/`、字幕存放於 `subtitles/`、投影片圖檔則歸類於 `slides/`）。


---

## 🎬 使用範例 (Showcase)

以下展示了三種不同字幕處理路徑下的實際影片與產出講義對比，協助您了解 `video-to-ai-friendly-notes` 在不同情境下的使用方法：

### 1. 載入手動建立的 YouTube 官方字幕 (YT Manual Subtitles)
針對長時間影片（例如 1 小時以上的演講或課程），直接使用 `--subs-from-yt zh-TW` 下載手動校對的官方繁體中文字幕。**跳過本地 AI 轉譯時間**，生成具備高結構化排版與時間軸對齊的 PDF 筆記。
*   **適合影片類型**：有官方精心翻譯/校對字幕的長時間學術演講、大型開發者大會（如 Google I/O、WWDC）、Coursera 或 edX 等線上課程影片。
*   **示範影片**：<!-- [請在此填入 YouTube 影片連結或名稱] -->
*   **產出 PDF**：<!-- [請在此填入 PDF 檔案下載連結] -->
*   **效果展示**：
    | 原始影片畫面 | 產出之完成版投影片與字幕對齊 |
    | :---: | :---: |
    | ![原始影片截圖](<!-- [請在此填入原始影片截圖路徑] -->) | ![產出 PDF 頁面](<!-- [請在此填入 PDF 預覽圖片路徑] -->) |

### 2. 載入 YouTube 自動生成的字幕 (YT Auto-generated Subtitles)
針對沒有提供手動校對字幕、僅有 YouTube 系統語音識別自動生成字幕的影片。本工具可直接無縫下載並解析其自動生成字幕（支援自動翻譯/自動轉譯語系），產出講義。
*   **適合影片類型**：時效性高的每日新聞、財經速讀解說影片、談話性節目（帶有輔助投影片或大字卡背景），且原作者未提供手動上傳字幕者。
*   **示範影片**：<!-- [請在此填入 YouTube 影片連結或名稱] -->
*   **產出 PDF**：<!-- [請在此填入 PDF 檔案下載連結] -->
*   **效果展示**：
    | 原始影片畫面 | 產出之完成版投影片與字幕對齊 |
    | :---: | :---: |
    | ![原始影片截圖](<!-- [請在此填入原始影片截圖路徑] -->) | ![產出 PDF 頁面](<!-- [請在此填入 PDF 預覽圖片路徑] -->) |

### 3. 本地 AI 語音轉文字生成字幕 (Local AI Transcription)
針對完全沒有任何線上字幕的 YouTube 影片，或是本地上傳的課程影片檔。本專案將自動調用本地 `faster-whisper` CTranslate2 推理引擎，在偵測到中文語音時自動注入繁體中文引導 Prompt，離線生成繁體中文 SRT 並編排為結構化 PDF。
*   **適合影片類型**：本地錄影課（MP4 檔）、學校課程錄影、線上未提供任何中文字幕的個人國外技術教學（如自製 Coding Tutorial）、或是實地演講錄音影片。
*   **示範影片**：<!-- [請在此填入 YouTube 影片連結或名稱] -->
*   **產出 PDF**：<!-- [請在此填入 PDF 檔案下載連結] -->
*   **效果展示**：
    | 原始影片畫面 | 產出之完成版投影片與字幕對齊 |
    | :---: | :---: |
    | ![原始影片截圖](<!-- [請在此填入原始影片截圖路徑] -->) | ![產出 PDF 頁面](<!-- [請在此填入 PDF 預覽圖片路徑] -->) |

---

## 💡 為什麼本專案生成的 PDF 比影片/純文字更適合匯入 NotebookLM？

當您將學習資源匯入 Google NotebookLM 或其他 RAG/LLM 知識庫時，直接貼上 YouTube 連結或純逐字稿往往效果有限。本專案產出的 PDF 講義具備以下核心優勢，能提升 AI 的回答品質：

1. **多模態語意對齊 (Multimodal Alignment)**
   * **問題**：只餵給 AI 純文字字幕時，AI 無法得知「投影片上的架構圖」、「程式碼截圖」或「數據圖表」長怎樣；而直接給影片時，AI 難以定位影像與講者口述的對應關係。
   * **解決方案**：本專案產出的 PDF 將「關鍵投影片影格」與「該時間區段的口述字幕」排版在同一個視覺區塊中。不論是支援多模態的 NotebookLM，或是其他多模態 RAG 系統，都能同時讀取圖表與文字，理解更深層的脈絡。

2. **分頁與主題錨點 (Structured Segmentation)**
   * **問題**：長篇的口講逐字稿通常沒有段落，AI 在進行向量檢索（Retrieval）時，容易把前後無關的段落混淆在一起（Context Drift），導致回答張冠李戴。
   * **解決方案**：PDF 講義以每張投影片為單位（`Slide X [MM:SS]`）進行分頁與排版。這對 AI 來說是「語意分塊（Chunking）」，確保 AI 能給出帶有時間戳記與頁碼的參考來源。

3. **過濾無效資訊，提升 Token 密度 (Token & Cost Efficiency)**
   * **問題**：若直接將整段影片餵給多模態大模型，會消耗極大量的 Input Token，且影片中多數時間投影片是靜止的，產生大量重複影格與無效的語音贅詞。
   * **解決方案**：自動過濾轉場動畫與重複影格，只保留精煉後的投影片圖像與去蕪存菁的字幕，大幅節省 AI 處理的 Token 消耗，提高檢索速度。

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

### 1. 查詢 YouTube 影片上可下載的字幕列表
```bash
python3 -m src.main -u "https://www.youtube.com/watch?v=xxx" --list-subs
```
### 2. 使用 YouTube 影片 URL 生成講義
```bash
python3 -m src.main -u "https://www.youtube.com/watch?v=xxx" -o lecture_notes.pdf --subs-from-yt zh-TW
```

### 3. 使用本地影片檔案生成講義
```bash
python3 -m src.main -i "path/to/lecture.mp4" -o output_notes.pdf -m medium -l zh
```

> [!NOTE]  
> 執行完畢後，講義與同名 `.srt` 字幕檔案預設會自動安全存放在專案的 `outputs/` 目錄中，保持根目錄的整潔。

---

## 🎛️ CLI 參數說明

| 參數短寫 | 參數長寫 | 預設值 | 說明 |
| :--- | :--- | :--- | :--- |
| `-u` | `--url` | *None* | YouTube 課程影片的 URL（與 `-i` 互斥，兩者必填其一） |
| `-i` | `--input` | *None* | 本地影片的檔案路徑（與 `-u` 互斥，兩者必填其一） |
| *無* | `--list-subs` | *None* | 查詢並列出 YouTube 影片上所有可下載的手動與自動生成字幕列表，隨後立即退出（僅適用於 `-u/--url`）。 |
| `-o` | `--output` | `outputs/lecture_notes.pdf` | 生成的 PDF 講義路徑（同名 `.srt` 字幕亦會隨之輸出，若目錄不存在會自動為您建立） |
| `-m` | `--model` | `medium` | `faster-whisper` 的模型大小（支援 `tiny`, `base`, `small`, `medium`, `large-v3`） |
| `-l` | `--lang` | `zh` | 語音轉譯的語系代碼（預設 `zh` 會自動帶入繁體中文優化 prompt） |
| `-t` | `--threshold`| `auto` | 投影片切換偵測的 MAE 敏感度閾值（浮點數，或設為 `"auto"` 以透過 MAD 統計演算法自動計算最優動態閾值） |
| `-d` | `--device` | `cpu` | 計算推理硬體載體（`cpu` 或 `cuda`） |
| *無* | `--subs-from-yt` | *None* | 直接從 YouTube 下載指定的字幕語言（例如 `zh-TW`）並跳過本地 Whisper 轉譯。若該影片無此字幕則會報錯並終止。 |
| *無* | `--max-res` | `720` | 限制下載 YouTube 影片的最大高度解析度（例如 `480`, `720`, `1080`），有效縮短下載時間及提升 OpenCV 影格處理效率。 |
| *無* | `--time-range` | *None* | 指定要下載與處理的影片時間區段，格式為 `HH:MM:SS-HH:MM:SS`（例如 `00:10:00-00:20:30`）。 |
| *無* | `--srt` | *None* | 指定本地 `.srt` 或 `.vtt` 字幕檔案路徑，完全跳過 Whisper 語音轉譯與 YouTube 字幕下載流程。 |
| *無* | `--min-duration` | `1.0` | 兩次投影片切換之間的最小冷卻秒數（越低越能捕捉快速切換的投影片）。 |
| *無* | `--slide-mode` | `final` | 投影片動畫擷取策略（`final` 只保留最終動畫完成版、`all` 擷取所有步驟、`first` 只保留初始無動畫版） |



---

## 📂 專案目錄結構

```text
video-to-ai-friendly-notes/
├── LICENSE             # MIT 授權條款
├── requirements.txt    # 專案依賴描述
├── inputs/             # 存放下載完成的影片
├── outputs/            # 智慧分流專案產出
│   ├── pdf/            # 存放生成的 PDF 講義
│   ├── subtitles/      # 存放輸出的 .srt 字幕
│   └── slides/         # 依名稱分流存放投影片 JPEG 影格
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

本專案擁有 100% 覆蓋核心 API 的測試套件（共計 25 個測試案例）。執行測試完全不消耗外部網路流量、不讀寫真實影片，保證 CI-safe：

```bash
PYTHONPATH=. ./venv/bin/pytest -v
```

**期望輸出**：
```text
============================== 25 passed in 1.94s ==============================
```

---

## 📄 授權條款

本專案採用 [MIT License](LICENSE) 授權條款開源發布。
