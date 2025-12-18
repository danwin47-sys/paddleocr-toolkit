# 📚 API 使用指南

完整的 PaddleOCR Toolkit API 參考文件。

---

## 📖 目錄

- [核心類別](#核心類別)
- [OCR 處理](#ocr-處理)
- [PDF 處理](#pdf-處理)
- [輸出管理](#輸出管理)
- [工具函式](#工具函式)

---

## 核心類別

### PaddleOCRTool

主要的 OCR 處理類別。

#### 初始化

```python
from paddle_ocr_tool import PaddleOCRTool

ocr_tool = PaddleOCRTool(
    mode="basic",          # OCR 模式: basic, structure, vl, formula, hybrid
    device="gpu",          # 裝置: gpu, cpu
    lang="ch",             # 語言: ch, en, etc.
    use_angle_cls=True,    # 使用角度分類
    use_gpu=True,          # 使用 GPU
    dpi=150                # PDF 轉圖片 DPI
)
```

#### 參數說明

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `mode` | str | "basic" | OCR 模式 |
| `device` | str | "gpu" | 計算裝置 |
| `lang` | str | "ch" | 識別語言 |
| `use_angle_cls` | bool | True | 文字方向分類 |
| `use_gpu` | bool | True | 使用 GPU |
| `dpi` | int | 150 | PDF 解析度 |

---

## OCR 處理

### process_image()

處理單張圖片。

```python
results = ocr_tool.process_image(
    image_path="document.jpg"
)

# 傳回: List[OCRResult]
for result in results:
    print(result.text)           # 識別文字
    print(result.confidence)     # 信心度 (0-1)
    print(result.bbox)          # 邊界框座標
```

#### OCRResult 物件

```python
class OCRResult:
    text: str              # 識別的文字
    confidence: float      # 信心度 (0.0-1.0)
    bbox: List[List[float]]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    
    # 便利屬性
    @property
    def x(self) -> float:  # 左上角 x 座標
    
    @property
    def y(self) -> float:  # 左上角 y 座標
    
    @property
    def width(self) -> float:  # 寬度
    
    @property
    def height(self) -> float:  # 高度
```

### process_pdf()

處理 PDF 文件。

```python
all_results, pdf_generator = ocr_tool.process_pdf(
    pdf_path="document.pdf",
    output_searchable_pdf="output.pdf",  # 可選
    pages=None,                          # None=全部頁面，或 [0,1,2]
    dpi=200,                            # 覆蓋預設 DPI
    show_progress=True                   # 顯示進度條
)

# all_results: List[List[OCRResult]] - 每頁的結果
# pdf_generator: PDFGenerator - PDF 生成器（如果 output_searchable_pdf 不為 None）
```

#### 範例：處理特定頁面

```python
# 只處理第 1, 3, 5 頁
results, _ = ocr_tool.process_pdf(
    "document.pdf",
    pages=[0, 2, 4]  # 0-indexed
)
```

#### 範例：生成可搜尋 PDF

```python
results, pdf_gen = ocr_tool.process_pdf(
    "input.pdf",
    output_searchable_pdf="output_searchable.pdf",
    dpi=300
)

# PDF 會自動儲存
```

---

## PDF 處理

### get_text()

從 OCR 結果提取純文字。

```python
# 單頁結果
text = ocr_tool.get_text(
    page_results,
    separator="\n",        # 文字間分隔符
    skip_empty=True        # 跳過空行
)

# 多頁結果
full_text = ocr_tool.get_text(
    all_results,
    separator="\n",
    skip_empty=True
)
```

### save_as_markdown()

儲存為 Markdown 格式。

```python
ocr_tool.save_as_markdown(
    all_results,
    output_path="output.md",
    add_page_numbers=True   # 添加頁碼標記
)
```

### save_as_json()

儲存為 JSON 格式。

```python
ocr_tool.save_as_json(
    all_results,
    output_path="output.json",
    indent=2                # JSON 縮排
)
```

---

## 輸出管理

### OutputManager

管理多種輸出格式。

```python
from paddleocr_toolkit.outputs import OutputManager

output_mgr = OutputManager(
    output_dir="./output",
    formats=["md", "json", "html"]
)

# 寫入多種格式
output_mgr.write_all_formats(
    all_results,
    base_filename="document"
)

# 生成的檔案:
# - output/document.md
# - output/document.json
# - output/document.html
```

#### 單獨格式

```python
# Markdown
output_mgr.write_markdown(results, "doc.md")

# JSON
output_mgr.write_json(results, "doc.json")

# HTML
output_mgr.write_html(results, "doc.html")

# 純文字
output_mgr.write_text(results, "doc.txt")
```

---

## 工具函式

### 批次處理

```python
from paddleocr_toolkit.processors import BatchProcessor

batch_processor = BatchProcessor(
    max_workers=4,    # 並行執行緒數
    batch_size=8     # 批次大小
)

# 處理多個圖片
images = [img1, img2, img3, ...]
results = batch_processor.process_images(
    images,
    process_func=ocr_tool.process_image
)
```

### 圖片預處理

```python
from paddleocr_toolkit.processors import ImagePreprocessor

preprocessor = ImagePreprocessor()

# 去雜訊
clean_img = preprocessor.denoise(image)

# 二值化
binary_img = preprocessor.binarize(image)

# 傾斜校正
rotated_img = preprocessor.deskew(image)
```

### 設定載入

```python
from paddleocr_toolkit.core import load_config

config = load_config("config.yaml")

# 套送到 args
from paddleocr_toolkit.cli import apply_config_to_args
apply_config_to_args(config, args)
```

---

## 進階使用

### 自訂處理流程

```python
from paddleocr_toolkit.core import OCREngineManager, OCRResultParser

# 建立自訂引擎
engine = OCREngineManager(mode="hybrid")
engine.init_engine()

# 處理
raw_result = engine.predict(image)

# 解析結果
parser = OCRResultParser()
ocr_results = parser.parse_basic_result(raw_result)

# 清理
engine.close()
```

### 使用 Context Manager

```python
from paddleocr_toolkit.core import OCREngineManager

with OCREngineManager(mode="basic") as engine:
    result = engine.predict(image)
    # 自動清理
```

### 串流處理大型 PDF

```python
from paddleocr_toolkit.core import streaming_utils

with streaming_utils.open_pdf_context("large.pdf") as pdf_doc:
    for page_num, page in streaming_utils.pdf_pages_generator("large.pdf"):
        # 處理單頁
        result = ocr_tool.process_page(page)
```

---

## 錯誤處理

### 基本錯誤處理

```python
try:
    results = ocr_tool.process_pdf("document.pdf")
except FileNotFoundError:
    print("PDF 檔案不存在")
except ImportError:
    print("缺少必要的套件")
except Exception as e:
    print(f"處理錯誤: {e}")
```

### 使用 strict_mode

```python
from paddleocr_toolkit.core import OCRResultParser

# 嚴格模式：錯誤時丟出異常
parser = OCRResultParser(strict_mode=True)

try:
    results = parser.parse_basic_result(raw_result)
except ValueError as e:
    print(f"解析失敗: {e}")
```

---

## 效能優化

### GPU 加速

```python
ocr_tool = PaddleOCRTool(
    mode="basic",
    device="gpu",
    use_gpu=True
)
```

### 批次處理

```python
# 處理多個文件
from pathlib import Path

pdf_files = list(Path("pdfs/").glob("*.pdf"))

batch_processor = BatchProcessor(max_workers=4)

for pdf_file in pdf_files:
    results, _ = ocr_tool.process_pdf(str(pdf_file))
```

### 記憶體優化

```python
# 啟用壓縮
ocr_tool = PaddleOCRTool(
    mode="basic",
    enable_compression=True,
    jpeg_quality=85
)

# 降低 DPI
results, _ = ocr_tool.process_pdf("doc.pdf", dpi=150)
```

---

## 完整範例

### 端到端 OCR 流程

```python
from paddle_ocr_tool import PaddleOCRTool
from paddleocr_toolkit.outputs import OutputManager

# 1. 初始化
ocr_tool = PaddleOCRTool(mode="hybrid", device="gpu")
output_mgr = OutputManager(output_dir="./output")

# 2. 處理 PDF
all_results, pdf_gen = ocr_tool.process_pdf(
    "input.pdf",
    output_searchable_pdf="output_searchable.pdf",
    dpi=200
)

# 3. 儲存多種格式
output_mgr.write_all_formats(all_results, "document")

# 4. 提取純文字
full_text = ocr_tool.get_text(all_results)
print(f"總字數: {len(full_text)}")

# 5. 統計
total_pages = len(all_results)
total_texts = sum(len(page) for page in all_results)
avg_confidence = sum(
    sum(r.confidence for r in page) 
    for page in all_results
) / total_texts

print(f"處理完成: {total_pages}頁, {total_texts}個文字區塊")
print(f"平均信心度: {avg_confidence:.1%}")
```

---

## 參考資源

- [快速開始](QUICK_START.md)
- [最佳實踐](BEST_PRACTICES.md)
- [故障排除](TROUBLESHOOTING.md)
- [範例項目](../examples/README.md)

---

**更新時間**: 2024-12-15  
**版本**: v1.0.0
