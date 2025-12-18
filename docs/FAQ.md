# ❓ 常見問題 (FAQ)

PaddleOCR Toolkit 使用中的常見問題與解答。

---

## 📦 安裝相關

### Q: 如何安裝 PaddleOCR Toolkit?

**A**: 使用 pip 安裝：

```bash
pip install paddleocr PyMuPDF pillow
```

---

### Q: GPU 版本如何安裝?

**A**: 安裝 GPU 版本的 PaddlePaddle：

```bash
# CUDA 11.7
python -m pip install paddlepaddle-gpu

# 或指定版本
python -m pip install paddlepaddle-gpu==2.6.0 -i https://mirror.baidu.com/pypi/simple
```

---

### Q: 缺少某個模組怎麼辦?

**A**: 安裝選配依賴：

```bash
# Rich (CLI 美化)
pip install rich

# psutil (效能監控)
pip install psutil

# wordninja (英文分詞)
pip install wordninja
```

---

## 🚀 使用相關

### Q: 如何提高 OCR 準確度?

**A**: 嘗試以下方法：

1. **提高 DPI**:

```bash
python paddle_ocr_tool.py doc.pdf --dpi 300
```

2. **使用 hybrid 模式**:

```bash
python paddle_ocr_tool.py doc.pdf --mode hybrid
```

3. **圖片預處理**:

```python
from paddleocr_toolkit.processors import ImagePreprocessor

preprocessor = ImagePreprocessor()
clean_img = preprocessor.denoise(image)
binary_img = preprocessor.binarize(clean_img)
```

---

### Q: GPU 加速無法運作?

**A**: 檢查以下項目：

1. **確認 GPU 可用**:

```python
import paddle
print(paddle.device.get_device())
```

2. **指定使用 GPU**:

```python
ocr_tool = PaddleOCRTool(device="gpu", use_gpu=True)
```

3. **檢查 CUDA 版本**:

```bash
nvidia-smi
```

---

### Q: 記憶體不足怎麼辦?

**A**: 嘗試以下優化：

1. **降低 DPI**:

```bash
python paddle_ocr_tool.py doc.pdf --dpi 150
```

2. **啟用壓縮**:

```bash
python paddle_ocr_tool.py doc.pdf --compress
```

3. **分批處理**:

```python
from paddleocr_toolkit.core import streaming_utils

for batch in streaming_utils.batch_pages_generator("large.pdf", batch_size=5):
    # 處理 batch
    pass
```

---

### Q: 如何處理大型 PDF?

**A**: 使用串流處理：

```python
from paddleocr_toolkit.core import streaming_utils

with streaming_utils.open_pdf_context("large.pdf") as pdf_doc:
    for page_num, page in streaming_utils.pdf_pages_generator("large.pdf"):
        result = ocr_tool.process_page(page)
        # 立即處理並釋放
```

---

## 📄 輸出相關

### Q: 如何生成可搜尋 PDF?

**A**: 使用 `--searchable` 選項：

```bash
python paddle_ocr_tool.py input.pdf --searchable
```

或使用 API：

```python
ocr_tool.process_pdf(
    "input.pdf",
    output_searchable_pdf="output.pdf"
)
```

---

### Q: 支援哪些輸出格式?

**A**: 支援以下格式：

- Markdown (.md)
- JSON (.json)
- HTML (.html)
- 純文字 (.txt)
- 可搜尋 PDF (.pdf)

使用方法：

```bash
python paddle_ocr_tool.py doc.pdf --format md json html
```

---

### Q: 如何自訂輸出格式?

**A**: 繼承 OutputManager：

```python
from paddleocr_toolkit.outputs import OutputManager

class MyOutputManager(OutputManager):
    def write_custom(self, results, output_path):
        # 自訂輸出邏輯
        pass
```

---

## 🎯 效能相關

### Q: 處理速度太慢?

**A**: 優化建議：

1. **使用 GPU**:

```python
ocr_tool = PaddleOCRTool(device="gpu")
```

2. **降低 DPI** (如果可接受):

```python
ocr_tool.process_pdf("doc.pdf", dpi=150)
```

3. **使用 basic 模式** (純文字文件):

```python
ocr_tool = PaddleOCRTool(mode="basic")
```

---

### Q: 如何批次處理多個文件?

**A**: 使用 BatchProcessor：

```python
from paddleocr_toolkit.processors import BatchProcessor
from pathlib import Path

batch_processor = BatchProcessor(max_workers=4)
pdf_files = list(Path("pdfs/").glob("*.pdf"))

for pdf_file in pdf_files:
    results, _ = ocr_tool.process_pdf(str(pdf_file))
```

---

## 🔧 技術相關

### Q: 如何處理傾斜的文件?

**A**: 使用角度分類：

```python
ocr_tool = PaddleOCRTool(use_angle_cls=True)
```

或手動校正：

```python
from paddleocr_toolkit.processors import ImagePreprocessor

preprocessor = ImagePreprocessor()
deskewed = preprocessor.deskew(image)
```

---

### Q: 支援哪些語言?

**A**: 支援多種語言：

- 中文 (ch)
- 英文 (en)
- 日文 (japan)
- 韓文 (korean)
- 等等...

使用方法：

```python
ocr_tool = PaddleOCRTool(lang="en")
```

---

### Q: 如何處理表格?

**A**: 使用 structure 模式：

```python
ocr_tool = PaddleOCRTool(mode="structure")
results, _ = ocr_tool.process_pdf("table_doc.pdf")
```

---

## 🐛 錯誤處理

### Q: FileNotFoundError 錯誤?

**A**: 檢查檔案路徑：

```python
from pathlib import Path

pdf_path = Path("document.pdf")
if not pdf_path.exists():
    print(f"檔案不存在: {pdf_path}")
else:
    results, _ = ocr_tool.process_pdf(str(pdf_path))
```

---

### Q: ImportError 錯誤?

**A**: 安裝缺少的依賴：

```bash
# fitz (PyMuPDF)
pip install PyMuPDF

# wordninja
pip install wordninja

# rich
pip install rich
```

---

### Q: UnicodeEncodeError 錯誤 (Windows)?

**A**: 設定環境變數：

```bash
# PowerShell
$env:PYTHONIOENCODING = "utf-8"

# 或在 Python 中
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

---

## 📱 進階使用

### Q: 如何整合到 Web 應用程式?

**A**: 使用 Flask 範例：

```python
from flask import Flask, request, jsonify
from paddle_ocr_tool import PaddleOCRTool

app = Flask(__name__)
ocr_tool = PaddleOCRTool(mode="hybrid")

@app.route('/ocr', methods=['POST'])
def ocr_endpoint():
    file = request.files['file']
    results = ocr_tool.process_image(file)
    return jsonify([{
        'text': r.text,
        'confidence': r.confidence
    } for r in results])
```

---

### Q: 如何使用設定檔?

**A**: 建立 config.yaml：

```yaml
ocr:
  mode: hybrid
  device: gpu
  dpi: 200

output:
  format: md
  directory: ./output
```

使用：

```bash
python paddle_ocr_tool.py doc.pdf --config config.yaml
```

---

### Q: 如何監控處理進度?

**A**: 使用進度回呼：

```python
def progress_callback(current, total):
    print(f"進度: {current}/{total} ({current/total*100:.1f}%)")

results, _ = ocr_tool.process_pdf(
    "doc.pdf",
    progress_callback=progress_callback
)
```

---

## 🔍 調核 (Debug) 相關

### Q: 如何啟用詳細日誌?

**A**: 設定 logging 級別：

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

---

### Q: 如何檢查 OCR 結果品質?

**A**: 使用品質檢查函式：

```python
def check_quality(results):
    avg_conf = sum(r.confidence for page in results for r in page) / \
               sum(len(page) for page in results)
    
    print(f"平均信心度: {avg_conf:.1%}")
    
    if avg_conf < 0.7:
        print("⚠️ 警告：信心度較低，建議提高 DPI 或使用不同模式")
```

---

## 💡 最佳實踐

### Q: 生產環境部署建議?

**A**: 遵循最佳實踐：

1. **使用設定檔** - 不要硬編碼參數
2. **錯誤處理** - 完整的 try-except
3. **日誌記錄** - 記錄所有重要操作
4. **資源管理** - 適當的 context manager
5. **效能監控** - 追蹤處理時間和記憶體

詳見 [最佳實踐指南](BEST_PRACTICES.md)

---

### Q: 如何貢獻程式碼?

**A**: 歡迎貢獻！

1. Fork 專案
2. 建立 feature 分支
3. 提交程式碼
4. 建立 Pull Request

詳見 [貢獻指南](../CONTRIBUTING.md)

---

## 📚 更多資源

- [快速開始](QUICK_START.md)
- [API 指南](API_GUIDE.md)
- [最佳實踐](BEST_PRACTICES.md)
- [故障排除](TROUBLESHOOTING.md)
- [範例項目](../examples/README.md)

---

## 🆘 還有問題?

- 📧 提交 Issue: [GitHub Issues](https://github.com/danwin47-sys/paddleocr-toolkit/issues)
- 💬 討論區: [GitHub Discussions](https://github.com/danwin47-sys/paddleocr-toolkit/discussions)
- 📖 文件: [完整文件](../README.md)

---

**更新時間**: 2024-12-15  
**版本**: v1.0.0

**找不到答案？歡迎提問！** 🙋‍♂️
