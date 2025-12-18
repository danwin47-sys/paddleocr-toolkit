# 🔧 故障排除指南

遇到問題？這份指南將幫助你快速診斷和解決常見問題。

---

## 📋 快速診斷

### 問題分類

執行診斷命令：

```python
python -c "
from paddle_ocr_tool import PaddleOCRTool
import sys
print(f'Python 版本: {sys.version}')
print(f'PaddleOCR 工具: OK')
"
```

---

## 🚨 常見錯誤

### 1. ImportError: No module named 'paddleocr'

**原因**: PaddleOCR 未安裝

**解決方案**:

```bash
pip install paddleocr
```

**驗證**:

```python
import paddleocr
print(paddleocr.__version__)
```

---

### 2. FileNotFoundError: PDF not found

**原因**: 檔案路徑錯誤

**解決方案**:

```python
from pathlib import Path

# 檢查檔案
pdf_path = Path("document.pdf")
if not pdf_path.exists():
    print(f"檔案不存在: {pdf_path.absolute()}")
else:
    print(f"檔案存在: {pdf_path.absolute()}")
```

**建議**: 使用絕對路徑

---

### 3. GPU 不可用

**症狀**:

```
WARNING: GPU is not available, using CPU instead
```

**診斷**:

```python
import paddle
print(f"GPU 可用: {paddle.device.is_compiled_with_cuda()}")
print(f"目前裝置: {paddle.device.get_device()}")
```

**解決方案**:

1. **安裝 GPU 版本**:

```bash
python -m pip install paddlepaddle-gpu
```

2. **檢查 CUDA**:

```bash
nvidia-smi
```

3. **指定裝置**:

```python
ocr_tool = PaddleOCRTool(device="cpu")  # 使用 CPU
```

---

### 4. 記憶體不足 (MemoryError)

**症狀**:

```
MemoryError: Unable to allocate...
```

**解決方案**:

**方法 1**: 降低 DPI

```bash
python paddle_ocr_tool.py doc.pdf --dpi 150
```

**方法 2**: 啟用壓縮

```bash
python paddle_ocr_tool.py doc.pdf --compress
```

**方法 3**: 分批處理

```python
from paddleocr_toolkit.core import streaming_utils

for batch in streaming_utils.batch_pages_generator("large.pdf", batch_size=5):
    # 處理小批次
    pass
```

---

### 5. UnicodeEncodeError (Windows)

**症狀**:

```
UnicodeEncodeError: 'cp950' codec can't encode character
```

**解決方案**:

**方法 1**: 設定環境變數

```powershell
$env:PYTHONIOENCODING = "utf-8"
```

**方法 2**: 在程式碼中設定

```python
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

**方法 3**: 輸出到檔案

```bash
python paddle_ocr_tool.py doc.pdf > output.txt
```

---

## 🔍 除錯技巧

### 啟用詳細日誌

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ocr_debug.log'),
        logging.StreamHandler()
    ]
)
```

### 檢查 OCR 結果

```python
results = ocr_tool.process_image("test.jpg")

print(f"找到 {len(results)} 個文字區塊")
for i, result in enumerate(results):
    print(f"{i+1}. 文字: {result.text}")
    print(f"   信心度: {result.confidence:.1%}")
    print(f"   位置: {result.bbox}")
```

### 效能分析

```python
import time
import psutil
import os

process = psutil.Process(os.getpid())

# 效能監控
start_time = time.time()
start_mem = process.memory_info().rss / 1024 / 1024

results, _ = ocr_tool.process_pdf("doc.pdf")

elapsed = time.time() - start_time
peak_mem = process.memory_info().rss / 1024 / 1024

print(f"耗時: {elapsed:.2f} 秒")
print(f"記憶體: {peak_mem - start_mem:.1f} MB")
```

---

## 🛠️ 設定問題

### 設定檔不生效

**檢查設定**:

```python
from paddleocr_toolkit.core import load_config

config = load_config("config.yaml")
print(config)
```

**常見問題**:

- YAML 格式錯誤
- 檔案路徑錯誤
- 權限問題

**驗證 YAML**:

```python
import yaml

with open("config.yaml") as f:
    try:
        config = yaml.safe_load(f)
        print("YAML 格式正確")
    except yaml.YAMLError as e:
        print(f"YAML 錯誤: {e}")
```

---

## 📊 品質問題

### OCR 辨識率低

**診斷**:

```python
def diagnose_quality(results):
    avg_conf = sum(r.confidence for page in results for r in page) / \
               sum(len(page) for page in results)
    
    print(f"平均信心度: {avg_conf:.1%}")
    
    if avg_conf < 0.7:
        print("建議:")
        print("1. 提高 DPI 到 300")
        print("2. 使用 hybrid 模式")
        print("3. 進行圖片預處理")
```

**改進方案**:

1. **提高 DPI**:

```python
results, _ = ocr_tool.process_pdf("doc.pdf", dpi=300)
```

2. **預處理**:

```python
from paddleocr_toolkit.processors import ImagePreprocessor

preprocessor = ImagePreprocessor()
clean_img = preprocessor.denoise(image)
binary_img = preprocessor.binarize(clean_img)
```

3. **換模式**:

```python
ocr_tool = PaddleOCRTool(mode="hybrid")
```

---

## ⚠️ 執行階段錯誤

### 模組初始化失敗

**錯誤訊息**:

```
RuntimeError: (PreconditionNotMet) Cannot load cudnn shared library
```

**解決方案**:

```bash
# 重新安裝 PaddlePaddle
pip uninstall paddlepaddle-gpu
pip install paddlepaddle-gpu
```

### 模型下載失敗

**錯誤訊息**:

```
URLError: <urlopen error [Errno 11001] getaddrinfo failed>
```

**解決方案**:

1. **設定代理**:

```python
import os
os.environ['HTTP_PROXY'] = 'http://proxy:port'
os.environ['HTTPS_PROXY'] = 'http://proxy:port'
```

2. **手動下載模型**:
存取 PaddleOCR 模型庫下載

---

## 🔄 重啟和重置

### 清理快取

```bash
# Windows
del /s /q __pycache__
del /s /q .pytest_cache
del /s /q .mypy_cache

# Linux/Mac
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name ".pytest_cache" -exec rm -rf {} +
```

### 重新安裝

```bash
# 完全解除安裝
pip uninstall -y paddleocr paddlepaddle paddlepaddle-gpu

# 重新安裝
pip install paddleocr paddlepaddle-gpu
```

---

## 📞 取得協助

### 提交問題報告

包含以下資訊：

```python
import sys
import platform
import paddleocr

print(f"Python 版本: {sys.version}")
print(f"平台: {platform.platform()}")
print(f"PaddleOCR 版本: {paddleocr.__version__}")
print(f"錯誤訊息: [貼上完整錯誤]")
```

### 社群資源

- 📖 [官方文件](../README.md)
- 💬 [GitHub Issues](https://github.com/danwin47-sys/paddleocr-toolkit/issues)
- 📚 [FAQ](FAQ.md)
- 🎯 [最佳實踐](BEST_PRACTICES.md)

---

## 🎯 預防措施

### 環境設定

```bash
# 建立虛擬環境
python -m venv ocr_env

# Windows
ocr_env\Scripts\activate

# Linux/Mac
source ocr_env/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

### 測試安裝

```python
# test_installation.py
try:
    from paddle_ocr_tool import PaddleOCRTool
    print("[OK] PaddleOCR 工具")
    
    import fitz
    print("[OK] PyMuPDF")
    
    import paddleocr
    print("[OK] PaddleOCR")
    
    print("\n所有依賴已正確安裝！")
    
except ImportError as e:
    print(f"[ERROR] 缺少依賴: {e}")
```

---

## 📋 檢查清單

執行以下檢查：

- [ ] Python 版本 >= 3.8
- [ ] PaddleOCR 已安裝
- [ ] PyMuPDF 已安裝
- [ ] 檔案路徑正確
- [ ] 足夠的磁碟空間
- [ ] 足夠的記憶體
- [ ] GPU 驅動正確（如使用）

---

## 📝 備註

**更新時間**: 2024-12-15  
**版本**: v1.0.0

**仍有問題？提交 Issue 取得協助！** 🆘
