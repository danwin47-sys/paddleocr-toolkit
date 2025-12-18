# PaddleOCR Toolkit 项目

这个项目使用 PaddleOCR Toolkit 进行文档OCR处理。

## 目录结构

```
.
├── input/          # 输入文件
├── output/         # 输出结果
├── config/         # 配置文件
│   └── default.yaml
└── logs/           # 日志文件
```

## 使用方法

```bash
# 处理单个文件
# 處理單個檔案
python -m paddleocr_toolkit input/document.pdf

# 使用設定檔
python -m paddleocr_toolkit input/document.pdf --config config/default.yaml

# 批次處理
python -m paddleocr_toolkit input/
```

## 設定

編輯 `config/default.yaml` 來自定義設定。

## 文件

- [快速開始](https://github.com/danwin47-sys/paddleocr-toolkit/blob/master/docs/QUICK_START.md)
- [API文件](https://github.com/danwin47-sys/paddleocr-toolkit/blob/master/docs/API_GUIDE.md)
