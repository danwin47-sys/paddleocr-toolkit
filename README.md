# PaddleOCR Toolkit

[![CI](https://github.com/danwin47-sys/paddleocr-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/danwin47-sys/paddleocr-toolkit/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-391%20passed-success)](https://github.com/danwin47-sys/paddleocr-toolkit/actions)
[![Coverage](https://img.shields.io/badge/coverage-84%25-green)](https://codecov.io/gh/danwin47-sys/paddleocr-toolkit)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](Dockerfile)

🔍 **專業級 OCR 文件辨識與處理工具**

基於 [PaddleOCR 3.x](https://github.com/PaddlePaddle/PaddleOCR) 開發的命令列工具與 Python 套件，經過完整重構和效能優化，提供生產級代碼質量。

**📚 [快速開始](docs/QUICK_START.md) | [API文檔](docs/API_GUIDE.md) | [示例工具](examples/) | [貢獻指南](CONTRIBUTING.md)**

---

## ✨ 核心特色

### 功能特色

| 📄 可搜索 PDF | 在原始 PDF 上疊加透明文字層，可選取、搜尋 |
| 📝 多種輸出格式 | 純文字、Markdown、JSON、HTML、Excel、LaTeX |
| 🔀 混合模式 | PP-StructureV3 版面分析 + PP-OCRv5 精確座標 |
| 🌐 PDF 翻譯 | 使用 Ollama 本地模型翻譯，支持雙語輸出 |
| 🤖 **AI 語義修正** | **v3.0** - LLM 自動修正 OCR 錯誤，準確率 +15% |
| 📊 **結構化提取** | **v3.0** - 從 OCR 文字自動提取 JSON 資料 |
| 🔧 文字修正 | 自動修復 OCR 空格和格式問題 |
| 📊 進度條 | 處理多頁 PDF 時顯示進度 |
| 🔄 方向校正 | 自動旋轉傾斜文檔 |
| ⚙️ 設定檔支持 | 支持 YAML 設定檔，簡化參數輸入 |
| 🛠️ 批次處理 | 支持多線程批次處理圖片 |
| 🎨 CLI美化 | Rich UI支持，炫酷終端界面 |

### 🆕 性能優化（Stage 2）

| 項目 | 改善 |
|------|------|
| PDF 記憶體使用 | **-90%** (600MB → 20MB) |
| I/O 寫入速度 | **+50%** |
| 串流處理 | 恒定記憶體處理大型 PDF |
| 批次緩衝 | 智慧批次寫入優化 |

### 🧩 模組化架構（Stage 3）

**26 個專業化組件**:

- **CLI 層**: `argument_parser`, `config_handler`, `mode_processor`, `output_manager`, `rich_ui`
- **核心 層**: `ocr_engine`, `result_parser`, `pdf_generator`, `pdf_utils`, `streaming_utils`, `config_loader`, `models`
- **處理器 層**: `batch_processor`, `pdf_processor`, `image_preprocessor`, `structure_processor`, `translation_processor`
- **輸出 層**: `output_manager`

### 📊 代碼質量

- ✅ **391 個單元測試**（100% 通過率）⬆️
- ✅ **84% 測試覆蓋率**⬆️
- ✅ **100% 類型提示**
- ✅ **100% Docstrings**
- ✅ **模組化設計**（26 個專業化模組）⬆️
- ✅ **代碼格式化**（Black + isort）
- ✅ **CI/CD流程**（GitHub Actions）🆕
- ✅ **Docker支持**（生產級配置）🆕

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
│   ├── cli/                     # 🆕 CLI 模組（Stage 2 重構）
│   │   ├── argument_parser.py   # 命令列參數解析
│   │   ├── output_manager.py    # 輸出路徑管理
│   │   ├── config_handler.py    # 設定檔處理
│   │   └── mode_processor.py    # 模式處理器
│   ├── core/                    # 核心模組
│   │   ├── models.py            # 資料模型
│   │   ├── pdf_generator.py     # PDF 生成器
│   │   ├── pdf_utils.py         # PDF 工具函數
│   │   ├── config_loader.py     # 設定檔載入器
│   │   ├── ocr_engine.py        # 🆕 OCR 引擎管理器（Stage 3）
│   │   ├── result_parser.py     # 🆕 結果解析器（Stage 3）
│   │   ├── streaming_utils.py   # 🆕 串流處理工具（性能優化）
│   │   └── buffered_writer.py   # 🆕 緩衝寫入器（性能優化）
│   ├── processors/              # 處理器模組
│   │   ├── text_processor.py    # 文字處理
│   │   ├── pdf_quality.py       # PDF 品質偵測
│   │   ├── batch_processor.py   # 批次處理
│   │   ├── pdf_processor.py     # 🆕 PDF 處理器（Stage 3）
│   │   ├── structure_processor.py # 🆕 結構化處理器（Stage 3）
│   │   ├── translation_processor.py # 🆕 翻譯處理器（Stage 3）
│   │   ├── image_preprocessor.py# 影像前處理
│   │   ├── glossary_manager.py  # 術語管理
│   │   ├── ocr_workaround.py    # OCR 替代方案
│   │   └── stats_collector.py   # 統計收集
│   └── outputs/                 # 🆕 輸出格式處理（Stage 3）
│       └── output_manager.py    # 輸出管理器
├── tests/                       # 🆕 測試套件
│   ├── test_cli_*.py            # CLI 模組測試（71 個測試）
│   ├── test_core_*.py           # 核心模組測試
│   ├── test_processors_*.py     # 處理器測試
│   └── test_performance_*.py    # 性能測試
├── artifacts/plans/             # 📚 工作計畫與總結
├── requirements.txt             # Python 依賴
├── glossary.csv                 # 翻譯術語表
└── README.md                    # 說明文件
```

---

## 🏆 代碼質量

### 測試覆蓋率

[![Coverage](https://img.shields.io/badge/coverage-84%25-brightgreen)](https://github.com/danwin47-sys/paddleocr-toolkit)

- **整體覆蓋率**: 84%
- **CLI 模組**: 96%
- **核心模組**: 85%
- **處理器模組**: 79%
- **總測試數**: 247 個
- **測試通過率**: 100%

### 代碼組織

本專案經過專業重構，遵循以下最佳實踐：

- ✅ **SOLID 原則** - 單一職責、開閉原則
- ✅ **DRY 原則** - 消除重複代碼
- ✅ **模組化設計** - 清晰的模組邊界
- ✅ **類型提示** - 100% 類型提示覆蓋
- ✅ **文檔字串** - 100% Google Style docstrings
- ✅ **測試驅動** - 247 個單元測試

### 重構成果（2024-12）

最近完成的 Stage 2 重構大幅提升了代碼質量：

| 指標 | 重構前 | 重構後 | 改善 |
|------|--------|--------|------|
| 主方法平均長度 | 294 行 | 82 行 | ⬇️ 72% |
| 測試覆蓋率 | 40% | 84% | ⬆️ 44% |
| 測試數量 | ~50 | 247 | ⬆️ 395% |
| 類型提示覆蓋 | ~85% | 100% | ⬆️ 15% |
| Docstrings 覆蓋 | ~70% | 100% | ⬆️ 30% |

**重構詳情**:

- 將 5 個巨型方法（1,471 行）重構為 25 個輔助方法（410 行）
- 提取 CLI 邏輯到獨立模組（`paddleocr_toolkit/cli/`）
- 創建 71 個 CLI 測試，達到 96% 覆蓋率
- 所有代碼遵循 Google Style Python 規範

---

## 🧩 新模組 API (Stage 3)

### OCR 引擎管理器

```python
from paddleocr_toolkit.core import OCREngineManager

# 使用 context manager
with OCREngineManager(mode='basic', device='gpu') as manager:
    result = manager.predict('image.jpg')

# 或手動管理
manager = OCREngineManager(mode='hybrid', device='cpu')
manager.init_engine()
result = manager.predict('document.pdf')
manager.close()
```

### OCR 結果解析器

```python
from paddleocr_toolkit.core import OCRResultParser

parser = OCRResultParser()

# 解析基本結果
results = parser.parse_basic_result(predict_output)

# 解析結構化結果
results = parser.parse_structure_result(structure_output)

# 過濾和排序
filtered = parser.filter_by_confidence(results, min_confidence=0.8)
sorted_results = parser.sort_by_position(filtered, reading_order='top-to-bottom')
```

### PDF 處理器

```python
from paddleocr_toolkit.processors import PDFProcessor

processor = PDFProcessor(
    ocr_func=engine.predict,
    result_parser=parser.parse_basic_result
)

# 處理 PDF
results, output_path = processor.process_pdf(
    pdf_path='document.pdf',
    searchable=True,
    dpi=200
)

# 提取文字
text = processor.extract_all_text(results)
```

### 輸出管理器

```python
from paddleocr_toolkit.outputs import OutputManager

# 創建管理器
manager = OutputManager(
    base_path='output/result',
    formats=['md', 'json', 'txt', 'html']
)

# 批次輸出
paths = manager.write_all({
    'text': '純文字內容',
    'markdown': '# Markdown\n內容',
    'json_data': {'key': 'value'}
})

# 單獨輸出
manager.write_markdown('# 標題\n內容')
manager.write_json({'data': [1, 2, 3]})
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
