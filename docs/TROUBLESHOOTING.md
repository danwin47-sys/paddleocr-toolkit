# 🔧 故障排除指南

遇到问题？这份指南将帮助你快速诊断和解决常见问题。

---

## 📋 快速诊断

### 问题分类

运行诊断命令：

```python
python -c "
from paddle_ocr_tool import PaddleOCRTool
import sys
print(f'Python版本: {sys.version}')
print(f'PaddleOCR工具: OK')
"
```

---

## 🚨 常见错误

### 1. ImportError: No module named 'paddleocr'

**原因**: PaddleOCR未安装

**解决方案**:

```bash
pip install paddleocr
```

**验证**:

```python
import paddleocr
print(paddleocr.__version__)
```

---

### 2. FileNotFoundError: PDF not found

**原因**: 文件路径错误

**解决方案**:

```python
from pathlib import Path

# 检查文件
pdf_path = Path("document.pdf")
if not pdf_path.exists():
    print(f"文件不存在: {pdf_path.absolute()}")
else:
    print(f"文件存在: {pdf_path.absolute()}")
```

**建议**: 使用绝对路径

---

### 3. GPU不可用

**症状**:

```
WARNING: GPU is not available, using CPU instead
```

**诊断**:

```python
import paddle
print(f"GPU可用: {paddle.device.is_compiled_with_cuda()}")
print(f"当前设备: {paddle.device.get_device()}")
```

**解决方案**:

1. **安装GPU版本**:

```bash
python -m pip install paddlepaddle-gpu
```

2. **检查CUDA**:

```bash
nvidia-smi
```

3. **指定设备**:

```python
ocr_tool = PaddleOCRTool(device="cpu")  # 使用CPU
```

---

### 4. 内存不足 (MemoryError)

**症状**:

```
MemoryError: Unable to allocate...
```

**解决方案**:

**方法1**: 降低DPI

```bash
python paddle_ocr_tool.py doc.pdf --dpi 150
```

**方法2**: 启用压缩

```bash
python paddle_ocr_tool.py doc.pdf --compress
```

**方法3**: 分批处理

```python
from paddleocr_toolkit.core import streaming_utils

for batch in streaming_utils.batch_pages_generator("large.pdf", batch_size=5):
    # 处理小批次
    pass
```

---

### 5. UnicodeEncodeError (Windows)

**症状**:

```
UnicodeEncodeError: 'cp950' codec can't encode character
```

**解决方案**:

**方法1**: 设置环境变量

```powershell
$env:PYTHONIOENCODING = "utf-8"
```

**方法2**: 在代码中设置

```python
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

**方法3**: 输出到文件

```bash
python paddle_ocr_tool.py doc.pdf > output.txt
```

---

## 🔍 调试技巧

### 启用详细日志

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

### 检查OCR结果

```python
results = ocr_tool.process_image("test.jpg")

print(f"找到 {len(results)} 个文字块")
for i, result in enumerate(results):
    print(f"{i+1}. 文字: {result.text}")
    print(f"   信心度: {result.confidence:.1%}")
    print(f"   位置: {result.bbox}")
```

### 性能分析

```python
import time
import psutil
import os

process = psutil.Process(os.getpid())

# 性能监控
start_time = time.time()
start_mem = process.memory_info().rss / 1024 / 1024

results, _ = ocr_tool.process_pdf("doc.pdf")

elapsed = time.time() - start_time
peak_mem = process.memory_info().rss / 1024 / 1024

print(f"耗时: {elapsed:.2f}秒")
print(f"内存: {peak_mem - start_mem:.1f}MB")
```

---

## 🛠️ 配置问题

### 配置文件不生效

**检查配置**:

```python
from paddleocr_toolkit.core import load_config

config = load_config("config.yaml")
print(config)
```

**常见问题**:

- YAML格式错误
- 文件路径错误
- 权限问题

**验证YAML**:

```python
import yaml

with open("config.yaml") as f:
    try:
        config = yaml.safe_load(f)
        print("YAML格式正确")
    except yaml.YAMLError as e:
        print(f"YAML错误: {e}")
```

---

## 📊 质量问题

### OCR识别率低

**诊断**:

```python
def diagnose_quality(results):
    avg_conf = sum(r.confidence for page in results for r in page) / \
               sum(len(page) for page in results)
    
    print(f"平均信心度: {avg_conf:.1%}")
    
    if avg_conf < 0.7:
        print("建议:")
        print("1. 提高DPI到300")
        print("2. 使用hybrid模式")
        print("3. 进行图片预处理")
```

**改进方案**:

1. **提高DPI**:

```python
results, _ = ocr_tool.process_pdf("doc.pdf", dpi=300)
```

2. **预处理**:

```python
from paddleocr_toolkit.processors import ImagePreprocessor

preprocessor = ImagePreprocessor()
clean_img = preprocessor.denoise(image)
binary_img = preprocessor.binarize(clean_img)
```

3. **换模式**:

```python
ocr_tool = PaddleOCRTool(mode="hybrid")
```

---

## ⚠️ 运行时错误

### 模块初始化失败

**错误信息**:

```
RuntimeError: (PreconditionNotMet) Cannot load cudnn shared library
```

**解决方案**:

```bash
# 重新安装PaddlePaddle
pip uninstall paddlepaddle-gpu
pip install paddlepaddle-gpu
```

### 模型下载失败

**错误信息**:

```
URLError: <urlopen error [Errno 11001] getaddrinfo failed>
```

**解决方案**:

1. **设置代理**:

```python
import os
os.environ['HTTP_PROXY'] = 'http://proxy:port'
os.environ['HTTPS_PROXY'] = 'http://proxy:port'
```

2. **手动下载模型**:
访问 PaddleOCR 模型库下载

---

## 🔄 重启和重置

### 清理缓存

```bash
# Windows
del /s /q __pycache__
del /s /q .pytest_cache
del /s /q .mypy_cache

# Linux/Mac
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name ".pytest_cache" -exec rm -rf {} +
```

### 重新安装

```bash
# 完全卸载
pip uninstall -y paddleocr paddlepaddle paddlepaddle-gpu

# 重新安装
pip install paddleocr paddlepaddle-gpu
```

---

## 📞 获取帮助

### 提交问题报告

包含以下信息：

```python
import sys
import platform
import paddleocr

print(f"Python版本: {sys.version}")
print(f"平台: {platform.platform()}")
print(f"PaddleOCR版本: {paddleocr.__version__}")
print(f"错误信息: [粘贴完整错误]")
```

### 社区资源

- 📖 [官方文档](../README.md)
- 💬 [GitHub Issues](https://github.com/danwin47-sys/paddleocr-toolkit/issues)
- 📚 [FAQ](FAQ.md)
- 🎯 [最佳实践](BEST_PRACTICES.md)

---

## 🎯 预防措施

### 环境设置

```bash
# 创建虚拟环境
python -m venv ocr_env

# Windows
ocr_env\Scripts\activate

# Linux/Mac
source ocr_env/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 测试安装

```python
# test_installation.py
try:
    from paddle_ocr_tool import PaddleOCRTool
    print("[OK] PaddleOCR工具")
    
    import fitz
    print("[OK] PyMuPDF")
    
    import paddleocr
    print("[OK] PaddleOCR")
    
    print("\n所有依赖已正确安装！")
    
except ImportError as e:
    print(f"[ERROR] 缺少依赖: {e}")
```

---

## 📋 检查清单

运行以下检查：

- [ ] Python版本 >= 3.8
- [ ] PaddleOCR已安装
- [ ] PyMuPDF已安装
- [ ] 文件路径正确
- [ ] 足够的磁盘空间
- [ ] 足够的内存
- [ ] GPU驱动正确（如使用）

---

**更新时间**: 2024-12-15  
**版本**: v1.0.0

**仍有问题？提交Issue获取帮助！** 🆘
