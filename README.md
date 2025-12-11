# PaddleOCR Toolkit

🔍 **多功能 OCR 文件辨識與處理工具**

基於 [PaddleOCR 3.x](https://github.com/PaddlePaddle/PaddleOCR) 開發的命令列工具，支援多種 OCR 模式和輸出格式。

## ✨ 功能特色

| 功能 | 說明 |
|------|------|
| 📄 可搜尋 PDF | 在原始 PDF 上疊加透明文字層，可選取、搜尋 |
| 📝 文字輸出 | 提取純文字並儲存 |
| 📊 Markdown/JSON | PP-StructureV3 結構化文件解析 |
| 📈 Excel 輸出 | 表格識別並輸出 `.xlsx` |
| 📐 LaTeX 輸出 | 數學公式識別並輸出 LaTeX |
| 📊 進度條 | 處理多頁 PDF 時顯示進度 |
| 🔄 方向校正 | 自動旋轉傾斜文件 |

## 🚀 安裝

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 首次執行

首次執行時會自動下載 PaddleOCR 模型（約 100MB），之後會使用本機快取。

## 📖 使用方式

### 基本 OCR（文字輸出 + 可搜尋 PDF）

```bash
python paddle_ocr_tool.py input.pdf
```

預設會輸出：

- `input_ocr.txt` - 識別的文字
- `input_searchable.pdf` - 可搜尋的 PDF

### OCR 模式

| 模式 | 說明 | 使用場景 |
|------|------|----------|
| `basic` | PP-OCRv5 基本文字識別 | 一般文件、書籍 |
| `structure` | PP-StructureV3 結構化解析 | 表格、複雜排版 |
| `vl` | PaddleOCR-VL 視覺語言模型 | 複雜文件理解 |
| `formula` | PP-FormulaNet 公式識別 | 數學公式、學術論文 |

### 使用範例

```bash
# 基本 OCR（預設）
python paddle_ocr_tool.py document.pdf

# 生成可搜尋 PDF
python paddle_ocr_tool.py document.pdf --searchable

# 結構化模式（Markdown + Excel）
python paddle_ocr_tool.py document.pdf --mode structure --excel-output tables.xlsx

# 公式識別（LaTeX 輸出）
python paddle_ocr_tool.py formula.png --mode formula --latex-output result.tex

# 啟用文件方向校正
python paddle_ocr_tool.py document.pdf --orientation-classify

# 停用進度條
python paddle_ocr_tool.py document.pdf --no-progress

# 使用 CPU（無 GPU 環境）
python paddle_ocr_tool.py document.pdf --device cpu
```

## 📋 命令列參數

### 必要參數

| 參數 | 說明 |
|------|------|
| `input` | 輸入檔案或目錄路徑 |

### OCR 模式

| 參數 | 說明 |
|------|------|
| `--mode`, `-m` | OCR 模式：`basic`, `structure`, `vl`, `formula` |

### 輸出選項

| 參數 | 說明 |
|------|------|
| `--searchable`, `-s` | 生成可搜尋 PDF（basic 模式）|
| `--text-output`, `-t` | 文字輸出路徑 |
| `--markdown-output` | Markdown 輸出（structure/vl 模式）|
| `--json-output` | JSON 輸出（structure/vl 模式）|
| `--excel-output` | Excel 輸出（structure 模式）|
| `--latex-output` | LaTeX 輸出（formula 模式）|

### 文件校正

| 參數 | 說明 |
|------|------|
| `--orientation-classify` | 自動校正文件方向 |
| `--unwarping` | 校正彎曲文件 |
| `--textline-orientation` | 文字行方向偵測 |

### 其他選項

| 參數 | 說明 |
|------|------|
| `--dpi` | PDF 轉圖片解析度（預設：150）|
| `--device` | 運算設備：`gpu` 或 `cpu` |
| `--no-progress` | 停用進度條 |
| `--recursive`, `-r` | 遞迴處理子目錄 |

## 📁 專案結構

```
paddleocr-toolkit/
├── paddle_ocr_tool.py    # 主程式
├── requirements.txt      # Python 依賴
├── README.md             # 說明文件
└── .gitignore            # Git 忽略規則
```

## 🔧 系統需求

- Python 3.8+
- CUDA 11.x（使用 GPU 加速，可選）
- 約 2GB 磁碟空間（模型檔案）

## 📝 License

MIT License

## 🙏 致謝

- [PaddlePaddle](https://github.com/PaddlePaddle/Paddle) - 百度深度學習框架
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - 多語言 OCR 工具
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF 處理庫
