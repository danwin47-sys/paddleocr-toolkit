# PaddleOCR Toolkit

[![CI](https://github.com/danwin47-sys/paddleocr-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/danwin47-sys/paddleocr-toolkit/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-581%20passed-success)](https://github.com/danwin47-sys/paddleocr-toolkit/actions)
[![Coverage](https://img.shields.io/badge/coverage-84%25-green)](https://codecov.io/gh/danwin47-sys/paddleocr-toolkit)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](Dockerfile)

🔍 **專業級 OCR 文件辨識與處理工具**

基於 [PaddleOCR 3.x](https://github.com/PaddlePaddle/PaddleOCR) 開發的命令列工具與 Python 套件，能將 PDF/圖片轉為可搜尋 PDF、Markdown 或 JSON。
本專案已完成企業級重構，提供高覆蓋率測試與模組化架構。

**📚 [快速開始](docs/QUICK_START.md) | [API文檔](docs/API_GUIDE.md) | [插件範例](custom/) | [貢獻指南](CONTRIBUTING.md)**

---

## ✨ 核心特色

### 🚀 企業級功能
- **混合模式 (Hybrid Mode)**: 結合版面分析與精確 OCR，生成幾乎完美的 Markdown/JSON。
- **多語言支持 (i18n)**: 內建繁體中文 (`zh_TW`) 與英文介面。
- **插件系統 (Plugins)**: 支援自定義前處理/後處理邏輯（如個資遮蔽、浮水印去除）。
- **並行處理**: 多核心 CPU 並行加速大型 PDF 處理。
- **雙 AI 校正**: 整合 Gemini/Claude LLM 進行語義錯誤修正。

### 🛠️ 工具集
- **CLI**: 功能強大的命令列介面，支援豐富參數與 Rich UI。
- **Web Dashboard**: 現代化 Glassmorphism 介面，支援批次拖放與預覽。
- **Python SDK**: 簡潔的 Facade API，易於整合至其他專案。

### 📊 代碼質量
- ✅ **581 個單元測試**（100% 通過率）
- ✅ **84% 測試覆蓋率**
- ✅ **100% 類型提示** (Type Hints)
- ✅ **模組化設計** (Core/Processors/CLI 分層架構)

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
# 基本使用 (生成可搜尋 PDF)
python paddle_ocr_tool.py input.pdf

# 混合模式 (推薦，生成 Markdown + PDF)
python paddle_ocr_tool.py input.pdf --mode hybrid

# 啟用 Web 儀表板
python -m paddleocr_toolkit.api.main
```

### 方法二：Python API (Facade)

```python
from paddle_ocr_facade import PaddleOCRFacade

# 初始化
tool = PaddleOCRFacade(mode="hybrid", enable_semantic=True)

# 執行 OCR
result = tool.process("document.pdf")

# 取得結果
print(f"辨識文字: {len(result['text_content'])} 字")
print(f"輸出檔案: {result['output_files']}")
```

---

## 🧩 插件系統 (Plugins)

本專案支援強大的插件擴充。範例位於 `custom/` 目錄：

- **PII Masking**: 自動遮蔽身分證、手機號、Email。
- **Watermark Remover**: 去除文件浮水印以提升 OCR 精度。
- **Doc Classifier**: 自動分類文件類型（發票/合約）。

啟用方式：
將插件放入 `custom/` 並在設定檔中啟用，或程式化載入。

---

## ⚙️ 設定檔

支援 `config.yaml` 與 `i18n` 設定：

```yaml
ocr:
  mode: "hybrid"
  lang: "ch"
  
system:
  language: "zh_TW"  # 介面語言
  device: "cpu"      # cpu 或 gpu
```

---

## 📦 專案結構

```
paddleocr-toolkit/
├── paddle_ocr_tool.py      # CLI 入口 Shim
├── paddle_ocr_facade.py    # Facade API 入口
├── paddleocr_toolkit/      # 核心套件
│   ├── core/               # 核心 (Engine, Config, Logging)
│   ├── processors/         # 處理器 (PDF, Image, Text, Batch)
│   ├── cli/                # 命令列介面
│   ├── api/                # Web API (FastAPI)
│   ├── i18n/               # 國際化資源
│   └── plugins/            # 插件基類
├── custom/                 # 使用者自訂插件
├── tests/                  # 測試套件
└── docs/                   # 完整文件
```

---

## 📜 License

MIT License
