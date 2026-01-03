# PaddleOCR Toolkit 使用者手冊

本手冊提供 PaddleOCR Toolkit 的詳細使用說明，涵蓋安裝、CLI 命令、配置設定與進階功能。

## 📋 目錄

1.  [⚡ 快速開始](#-快速開始)
2.  [📦 安裝指南](#-安裝指南)
3.  [💻 命令列工具 (CLI)](#-命令列工具-cli)
4.  [⚙️ 配置設定](#-配置設定)
5.  [🧠 LLM 整合 (AI 校正)](#-llm-整合-ai-校正)
6.  [🌐 Web 儀表板](#-web-儀表板)

---

## ⚡ 快速開始

### 1. 安裝套件
```bash
pip install -r requirements.txt
```

### 2. 生成可搜尋 PDF (基本模式)
```bash
python paddle_ocr_tool.py input.pdf
```

### 3. 使用混合模式 (表格識別 + Markdown 輸出)
```bash
python paddle_ocr_tool.py input.pdf --mode hybrid
```

---

## 📦 安裝指南

### 系統需求
- Python 3.8+
- RAM: 建議 4GB+ (若啟用 LLM 或處理大型 PDF)
- (可選) NVIDIA GPU + CUDA 用於加速 OCR

### 本地安裝 (MacOS/Linux/Windows)

```bash
# 1. Clone 專案
git clone https://github.com/danwin47-sys/paddleocr-toolkit.git
cd paddleocr-toolkit

# 2. 建立虛擬環境 (推薦)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安裝依賴
pip install -r requirements.txt
```

### Docker 安裝 (尚未發布)
*(即將推出)*

---

## 💻 命令列工具 (CLI)

主要的進入點是 `paddle_ocr_tool.py`。

### 基本語法
```bash
python paddle_ocr_tool.py [INPUT_PATH] [OPTIONS]
```

### 核心模式 (`--mode`)
| 模式        | 描述                          | 適用場景                          |
| :---------- | :---------------------------- | :-------------------------------- |
| `basic`     | 基礎 OCR，僅提取文字          | 快速提取純文字，無需格式          |
| `hybrid`    | **(推薦)** 結合版面分析與 OCR | 表格、多欄排版文件，生成 Markdown |
| `structure` | 專注於結構化提取              | 複雜表格與文件結構還原            |

### 常用參數

#### 輸入與輸出
- `--output <DIR>`: 指定輸出目錄 (預設: 當前目錄)
- `--recursive`: 遞歸處理目錄下的所有檔案
- `--overwrite`: 強制覆蓋已存在的輸出檔案

#### 影像處理
- `--dpi <INT>`: 處理 PDF 時的解析度 (預設: 150，建議: 200-300 以提升準確度)
- `--deskew`: 啟用影像歪斜校正
- `--unwarp`: 啟用影像去彎曲 (適用於相片掃描件)

#### 進階功能
- `--translate`: 啟用翻譯功能 (需配置 LLM)
- `--source_lang <LANG>`: 翻譯來源語言 (預設: auto)
- `--target_lang <LANG>`: 翻譯目標語言 (預設: en)
- `--enable_semantic`: 啟用語義檢查修正 (需配置 LLM)

### 範例

**批次處理目錄並啟用高解析度：**
```bash
python paddle_ocr_tool.py ./documents --output ./results --recursive --dpi 300
```

**驗證 OCR 準確度 (Validate 命令)：**
```bash
python -m paddleocr_toolkit.cli.commands.validate <OCR_JSON> <GROUND_TRUTH_TXT>
```

**運行效能基準測試 (Benchmark 命令)：**
```bash
python -m paddleocr_toolkit.cli.commands.benchmark input.pdf
```

---

## ⚙️ 配置設定

系統會在以下路徑依序尋找 `config.yaml`：
1. 當前工作目錄
2. `~/.paddleocr_toolkit/`

### 範例 `config.yaml`

```yaml
ocr:
  mode: "hybrid"
  device: "cpu"       # "cpu" 或 "gpu"
  dpi: 150
  use_angle_cls: true # 啟用方向分類器

output:
  searchable_pdf: true
  markdown: true
  json: true

translation:
  enabled: false
  provider: "ollama"  # "ollama", "openai", "gemini", "claude"
  ollama_url: "http://localhost:11434"
  ollama_model: "qwen2.5:7b"
  
logging:
  level: "INFO"
  save_to_file: true
```

---

## 🧠 LLM 整合 (AI 校正)

PaddleOCR Toolkit 支援整合大型語言模型 (LLM) 進行 OCR 結果的後處理，例如語義修正與翻譯。

### 支援的提供商
1. **Ollama (本地)**: 免費、隱私高，需安裝 [Ollama](https://ollama.com)。
2. **OpenAI**: 使用 GPT-3.5/4。
3. **Google Gemini**: 使用 Gemini Pro/Flash。
4. **Anthropic Claude**: 使用 Claude 3/3.5。

### 啟用方式 (以 Ollama 為例)

1. 啟動 Ollama 服務：
   ```bash
   ollama serve
   ollama pull qwen2.5:7b
   ```

2. 執行 CLI 時帶上參數：
   ```bash
   python paddle_ocr_tool.py doc.pdf --enable_semantic \
     --llm_provider ollama \
     --ollama_model qwen2.5:7b
   ```

---

## 🌐 Web 儀表板

內建的 Web 介面提供可視化的任務管理與系統監控。

### 啟動服務
```bash
python -m paddleocr_toolkit.api.main
```
服務預設運行於 `http://localhost:8000`。

### 主要功能
- **任務上傳**: 拖放檔案進行 OCR。
- **即時日誌**: 透過 WebSocket 查看處理進度。
- **系統健康**: `/health` 端點監控 CPU/RAM 使用量。
- **API 文件**: 瀏覽器訪問 `/docs` 查看 Swagger UI。
