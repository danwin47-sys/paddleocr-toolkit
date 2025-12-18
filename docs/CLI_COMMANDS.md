# CLI 命令文件

## 可用命令

PaddleOCR Toolkit v1.2.0 提供以下 CLI 命令：

---

## paddleocr init

初始化 PaddleOCR Toolkit 專案。

### 用法

```bash
paddleocr init [directory]
```

### 參數

- `directory`: 專案目錄（可選，預設為當前目錄）

### 範例

```bash
# 在當前目錄初始化
paddleocr init

# 在指定目錄初始化
paddleocr init my_ocr_project
```

### 建立內容

- `input/` - 輸入檔案目錄
- `output/` - 輸出結果目錄
- `config/` - 設定檔目錄
- `logs/` - 日誌檔案目錄
- `config/default.yaml` - 預設設定
- `README.md` - 專案說明
- `.gitignore` - Git 忽略檔案

---

## paddleocr config

互動式設定精靈。

### 用法

```bash
paddleocr config [--show CONFIG_FILE]
```

### 選項

- `--show CONFIG_FILE`: 顯示指定設定檔的內容

### 範例

```bash
# 啟動設定精靈
paddleocr config

# 顯示設定檔
paddleocr config --show config/default.yaml
```

### 設定項

- **OCR 設定**: mode, device, dpi, lang
- **輸出設定**: format, directory
- **效能設定**: batch_size, max_workers, enable_cache
- **日誌設定**: level, file

---

## paddleocr process

處理檔案或目錄。

### 用法

```bash
paddleocr process INPUT [options]
```

### 參數

- `INPUT`: 輸入檔案或目錄

### 選項

- `--mode {basic,hybrid,structure}`: OCR 模式（預設: hybrid）
- `--output DIR`: 輸出目錄
- `--format FORMAT`: 輸出格式（預設: md）

### 範例

```bash
# 處理單個 PDF
paddleocr process document.pdf

# 指定模式和輸出
paddleocr process document.pdf --mode structure --output results/

# 批次處理
paddleocr process documents/ --format json
```

---

## paddleocr benchmark

效能基準測試。

### 用法

```bash
paddleocr benchmark PDF [--output REPORT]
```

### 參數

- `PDF`: 測試 PDF 檔案

### 選項

- `--output REPORT`: 報告輸出路徑（可選）

### 範例

```bash
# 執行基準測試
paddleocr benchmark test.pdf

# 儲存報告
paddleocr benchmark test.pdf --output benchmark_report.json
```

### 測試場景

1. Basic (DPI 150)
2. Basic (DPI 200)
3. Hybrid (DPI 150)
4. Hybrid (DPI 200)

### 輸出

- 處理時間
- 速度（秒/頁）
- 記憶體使用
- JSON 格式報告

---

## paddleocr validate

驗證 OCR 結果準確率。

### 用法

```bash
paddleocr validate OCR_RESULTS GROUND_TRUTH
```

### 參數

- `OCR_RESULTS`: OCR 結果 JSON 檔案
- `GROUND_TRUTH`: 真實文字 TXT 檔案

### 範例

```bash
paddleocr validate output.json ground_truth.txt
```

### 指標

- **字元準確率**: 字元層級的準確度
- **詞準確率**: 詞層級的準確度
- **編輯距離**: Levenshtein 距離
- **綜合評分**: 整體評級

### 輸出

```
字元準確率: 95.2%
詞準確率: 92.8%
編輯距離: 45
綜合準確率: 94.0%
評級: +++ 優秀
```

---

## 全域選項

所有命令都支援以下全域選項：

- `--version`: 顯示版本資訊
- `--help`: 顯示幫助資訊

---

## 範例工作流程

### 1. 建立新專案

```bash
# 初始化
paddleocr init my_project
cd my_project

# 設定
paddleocr config

# 處理檔案
cp ~/document.pdf input/
paddleocr process input/document.pdf

# 查看結果
cat output/document.md
```

### 2. 效能測試

```bash
# 測試效能
paddleocr benchmark test.pdf --output report.json

# 查看報告
cat report.json
```

### 3. 品質驗證

```bash
# 處理檔案
paddleocr process document.pdf --format json --output results/

# 驗證準確率
paddleocr validate results/document.json ground_truth.txt
```

---

## 設定檔範例

`config/default.yaml`:

```yaml
ocr:
  mode: hybrid
  device: gpu
  dpi: 200
  lang: ch
  use_angle_cls: true

output:
  format: md
  directory: ./output

performance:
  batch_size: 8
  max_workers: 4
  enable_cache: true

logging:
  level: INFO
  file: ./logs/paddleocr.log
```

---

## 常見問題

### Q: 如何更改 OCR 語言？

A: 使用 `config` 命令或編輯設定檔中的 `ocr.lang`。

### Q: 如何提升處理速度？

A:

1. 使用 GPU (`device: gpu`)
2. 降低 DPI (`dpi: 150`)
3. 啟用快取 (`enable_cache: true`)
4. 增加批次大小 (`batch_size: 16`)

### Q: 支援哪些輸出格式？

A: md, json, html, txt, xlsx

---

**更多資訊**: [完整文件](https://github.com/danwin47-sys/paddleocr-toolkit)
