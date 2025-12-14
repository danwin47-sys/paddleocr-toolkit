# 🎬 快速开始视频脚本

**时长**: 3-5分钟  
**目标**: 新用户快速上手

---

## 场景1: 介绍 (30秒)

**画面**: Logo + 项目名称

**旁白**:
> "欢迎使用 PaddleOCR Toolkit - 一个专业级的OCR文件识别与处理工具。
> 今天我们将在5分钟内学会如何使用它。"

**字幕**:

- PaddleOCR Toolkit
- 专业级OCR工具
- 简单易用

---

## 场景2: 安装 (45秒)

**画面**: 终端/命令提示符

**操作**:

```bash
pip install paddleocr PyMuPDF pillow
```

**旁白**:
> "安装非常简单，只需一行命令即可安装所有依赖。"

**字幕**:

- 一键安装
- 自动处理依赖

---

## 场景3: 基本使用 (90秒)

### 3.1 处理图片 (30秒)

**画面**: 代码编辑器

**代码展示**:

```python
from paddle_ocr_tool import PaddleOCRTool

# 初始化
ocr_tool = PaddleOCRTool(mode="basic")

# 处理图片
results = ocr_tool.process_image("document.jpg")

# 显示结果
for result in results:
    print(result.text)
```

**旁白**:
> "处理图片只需3行代码。初始化工具，处理图片，获取结果。就这么简单！"

### 3.2 处理PDF (30秒)

**代码展示**:

```python
# 处理PDF
all_results, _ = ocr_tool.process_pdf("document.pdf")

# 提取文字
text = ocr_tool.get_text(all_results)
print(text)
```

**旁白**:
> "处理PDF同样简单。工具会自动处理每一页，并提取所有文字。"

### 3.3 生成可搜索PDF (30秒)

**代码展示**:

```python
# 生成可搜索PDF
ocr_tool.process_pdf(
    "input.pdf",
    output_searchable_pdf="searchable.pdf"
)
```

**旁白**:
> "甚至可以一键生成可搜索的PDF，让扫描文件变得可搜索。"

**画面**: 展示生成的PDF，演示搜索功能

---

## 场景4: CLI使用 (60秒)

**画面**: 终端

**操作演示**:

```bash
# 基本使用
python paddle_ocr_tool.py document.pdf

# 指定格式
python paddle_ocr_tool.py document.pdf --format md json

# 生成可搜索PDF
python paddle_ocr_tool.py input.pdf --searchable

# 批量处理
python paddle_ocr_tool.py pdfs/ --batch
```

**旁白**:
> "更喜欢命令行？我们也提供了功能完整的CLI工具。
> 可以指定输出格式，生成可搜索PDF，甚至批量处理整个文件夹。"

---

## 场景5: 示例工具展示 (60秒)

### 5.1 发票扫描器 (20秒)

**画面**: 运行发票扫描器

```bash
python examples/receipt_scanner.py receipt.jpg
```

**展示输出**:

- 自动提取的金额
- 日期
- 商家名称

**旁白**:
> "我们还提供了实用的示例工具，比如这个发票扫描器，
> 可以自动提取金额、日期和商家信息。"

### 5.2 名片扫描器 (20秒)

**画面**: 运行名片扫描器

```bash
python examples/business_card_scanner.py card.jpg
```

**展示**:

- 提取的联系信息
- 自动生成的vCard

**旁白**:
> "名片扫描器可以提取联系信息，并自动生成vCard文件，
> 方便导入到通讯录。"

### 5.3 性能测试 (20秒)

**画面**: 运行性能测试

```bash
python examples/benchmark.py
```

**展示**: 性能测试表格

**旁白**:
> "还有性能测试工具，帮助你优化配置，达到最佳性能。"

---

## 场景6: 高级功能 (30秒)

**画面**: 代码示例

**功能列表**:

- 多种OCR模式 (basic, structure, hybrid)
- GPU加速
- 批量处理
- 图片预处理
- 多种输出格式

**旁白**:
> "PaddleOCR Toolkit还支持多种高级功能：
> 多种OCR模式、GPU加速、批量处理等，
> 满足各种专业需求。"

---

## 场景7: 总结 (30秒)

**画面**: 功能总览

**要点**:

- ✅ 简单易用
- ✅ 功能强大
- ✅ 性能优异
- ✅ 文档完善

**旁白**:
> "PaddleOCR Toolkit - 简单易用，功能强大，性能优异。
> 完整的文档和示例让你快速上手。
> 现在就开始你的OCR之旅吧！"

**字幕**:

- GitHub: github.com/danwin47-sys/paddléocr-toolkit
- 文档: 完整指南
- 示例: 4个实用工具

**结束画面**: Logo + 链接

---

## 📝 拍摄提示

**画面质量**:

- 1080p或更高
- 清晰的字体
- 简洁的界面

**节奏**:

- 快速但不急促
- 每个场景间有短暂停顿
- 重要部分放慢

**音效**:

- 轻松的背景音乐
- 清晰的旁白
- 适当的提示音

**字幕**:

- 关键信息高亮
- 代码部分清晰可读
- 双语字幕（中英文）

---

**制作时长**: 预计2-3小时
**效果**: 专业演示视频
