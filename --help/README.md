# PaddleOCR Toolkit ?目

???目使用 PaddleOCR Toolkit ?行文?OCR?理。

## 目??構

```
.
├── input/          # ?入檔案
├── output/         # ?出?果
├── config/         # 配置檔案
│   └── default.yaml
└── logs/           # 日誌檔案
```

## 使用方法

```bash
# ?理??檔案
python -m paddleocr_toolkit input/document.pdf

# 使用配置檔案
python -m paddleocr_toolkit input/document.pdf --config config/default.yaml

# 批次?理
python -m paddleocr_toolkit input/
```

## 配置

?? `config/default.yaml` ?自定??置。

## 文?

- [快速?始](https://github.com/danwin47-sys/paddleocr-toolkit/blob/master/docs/QUICK_START.md)
- [API文?](https://github.com/danwin47-sys/paddleocr-toolkit/blob/master/docs/API_GUIDE.md)
