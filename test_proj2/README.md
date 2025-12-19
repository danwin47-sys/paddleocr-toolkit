# PaddleOCR Toolkit 專案

這個專案使用 PaddleOCR Toolkit 進行檔案OCR處理。

## 目錄結構

```
.
├── input/          # 輸入檔案
├── output/         # 輸出結果
├── config/         # 配置檔案
│   └── default.yaml
└── logs/           # 日誌檔案
```

## 使用方法

```bash
# 處理單個檔案
# 處理單個檔案
python -m paddleocr_toolkit input/document.pdf

# 使用設定檔
python -m paddleocr_toolkit input/document.pdf --config config/default.yaml

# 批次處理
python -m paddleocr_toolkit input/
```

## 設定

編輯 `config/default.yaml` 來自定義設定。

## 檔案

- [快速開始](https://github.com/danwin47-sys/paddleocr-toolkit/blob/master/docs/QUICK_START.md)
- [API檔案](https://github.com/danwin47-sys/paddleocr-toolkit/blob/master/docs/API_GUIDE.md)
