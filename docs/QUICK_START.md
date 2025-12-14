# 🚀 快速入門指南

歡迎使用 PaddleOCR Toolkit！這份指南將幫助你在 5 分鐘內開始使用。

---

## 📦 安裝

### 方法1: 使用 pip (推薦)

```bash
pip install paddleocr PyMuPDF pillow
```

### 方法2: 從源碼安裝

```bash
git clone https://github.com/danwin47-sys/paddleocr-toolkit.git
cd paddleocr-toolkit
pip install -r requirements.txt
```

---

## 🎯 第一個OCR程序

### 1. 基本圖片OCR

```python
from paddle_ocr_tool import PaddleOCRTool

# 初始化
ocr_tool = PaddleOCRTool(mode="basic")

# 處理圖片
results = ocr_tool.process_image("document.jpg")

# 顯示結果
for result in results:
    print(f"文字: {result.text}")
    print(f"信心度: {result.confidence:.2%}")
```

### 2. PDF轉文字

```python
from paddle_ocr_tool import PaddleOCRTool

# 初始化
ocr_tool = PaddleOCRTool(mode="basic", dpi=200)

# 處理PDF
all_results, pdf_gen = ocr_tool.process_pdf("document.pdf")

# 提取所有文字
full_text = ocr_tool.get_text(all_results)
print(full_text)
```

### 3. 生成可搜尋PDF

```python
from paddle_ocr_tool import PaddleOCRTool

ocr_tool = PaddleOCRTool(mode="basic")

# 生成可搜尋PDF
ocr_tool.process_pdf(
    "input.pdf",
    output_searchable_pdf="output_searchable.pdf"
)
```

---

## 🎨 CLI 使用

### 基本命令

```bash
# 處理圖片
python paddle_ocr_tool.py document.jpg

# 處理PDF
python paddle_ocr_tool.py document.pdf

# 指定輸出格式
python paddle_ocr_tool.py document.pdf --format md json html

# 生成可搜尋PDF
python paddle_ocr_tool.py document.pdf --searchable
```

### 進階選項

```bash
# 使用結構化模式
python paddle_ocr_tool.py document.pdf --mode structure

# 設定DPI
python paddle_ocr_tool.py document.pdf --dpi 300

# 使用GPU
python paddle_ocr_tool.py document.pdf --device gpu

# 翻譯功能
python paddle_ocr_tool.py document.pdf --translate en --target-lang zh

# 批次處理
python paddle_ocr_tool.py input_folder/ --batch
```

---

## 📖 常用模式

### basic模式（最快）

```python
ocr_tool = PaddleOCRTool(mode="basic")
```

- ⚡ 速度最快
- 📝 適合純文字文件
- 💾 記憶體使用最少

### structure模式（最準確）

```python
ocr_tool = PaddleOCRTool(mode="structure")
```

- 🎯 識別表格和版面
- 📊 保留文件結構
- 🔍 適合複雜文件

### hybrid模式（平衡）

```python
ocr_tool = PaddleOCRTool(mode="hybrid")
```

- ⚖️ 速度與準確度平衡
- 📄 適合混合文件
- 💡 推薦日常使用

---

## 💡 快速技巧

### 提高準確度

```python
ocr_tool = PaddleOCRTool(
    mode="hybrid",
    dpi=300,           # 提高解析度
    device="gpu"       # 使用GPU加速
)
```

### 批次處理

```python
from pathlib import Path

pdf_files = Path("pdfs/").glob("*.pdf")

for pdf_file in pdf_files:
    results, _ = ocr_tool.process_pdf(str(pdf_file))
    # 處理結果...
```

### 記憶體優化

```python
# 使用串流模式處理大檔案
ocr_tool = PaddleOCRTool(
    mode="basic",
    enable_streaming=True  # 減少記憶體使用
)
```

---

## 🔧 配置文件

創建 `config.yaml`:

```yaml
ocr:
  mode: hybrid
  device: gpu
  dpi: 200

output:
  format: md
  directory: ./output

compression:
  enable: true
  jpeg_quality: 85
```

使用配置:

```bash
python paddle_ocr_tool.py document.pdf --config config.yaml
```

---

## 📊 輸出格式

### Markdown

```bash
python paddle_ocr_tool.py doc.pdf --format md
```

### JSON

```bash
python paddle_ocr_tool.py doc.pdf --format json
```

### HTML

```bash
python paddle_ocr_tool.py doc.pdf --format html
```

### 多種格式

```bash
python paddle_ocr_tool.py doc.pdf --format md json html
```

---

## ❓ 常見問題

### Q: GPU加速不工作？

**A**: 確認已安裝GPU版本的PaddlePaddle:

```bash
python -m pip install paddlepaddle-gpu
```

### Q: 記憶體不足？

**A**: 降低DPI或啟用壓縮:

```bash
python paddle_ocr_tool.py doc.pdf --dpi 150 --compress
```

### Q: 中文識別不準確？

**A**: 使用更高的DPI和hybrid模式:

```bash
python paddle_ocr_tool.py doc.pdf --mode hybrid --dpi 300
```

---

## 🎓 下一步

- 📖 閱讀 [API文檔](API_GUIDE.md)
- 🔧 查看 [最佳實踐](BEST_PRACTICES.md)
- 💡 試用 [示例項目](../examples/README.md)
- 🐛 [故障排除](TROUBLESHOOTING.md)

---

**Happy OCR! 🎉**
