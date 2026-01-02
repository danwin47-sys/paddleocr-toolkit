# PaddleOCR Toolkit

> [!IMPORTANT]
> **本地啟動必讀**：如果您要配合 Vercel 前端使用，請務必先閱讀 [**BACKEND_GUIDE.md**](./BACKEND_GUIDE.md) 來啟動本地 OCR 服務。

---

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
- **混合模式 (Hybrid Mode)**: 結合版面分析與精確 OCR，支援表格識別與複雜文檔處理。
- **多語言支持 (i18n)**: 內建繁體中文 (`zh_TW`) 與英文介面。
- **插件系統 (Plugins)**: 支援自定義前處理/後處理邏輯（如個資遮蔽、浮水印去除）。
- **並行處理**: 多核心 CPU 並行加速大型 PDF 處理。
- **雙 AI 校正**: 整合 Gemini/Claude LLM 進行語義錯誤修正。
- **可搜尋 PDF**: 自動生成可搜尋的 PDF 文件（文字層嵌入）。
- **模型預載**: 啟動時預載 OCR 引擎，首次請求節省 10-30 秒。

### 🛠️ 工具集
- **CLI**: 功能強大的命令列介面，支援豐富參數與 Rich UI。
- **Web Dashboard**: 現代化 Clean Slate 介面，明亮極簡設計，支援批次拖放與即時預覽。
- **Python SDK**: 簡潔的 Facade API，易於整合至其他專案。
- **Analytics**: Google Analytics 整合，追蹤使用者行為與關鍵事件。

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

## 🌐 雲端部署 (Cloud Deployment)

### 部署架構

由於 PaddleOCR 模型記憶體需求較高（~500MB RAM），推薦的部署架構為：

- **前端 (Frontend)**: Vercel（免費）
- **後端 (Backend)**: 本地運行 + ngrok 暴露

### 步驟 1：啟動本地後端

```bash
# 啟動 FastAPI 後端
python -m paddleocr_toolkit.api.main

# 後端將運行在 http://localhost:8000
```

### 步驟 2：使用 ngrok 暴露後端

```bash
# 安裝 ngrok (Windows)
winget install Ngrok.Ngrok

# 或前往 https://ngrok.com 下載

# 註冊並取得 authtoken
# https://dashboard.ngrok.com/get-started/your-authtoken

ngrok config add-authtoken YOUR_TOKEN

# 暴露本地 8000 端口
ngrok http 8000

# 複製輸出的 Forwarding URL，例如：
# https://abc123.ngrok.io
```

### 步驟 3：部署前端到 Vercel

1. **推送代碼到 GitHub**（如果還沒有）

```bash
git add .
git commit -m "Ready for deployment"
git push
```

2. **連接 Vercel**
   - 前往 [vercel.com](https://vercel.com)
   - 點擊 "Import Project"
   - 選擇您的 GitHub 倉庫
   - Root Directory 設為 `web-frontend`

3. **設定環境變數**
   - 在 Vercel 專案設定中，新增環境變數：
     ```
     NEXT_PUBLIC_API_URL=https://your-ngrok-url.ngrok.io
     ```
   - 替換為您在步驟 2 獲得的 ngrok URL

4. **部署**
   - 點擊 "Deploy"
   - 等待構建完成
   - 獲得前端 URL：`https://your-app.vercel.app`

### 🔒 安全建議

- ngrok 免費版會在每次重啟時變更 URL，需要更新 Vercel 環境變數
- **生產環境建議**：
  - 使用 ngrok Pro（固定域名）
  - 或改用 [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
  - 或升級雲端平台到 2GB RAM 實例

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

## 📝 日誌與除錯 (Logging)

本專案使用統一的日誌系統，可透過環境變數控制輸出詳細程度。

### 環境變數設定

```bash
# 設定日誌級別 (DEBUG, INFO, WARNING, ERROR)
export LOG_LEVEL=DEBUG

# 設定日誌目錄 (預設為 logs/)
export LOG_DIR=/path/to/logs
```

### 日誌檔案

日誌會自動旋轉並儲存於 `logs/` 目錄：
- `paddleocr.log`: 主要應用程式日誌
- `error.log`: 僅包含錯誤訊息
- `access.log`: Web API 存取日誌

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
