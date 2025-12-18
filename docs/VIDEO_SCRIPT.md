# 🎬 快速入門影片腳本

**時長**: 3-5 分鐘  
**目標**: 新使用者快速上手

---

## 場景 1: 介紹 (30 秒)

**畫面**: Logo + 專案名稱

**旁白**:
> 「歡迎使用 PaddleOCR Toolkit - 一個專業級的 OCR 文件辨識與處理工具。
> 今天我們將在 5 分鐘內學會如何使用它。」

**字幕**:

- PaddleOCR Toolkit
- 專業級 OCR 工具
- 簡單易用

---

## 場景 2: 安裝 (45 秒)

**畫面**: 終端機/命令提示字元

**操作**:

```bash
pip install paddleocr PyMuPDF pillow
```

**旁白**:
> 「安裝非常簡單，只需一行命令即可安裝所有依賴項。」

**字幕**:

- 一鍵安裝
- 自動處理依賴

---

## 場景 3: 基本使用 (90 秒)

### 3.1 處理圖片 (30 秒)

**畫面**: 程式碼編輯器

**程式碼展示**:

```python
from paddle_ocr_tool import PaddleOCRTool

# 初始化
ocr_tool = PaddleOCRTool(mode="basic")

# 處理圖片
results = ocr_tool.process_image("document.jpg")

# 顯示結果
for result in results:
    print(result.text)
```

**旁白**:
> 「處理圖片只需 3 行程式碼。初始化工具，處理圖片，取得結果。就這麼簡單！」

### 3.2 處理 PDF (30 秒)

**程式碼展示**:

```python
# 處理 PDF
all_results, _ = ocr_tool.process_pdf("document.pdf")

# 提取文字
text = ocr_tool.get_text(all_results)
print(text)
```

**旁白**:
> 「處理 PDF 同樣簡單。工具會自動處理每一頁，並提取所有文字。」

### 3.3 生成可搜尋 PDF (30 秒)

**程式碼展示**:

```python
# 生成可搜尋 PDF
ocr_tool.process_pdf(
    "input.pdf",
    output_searchable_pdf="searchable.pdf"
)
```

**旁白**:
> 「甚至可以一鍵生成可搜尋的 PDF，讓掃描檔案變得可搜尋。」

**畫面**: 展示生成的 PDF，演示搜尋功能

---

## 場景 4: CLI 使用 (60 秒)

**畫面**: 終端機

**操作演示**:

```bash
# 基本使用
python paddle_ocr_tool.py document.pdf

# 指定格式
python paddle_ocr_tool.py document.pdf --format md json

# 生成可搜尋 PDF
python paddle_ocr_tool.py input.pdf --searchable

# 批次處理
python paddle_ocr_tool.py pdfs/ --batch
```

**旁白**:
> 「更喜歡命令列？我們也提供了功能完整的 CLI 工具。
> 可以指定輸出格式，生成可搜尋 PDF，甚至批次處理整個資料夾。」

---

## 場景 5: 範例工具展示 (60 秒)

### 5.1 發票掃描器 (20 秒)

**畫面**: 執行發票掃描器

```bash
python examples/receipt_scanner.py receipt.jpg
```

**展示輸出**:

- 自動提取的金額
- 日期
- 商家名稱

**旁白**:
> 「我們還提供了實用的範例工具，比如這個發票掃描器，
> 可以自動提取金額、日期和商家資訊。」

### 5.2 名片掃描器 (20 秒)

**畫面**: 執行名片掃描器

```bash
python examples/business_card_scanner.py card.jpg
```

**展示**:

- 提取的聯絡資訊
- 自動生成的 vCard

**旁白**:
> 「名片掃描器可以提取聯絡資訊，並自動生成 vCard 檔案，
> 方便載入進通訊錄。」

### 5.3 效能測試 (20 秒)

**畫面**: 執行效能測試

```bash
python examples/benchmark.py
```

**展示**: 效能測試表格

**旁白**:
> 「還有效能測試工具，幫助你優化設定，達到最佳效能。」

---

## 場景 6: 進階功能 (30 秒)

**畫面**: 程式碼範例

**功能列表**:

- 多種 OCR 模式 (basic, structure, hybrid)
- GPU 加速
- 批次處理
- 圖片預處理
- 多種輸出格式

**旁白**:
> 「PaddleOCR Toolkit 還支援多種進階功能：
> 多種 OCR 模式、GPU 加速、批次處理等，
> 滿足各種專業需求。」

---

## 場景 7: 總結 (30 秒)

**畫面**: 功能總覽

**要點**:

- ✅ 簡單易用
- ✅ 功能強大
- ✅ 效能優異
- ✅ 文件完善

**旁白**:
> 「PaddleOCR Toolkit - 簡單易用，功能強大，效能優異。
> 完整的文件和範例讓你快速上手。
> 現在就開始你的 OCR 之旅吧！」

**字幕**:

- GitHub: github.com/danwin47-sys/paddleocr-toolkit
- 文件: 完整指南
- 範例: 4 個實用工具

**結束畫面**: Logo + 連結

---

## 📝 拍攝提示

**畫面品質**:

- 1080p 或更高
- 清晰的字體
- 簡潔的介面

**節奏**:

- 快速但不急促
- 每個場景間有短暫停頓
- 重要部分放慢

**音效**:

- 輕鬆的背景音樂
- 清晰的旁白
- 適當的提示音

**字幕**:

- 關鍵資訊高亮
- 程式碼部分清晰可讀
- 雙語字幕（中英文）

---

**製作時長**: 預計 2-3 小時
**效果**: 專業演示影片
