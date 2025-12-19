# 💡 最佳實踐指南

PaddleOCR Toolkit 的專業使用建議與最佳實踐。

---

## 📊 效能最佳化

### 選擇合適的模式

```python
# 純文字檔案 → basic (最快)
ocr_tool = PaddleOCRTool(mode="basic")

# 包含表格 → structure
ocr_tool = PaddleOCRTool(mode="structure")

# 複雜檔案 → hybrid (推薦)
ocr_tool = PaddleOCRTool(mode="hybrid")
```

### DPI 設定建議

| 檔案型別 | 推薦 DPI | 說明 |
|----------|---------|------|
| 掃描檔案 | 200-300 | 高品質掃描 |
| 拍照檔案 | 150-200 | 清晰照片 |
| 螢幕截圖 | 72-150 | 數位檔案 |
| 低品質掃描 | 300+ | 模糊檔案 |

### GPU vs CPU

```python
# 大量檔案 → 使用 GPU
ocr_tool = PaddleOCRTool(device="gpu")

# 少量檔案 → CPU 即可
ocr_tool = PaddleOCRTool(device="cpu")
```

---

## 🎯 準確度提升

### 1. 圖片預處理

```python
from paddleocr_toolkit.processors import ImagePreprocessor

preprocessor = ImagePreprocessor()

# 去雜訊
clean = preprocessor.denoise(image)

# 二值化
binary = preprocessor.binarize(image, threshold=127)

# 傾斜校正
deskewed = preprocessor.deskew(image)
```

### 2. 使用適當的語言模型

```python
# 英文檔案
ocr_tool = PaddleOCRTool(lang="en")

# 中文檔案
ocr_tool = PaddleOCRTool(lang="ch")

# 多語言檔案
ocr_tool = PaddleOCRTool(lang="ch", use_angle_cls=True)
```

### 3. 信心度過濾

```python
# 過濾低信心度結果
high_confidence_results = [
    r for r in results 
    if r.confidence >= 0.8
]
```

---

## 💾 記憶體管理

### 處理大型 PDF

```python
# 方法 1: 分批處理
from paddleocr_toolkit.core import streaming_utils

for batch in streaming_utils.batch_pages_generator("large.pdf", batch_size=10):
    results = []
    for page_num, page in batch:
        result = ocr_tool.process_page(page)
        results.append(result)
    # 處理完立即儲存
    save_batch(results)
```

```python
# 方法 2: 啟用壓縮
ocr_tool = PaddleOCRTool(
    enable_compression=True,
    jpeg_quality=85
)
```

### 記憶體監控

```python
import psutil
import os

process = psutil.Process(os.getpid())

# 處理前
before = process.memory_info().rss / 1024 / 1024

results, _ = ocr_tool.process_pdf("doc.pdf")

# 處理後
after = process.memory_info().rss / 1024 / 1024

print(f"記憶體使用: {after - before:.1f} MB")
```

---

## 🚀 批次處理

### 並行處理多個檔案

```python
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

def process_single_pdf(pdf_path):
    ocr_tool = PaddleOCRTool(mode="basic")
    results, _ = ocr_tool.process_pdf(str(pdf_path))
    return pdf_path.name, results

pdf_files = list(Path("pdfs/").glob("*.pdf"))

with ProcessPoolExecutor(max_workers=4) as executor:
    results = executor.map(process_single_pdf, pdf_files)
    
for filename, ocr_results in results:
    print(f"完成: {filename}")
```

### 使用進度條

```python
from tqdm import tqdm

pdf_files = list(Path("pdfs/").glob("*.pdf"))

for pdf_file in tqdm(pdf_files, desc="處理 PDF"):
    results, _ = ocr_tool.process_pdf(
        str(pdf_file),
        show_progress=False  # 關閉內部進度
    )
```

---

## 📝 輸出管理

### 組織輸出結構

```python
from pathlib import Path
from datetime import datetime

# 按日期組織
date_str = datetime.now().strftime("%Y%m%d")
output_dir = Path(f"output/{date_str}")
output_dir.mkdir(parents=True, exist_ok=True)

# 儲存
output_mgr = OutputManager(output_dir=str(output_dir))
output_mgr.write_all_formats(results, pdf_file.stem)
```

### 檔名規範

```python
# 統一命名規則
def get_output_filename(input_path, suffix=""):
    """
    input: /path/to/document.pdf
    output: document_ocr_20241215.md
    """
    stem = Path(input_path).stem
    date = datetime.now().strftime("%Y%m%d")
    return f"{stem}_ocr{suffix}_{date}"
```

---

## 🔧 錯誤處理

### 穩健的錯誤處理

```python
import logging

logging.basicConfig(level=logging.INFO)

def safe_process_pdf(pdf_path):
    """安全處理 PDF 並帶有完整錯誤處理"""
    try:
        results, _ = ocr_tool.process_pdf(pdf_path)
        return results, None
        
    except FileNotFoundError:
        error_msg = f"檔案不存在: {pdf_path}"
        logging.error(error_msg)
        return None, error_msg
        
    except ImportError as e:
        error_msg = f"缺少依賴: {e}"
        logging.error(error_msg)
        return None, error_msg
        
    except Exception as e:
        error_msg = f"處理失敗: {e}"
        logging.exception(error_msg)
        return None, error_msg
```

### 重試機制

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def process_with_retry(pdf_path):
    return ocr_tool.process_pdf(pdf_path)
```

---

## 📊 品質控制

### 自動品質檢查

```python
def quality_check(results):
    """檢查 OCR 結果品質"""
    issues = []
    
    # 檢查 1: 平均信心度
    avg_conf = sum(r.confidence for page in results for r in page) / \
               sum(len(page) for page in results)
    
    if avg_conf < 0.7:
        issues.append(f"平均信心度過低: {avg_conf:.1%}")
    
    # 檢查 2: 空頁面
    empty_pages = [i for i, page in enumerate(results) if len(page) == 0]
    if empty_pages:
        issues.append(f"空頁面: {empty_pages}")
    
    # 檢查 3: 文字過少
    min_texts = min(len(page) for page in results if len(page) > 0)
    if min_texts < 5:
        issues.append(f"某些頁面文字過少: {min_texts}")
    
    return issues

# 使用
issues = quality_check(all_results)
if issues:
    print("品質問題:")
    for issue in issues:
        print(f"  - {issue}")
```

### 人工審核輔助

```python
def mark_low_confidence_results(results, threshold=0.7):
    """標記低信心度結果以便人工審核"""
    marked = []
    
    for page_num, page_results in enumerate(results):
        for result in page_results:
            if result.confidence < threshold:
                marked.append({
                    'page': page_num + 1,
                    'text': result.text,
                    'confidence': result.confidence,
                    'bbox': result.bbox
                })
    
    return marked
```

---

## 🎨 專案結構建議

### 推薦目錄結構

```
my_ocr_project/
├── config/
│   ├── production.yaml
│   └── development.yaml
├── input/
│   ├── pdfs/
│   └── images/
├── output/
│   ├── 20241215/
│   └── 20241214/
├── logs/
│   └── ocr.log
├── scripts/
│   ├── batch_process.py
│   └── quality_check.py
└── main.py
```

### 設定管理

```yaml
# config/production.yaml
ocr:
  mode: hybrid
  device: gpu
  dpi: 200
  lang: ch
  
output:
  directory: ./output
  formats: [md, json, html]
  
performance:
  max_workers: 4
  batch_size: 10
  enable_compression: true
  
logging:
  level: INFO
  file: ./logs/ocr.log
```

---

## 🔍 測試建議

### 單元測試

```python
import pytest
from paddle_ocr_tool import PaddleOCRTool

def test_basic_ocr():
    ocr_tool = PaddleOCRTool(mode="basic")
    results = ocr_tool.process_image("test.jpg")
    
    assert len(results) > 0
    assert all(r.text for r in results)
    assert all(0 <= r.confidence <= 1 for r in results)
```

### 整合測試

```python
def test_pdf_workflow():
    """測試完整 PDF 處理流程"""
    ocr_tool = PaddleOCRTool(mode="hybrid")
    
    # 處理
    results, _ = ocr_tool.process_pdf("test.pdf")
    
    # 驗證
    assert len(results) > 0
    
    # 輸出
    text = ocr_tool.get_text(results)
    assert len(text) > 0
```

---

## 📚 檔案建議

### 程式碼註解

```python
class MyOCRProcessor:
    """自定義 OCR 處理器
    
    負責處理特定型別之檔案，包括預處理、
    OCR 處理、後處理和結果驗證。
    
    Attributes:
        ocr_tool: PaddleOCRTool 例項
        preprocessor: 圖片前處理器
        validator: 結果驗證器
        
    Example:
        >>> processor = MyOCRProcessor(mode="hybrid")
        >>> results = processor.process("doc.pdf")
        >>> processor.save_results(results, "output/")
    """
    
    def process(self, pdf_path: str) -> List[List[OCRResult]]:
        """處理 PDF 檔案
        
        Args:
            pdf_path: PDF 檔案路徑
            
        Returns:
            每頁之 OCR 結果列表
            
        Raises:
            FileNotFoundError: 檔案不存在
            ValueError: PDF 格式錯誤
        """
        pass
```

---

## 🎯 效能基準

### 建立基準測試

```python
import time

def benchmark_ocr(pdf_path, modes=["basic", "hybrid", "structure"]):
    """對比不同模式之效能"""
    results = {}
    
    for mode in modes:
        ocr_tool = PaddleOCRTool(mode=mode)
        
        start = time.time()
        all_results, _ = ocr_tool.process_pdf(pdf_path, show_progress=False)
        elapsed = time.time() - start
        
        results[mode] = {
            'time': elapsed,
            'pages': len(all_results),
            'texts': sum(len(page) for page in all_results)
        }
    
    return results
```

---

## 🌟 生產部署

### Docker 部署

```dockerfile
FROM python:3.8

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

### 環境變數

```python
import os

# 從環境變數讀取設定
OCR_MODE = os.getenv("OCR_MODE", "hybrid")
OCR_DEVICE = os.getenv("OCR_DEVICE", "gpu")
DPI = int(os.getenv("DPI", "200"))

ocr_tool = PaddleOCRTool(
    mode=OCR_MODE,
    device=OCR_DEVICE,
    dpi=DPI
)
```

---

## 📖 延伸閱讀

- [快速開始](QUICK_START.md)
- [API 指南](API_GUIDE.md)
- [故障排除](TROUBLESHOOTING.md)
- [範例專案](../examples/README.md)

---

**更新時間**: 2024-12-15  
**版本**: v1.0.0
