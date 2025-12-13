# PaddleOCR Toolkit

[![CI](https://github.com/danwin47-sys/paddleocr-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/danwin47-sys/paddleocr-toolkit/actions/workflows/ci.yml)

🔍 **多功能 OCR 文件辨識與處理工具**

基於 [PaddleOCR 3.x](https://github.com/PaddlePaddle/PaddleOCR) 開發的命令列工具與 Python 套件，支援多種 OCR 模式和輸出格式。

---

## ✨ 功能特色

| 功能 | 說明 |
|------|------|
| 📄 可搜尋 PDF | 在原始 PDF 上疊加透明文字層，可選取、搜尋 |
| 📝 多種輸出格式 | 純文字、Markdown、JSON、HTML、Excel、LaTeX |
| 🔀 混合模式 | PP-StructureV3 版面分析 + PP-OCRv5 精確座標 |
| 🌐 PDF 翻譯 | 使用 Ollama 本地模型翻譯，支援雙語輸出 |
| 🔧 文字修正 | 自動修復 OCR 空格和格式問題 |
| 📊 進度條 | 處理多頁 PDF 時顯示進度 |
| 🔄 方向校正 | 自動旋轉傾斜文件 |
| ⚙️ 設定檔支援 | 支援 YAML 設定檔，簡化參數輸入 |
| 🛠️ 批次處理 | 支援多執行緒批次處理圖片 |

---

## 🚀 安裝

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 首次執行

首次執行時會自動下載 PaddleOCR 模型（約 100MB），之後會使用本機快取。

---

## 📖 使用方式

### 方法一：命令列工具（CLI）

```bash
# 基本使用
python paddle_ocr_tool.py input.pdf

# 或使用套件模組
python -m paddleocr_toolkit input.pdf
```

### 方法二：Python 套件

```python
from paddleocr_toolkit import PaddleOCRTool, OCRResult, PDFGenerator
from paddleocr_toolkit.processors import fix_english_spacing, detect_pdf_quality
from paddleocr_toolkit.core import load_config

# 初始化 OCR 工具
tool = PaddleOCRTool(mode="hybrid")

# 處理 PDF
result = tool.process_hybrid("input.pdf")
print(result['text_content'])
```

---

## ⚙️ 設定檔使用

本工具支援 `config.yaml` 設定檔，可避免每次輸入冗長的命令列參數。

### 1. 建立設定檔

複製 `config.yaml` 到專案根目錄或使用者家目錄：

```yaml
# config.yaml 範例
ocr:
  mode: "hybrid"
  lang: "ch"
  use_gpu: false
  det_db_thresh: 0.3

output:
  dir: "output"
  formats:
    - "pdf"
    - "markdown"
    - "json"
  searchable_pdf: true

pdf:
  dpi: 300
  auto_rotate: true
  quality_check: true

translate:
  enabled: false
  source_lang: "auto"
  target_lang: "en"
  ollama_model: "qwen2.5:7b"
```

### 2. 載入順序

工具會依序尋找並載入設定檔（後者覆蓋前者）：

1. 預設設定
2. 使用者家目錄 `~/.paddleocr_toolkit/config.yaml`
3. 當前目錄 `config.yaml`
4. 命令列參數 `--config path/to/config.yaml`
5. 其他命令列參數（優先級最高）

---

## 🎯 OCR 模式

| 模式 | 說明 | 使用場景 |
|------|------|----------|
| `basic` | PP-OCRv5 基本文字識別 | 一般文件、書籍 |
| `structure` | PP-StructureV3 結構化解析 | 表格、複雜排版 |
| `hybrid` | 版面分析 + 精確 OCR（推薦） | 生成可搜尋 PDF + Markdown |
| `vl` | PaddleOCR-VL 視覺語言模型 | 複雜文件理解 |
| `formula` | PP-FormulaNet 公式識別 | 數學公式、學術論文 |

---

## 📋 命令列參數詳解

### 基本參數

 | 參數 | 說明 | 範例 |
 |------|------|------|
 | `input` | 輸入檔案或目錄 | `input.pdf` |
 | `--config`, `-c` | 指定設定檔路徑 | `--config my_config.yaml` |
 | `--mode`, `-m` | OCR 模式 | `--mode hybrid` |
 | `--output`, `-o` | 輸出路徑 | `--output result.pdf` |

### 輸出格式

| 參數 | 說明 | 適用模式 |
|------|------|----------|
| `--searchable`, `-s` | 生成可搜尋 PDF | basic |
| `--text-output`, `-t` | 純文字輸出 | basic |
| `--markdown-output` | Markdown 輸出 | structure, hybrid |
| `--json-output` | JSON 輸出（含座標） | structure, hybrid |
| `--html-output` | HTML 輸出 | structure, hybrid |
| `--excel-output` | Excel 表格輸出 | structure |
| `--latex-output` | LaTeX 公式輸出 | formula |
| `--all` | 同時輸出所有格式 | structure, hybrid |

### 文件校正

| 參數 | 說明 |
|------|------|
| `--orientation-classify` | 自動校正文件方向 |
| `--unwarping` | 校正彎曲文件 |
| `--textline-orientation` | 文字行方向偵測 |

### 翻譯功能（需要 Ollama）

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `--translate` | 啟用翻譯 | - |
| `--source-lang` | 來源語言 | `auto` |
| `--target-lang` | 目標語言 | `en` |
| `--ollama-model` | Ollama 模型 | `qwen2.5:7b` |
| `--ollama-url` | Ollama API URL | `http://localhost:11434` |
| `--dual-mode` | 雙語模式 | `alternating` |

### 其他選項

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `--dpi` | PDF 轉圖片解析度 | 150（掃描件自動調至 300） |
| `--device` | 運算設備 | `cpu` |
| `--recursive`, `-r` | 遞迴處理子目錄 | - |
| `--debug-text` | 顯示粉紅色文字層（除錯） | - |
| `--no-progress` | 停用進度條 | - |

---

## 💡 使用範例

### 基本用法

```bash
# 基本 OCR（輸出文字 + 可搜尋 PDF）
python paddle_ocr_tool.py document.pdf

# 使用設定檔
python paddle_ocr_tool.py document.pdf --config config.yaml
```

### 混合模式（推薦）

```bash
# 生成可搜尋 PDF + Markdown
python paddle_ocr_tool.py document.pdf --mode hybrid

# 輸出所有格式（Markdown + JSON + HTML）
python paddle_ocr_tool.py document.pdf --mode hybrid --all

# 自訂輸出
python paddle_ocr_tool.py document.pdf --mode hybrid \
    --markdown-output result.md \
    --json-output result.json \
    --html-output result.html
```

### 結構化模式

```bash
# Markdown + Excel 表格輸出
python paddle_ocr_tool.py document.pdf --mode structure \
    --markdown-output result.md \
    --excel-output tables.xlsx

# 輸出所有格式
python paddle_ocr_tool.py document.pdf --mode structure --all
```

### 公式識別

```bash
# 識別數學公式並輸出 LaTeX
python paddle_ocr_tool.py formula.png --mode formula --latex-output formulas.tex
```

### 翻譯功能

```bash
# 翻譯 PDF（繁體中文 → 英文）
python paddle_ocr_tool.py document.pdf --mode hybrid \
    --translate \
    --source-lang zh-tw \
    --target-lang en

# 使用特定 Ollama 模型
python paddle_ocr_tool.py document.pdf --mode hybrid \
    --translate \
    --ollama-model llama3:8b

# 生成雙語 PDF（並排顯示）
python paddle_ocr_tool.py document.pdf --mode hybrid \
    --translate \
    --dual-mode side-by-side
```

### 批次處理

```bash
# 處理整個目錄
python paddle_ocr_tool.py ./documents/ --mode hybrid

# 遞迴處理子目錄
python paddle_ocr_tool.py ./documents/ --mode hybrid --recursive
```

### 除錯模式

```bash
# 顯示粉紅色文字層（檢查座標是否正確）
python paddle_ocr_tool.py document.pdf --mode hybrid --debug-text
```

---

## 📦 套件結構

```
paddleocr-toolkit/
├── paddle_ocr_tool.py           # 主程式（CLI 入口）
├── pdf_translator.py            # 翻譯模組
├── config.yaml                  # 設定檔範本
├── paddleocr_toolkit/           # Python 套件
│   ├── __init__.py              # 套件入口
│   ├── __main__.py              # CLI 入口（python -m）
│   ├── core/
│   │   ├── models.py            # 資料模型
│   │   ├── pdf_generator.py     # PDF 生成器
│   │   ├── pdf_utils.py         # PDF 工具函數
│   │   └── config_loader.py     # 設定檔載入器
│   ├── processors/
│   │   ├── text_processor.py    # 文字處理
│   │   ├── pdf_quality.py       # PDF 品質偵測
│   │   ├── batch_processor.py   # 批次處理
│   │   ├── image_preprocessor.py# 影像前處理
│   │   ├── glossary_manager.py  # 術語管理
│   │   ├── ocr_workaround.py    # OCR 替代方案
│   │   └── stats_collector.py   # 統計收集
│   └── outputs/                 # 輸出格式處理
├── requirements.txt             # Python 依賴
├── glossary.csv                 # 翻譯術語表
└── README.md                    # 說明文件
```

---

## 🐍 Python API

### 匯入方式

```python
# 主要類別
from paddleocr_toolkit import PaddleOCRTool, OCRResult, PDFGenerator

# 處理器
from paddleocr_toolkit.processors import (
    fix_english_spacing,
    detect_pdf_quality,
    BatchProcessor
)

# 核心模組
from paddleocr_toolkit.core import (
    OCRMode,
    load_config,
    pdf_utils
)
```

### OCRResult 類別

```python
@dataclass
class OCRResult:
    text: str                     # 識別的文字
    confidence: float             # 信賴度 (0-1)
    bbox: List[List[float]]       # 邊界框座標
    
    @property
    def x(self) -> float          # 左上角 X 座標
    def y(self) -> float          # 左上角 Y 座標
    def width(self) -> float      # 邊界框寬度
    def height(self) -> float     # 邊界框高度
```

### PDFGenerator 類別

```python
from paddleocr_toolkit import PDFGenerator, OCRResult

# 建立 PDF 生成器
generator = PDFGenerator("output.pdf", debug_mode=False)

# 新增頁面
generator.add_page("page1.png", ocr_results)
generator.add_page_from_pixmap(pixmap, ocr_results)

# 儲存
generator.save()
```

### 設定檔載入

```python
from paddleocr_toolkit.core import load_config

# 載入設定
config = load_config("config.yaml")
print(config['ocr']['mode'])
```

### 文字處理

```python
from paddleocr_toolkit.processors import fix_english_spacing

# 修復 OCR 空格問題
text = "FoundryServiceisdesigned"
fixed = fix_english_spacing(text)
print(fixed)  # "Foundry Service is designed"
```

### PDF 品質偵測

```python
from paddleocr_toolkit.processors import detect_pdf_quality

quality = detect_pdf_quality("document.pdf")
print(quality)
# {
#     'is_scanned': True,
#     'is_blurry': False,
#     'has_text': False,
#     'recommended_dpi': 300,
#     'reason': '偵測為掃描件...'
# }
```

---

## 🔧 系統需求

- Python 3.8+
- CUDA 11.x（使用 GPU 加速，可選）
- 約 2GB 磁碟空間（模型檔案）

---

## 📝 輸出檔案說明

使用 `--mode hybrid` 時會產生以下檔案：

| 檔案 | 說明 |
|------|------|
| `*_hybrid.pdf` | 原文可搜尋 PDF（透明文字層） |
| `*_hybrid.md` | Markdown 格式輸出 |
| `*_hybrid.json` | JSON 格式（含座標資訊） |
| `*_hybrid.html` | HTML 格式（可瀏覽） |
| `*_erased.pdf` | 文字擦除版（用於翻譯） |

使用 `--translate` 時額外產生：

| 檔案 | 說明 |
|------|------|
| `*_translated_{lang}.pdf` | 翻譯版 PDF |
| `*_bilingual_{lang}.pdf` | 雙語版 PDF |

---

## 📜 License

MIT License

## 🙏 致謝

- [PaddlePaddle](https://github.com/PaddlePaddle/Paddle) - 百度深度學習框架
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - 多語言 OCR 工具
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF 處理庫
- [Ollama](https://ollama.ai/) - 本地 LLM 執行環境
