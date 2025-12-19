# 🎨 PaddleOCR Toolkit - 示例專案集合

> **超酷的實用工具展示 PaddleOCR 的強大功能！**

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

## 📚 目錄

- [🚀 快速開始](#-快速開始)
- [📱 發票掃描器](#-發票掃描器)
- [⚡ 效能基準測試](#-效能基準測試)
- [🎨 CLI美化模組](#-cli美化模組)
- [💡 更多示例](#-更多示例)

---

## 🚀 快速開始

### 安裝依賴

```bash
# 基本依賴
pip install paddleocr PyMuPDF pillow

# 美化輸出（推薦）
pip install rich

# 效能監控
pip install psutil
```

### 執行示例

```bash
# 進入examples目錄
cd examples

# 試用發票掃描器
python receipt_scanner.py ../test_receipt.jpg

# 執行效能測試
python benchmark.py

# 試用CLI美化
python -c "from paddleocr_toolkit.cli.rich_ui import *; print_logo()"
```

---

## 📱 發票掃描器

### 🎯 功能特色

自動從發票圖片中智慧提取關鍵資訊：

- 💰 **金額識別** - 自動找出總金額
- 📅 **日期提取** - 支援多種日期格式
- 🏪 **商家識別** - 提取商家名稱
- 📦 **商品列表** - 列出購買專案
- 📂 **批次處理** - 一次處理整個資料夾
- 💾 **JSON輸出** - 結構化資料儲存

### 📸 使用範例

#### 單個發票掃描

```bash
python receipt_scanner.py receipt.jpg
```

**輸出**:

```
🔧 初始化 OCR 引擎...
✅ OCR 引擎就緒！

📷 掃描發票: receipt.jpg

==================================================
📋 發票掃描結果
==================================================
🏪 商家: 全聯福利中心
📅 日期: 2024/12/14
💰 總金額: NT$ 1,234.00

📦 商品專案 (5 項):
   1. 蘋果
   2. 香蕉
   3. 牛奶
   4. 麵包
   5. 雞蛋
==================================================

💾 結果已儲存至: receipt_result.json
```

#### 批次處理

```bash
python receipt_scanner.py receipts_folder/
```

**輸出**:

```
📂 找到 15 個圖片檔案

[1/15]
📷 掃描發票: receipt_001.jpg
...

==================================================
📊 批次處理摘要
==================================================
總發票數: 15
成功提取金額: 14/15
總金額: NT$ 12,450.00
==================================================
```

### 📊 JSON輸出格式

```json
{
  "file": "receipt.jpg",
  "scan_time": "2024-12-15T00:45:00",
  "total_amount": 1234.0,
  "date": "2024/12/14",
  "merchant": "全聯福利中心",
  "items": ["蘋果", "香蕉", "牛奶", "麵包", "雞蛋"],
  "raw_text": "完整OCR文字..."
}
```

### 💡 使用技巧

**提高準確度**:

1. 使用清晰的照片
2. 確保發票平整
3. 充足的光線
4. 避免反光

**批次處理建議**:

```bash
# 組織發票資料夾
receipts/
  ├── 2024-01/
  ├── 2024-02/
  └── 2024-03/

# 按月份處理
python receipt_scanner.py receipts/2024-01/
```

---

## ⚡ 效能基準測試

### 🎯 功能特色

專業級效能測試工具：

- 📈 **多場景測試** - 4種預設測試
- ⏱️ **速度測量** - 精確到毫秒
- 💾 **記憶體監控** - 追蹤記憶體使用
- 📊 **美化輸出** - Rich表格展示
- 🎯 **統計分析** - 自動計算平均值

### 📸 使用範例

```bash
python benchmark.py
```

**輸出**:

```
🚀 PaddleOCR Toolkit 效能基準測試
==================================================

📋 將執行 4 個測試場景
⚠️  這可能需要幾分鐘時間...

==================================================
場景 1/4
==================================================

🧪 測試: test_10_pages.pdf
   模式: basic, DPI: 150

   ⏱️  初始化OCR引擎...
   📄 處理PDF...
   ✅ 完成: 12.50s (1.25s/頁)
   💾 記憶體: 245.3MB

... (更多測試) ...

⚡ 效能基準測試結果
╭────────────┬──────┬─────────┬────────────┬──────────┬─────────╮
│ 測試       │ 頁數 │ 總時間  │ 速度       │ 記憶體   │ 文字數  │
├────────────┼──────┼─────────┼────────────┼──────────┼─────────┤
│ basic/150  │   10 │  12.50s │  1.25s/頁  │  245.3MB │   1,450 │
│ basic/200  │   10 │  15.30s │  1.53s/頁  │  312.7MB │   1,892 │
│ hybrid/150 │   10 │  18.20s │  1.82s/頁  │  389.1MB │   1,654 │
│ basic/150  │   50 │  62.50s │  1.25s/頁  │  267.8MB │   7,234 │
╰────────────┴──────┴─────────┴────────────┴──────────┴─────────╯

📊 測試總結:
   平均速度: 1.46s/頁
   平均記憶體: 303.7MB
   最快測試: basic/150
   最省記憶體: basic/150
```

### 🔧 自定義測試

修改 `benchmark.py` 中的 `test_scenarios`:

```python
test_scenarios = [
    # (頁數, 模式, DPI)
    (5, "basic", 150),      # 小型檔案
    (20, "basic", 200),     # 中型檔案
    (100, "hybrid", 150),   # 大型檔案
    (10, "structure", 300), # 高解析度
]
```

### 📊 效能最佳化建議

根據測試結果：

**速度優先**:

- 使用 `basic` 模式
- DPI 設定 150
- GPU 加速

**質量優先**:

- 使用 `hybrid` 模式
- DPI 設定 200-300
- 後處理開啟

**平衡配置**:

- `basic` 模式 + DPI 200
- 適合大多數場景

---

## 🎨 CLI美化模組

### 🎯 功能特色

打造專業級命令列介面：

- 🖼️ **ASCII Logo** - 炫酷的開場
- 🎨 **彩色輸出** - 視覺化狀態
- 📊 **美化表格** - Rich表格展示
- 💫 **進度條** - 即時進度追蹤
- ✨ **狀態面板** - 專業摘要顯示

### 📸 快速開始

```python
from paddleocr_toolkit.cli.rich_ui import *

# 顯示Logo
print_logo()

# 顯示橫幅
print_banner()

# 狀態訊息
print_success("OCR處理完成！")
print_error("找不到檔案")
print_warning("DPI設定較低")
print_info("開始處理PDF...")
```

### 🎨 進階使用

#### 1. 建立結果表格

```python
# 準備資料
results_data = [
    (1, 145, 0.95),  # (頁數, 文字數, 信心度)
    (2, 132, 0.88),
    (3, 167, 0.92),
]

# 建立並顯示表格
table = create_results_table(results_data)
console.print(table)
```

**輸出**:

```
📊 OCR 處理結果統計
╭──────┬────────────┬──────────────┬──────────╮
│ 頁數 │ 識別文字數 │ 平均信心度   │ 狀態     │
├──────┼────────────┼──────────────┼──────────┤
│  1   │    145     │    95.0%     │ 🟢 優秀  │
│  2   │    132     │    88.0%     │ 🟡 良好  │
│  3   │    167     │    92.0%     │ 🟢 優秀  │
╰──────┴────────────┴──────────────┴──────────╯
```

#### 2. 顯示效能摘要

```python
stats = {
    'total_pages': 10,
    'total_time': 25.5,
    'avg_time_per_page': 2.55,
    'peak_memory_mb': 389.2,
    'total_texts': 1847
}

print_performance_summary(stats)
```

**輸出**:

```
╔══════════════ 🎯 效能摘要 ══════════════╗
║                                          ║
║  📄 總頁數: 10                           ║
║  ⏱️  總時間: 25.50s                      ║
║  ⚡ 平均速度: 2.55s/頁                   ║
║  💾 峰值記憶體: 389.2MB                  ║
║  📝 識別文字: 1847個                     ║
║                                          ║
╚══════════════════════════════════════════╝
```

#### 3. 進度條

```python
# 建立進度條
with create_progress_bar(total=100, description="處理中") as progress:
    task = progress.add_task("處理PDF", total=100)
    
    for i in range(100):
        # 處理工作
        process_page(i)
        progress.update(task, advance=1)
```

### 🎨 視覺效果說明

| 狀態 | 顏色 | 圖示 | 用途 |
|------|------|------|------|
| 成功 | 綠色 | ✅ | 操作完成 |
| 錯誤 | 紅色 | ❌ | 發生錯誤 |
| 警告 | 黃色 | ⚠️ | 需要注意 |
| 資訊 | 藍色 | ℹ️ | 一般訊息 |

### 💡 整合到主程式

```python
# 在 paddle_ocr_tool.py 中使用

from paddleocr_toolkit.cli.rich_ui import *

def main():
    # 顯示Logo
    print_logo()
    print_banner()
    
    # 處理過程
    print_info("開始初始化OCR引擎...")
    ocr_tool = PaddleOCRTool()
    print_success("OCR引擎初始化完成！")
    
    # 處理PDF
    print_info(f"處理PDF: {pdf_path}")
    results = ocr_tool.process_pdf(pdf_path)
    
    # 顯示結果
    table = create_results_table(...)
    console.print(table)
    
    print_success("處理完成！")
```

---

## 💡 更多示例

### 即將推出

- 📚 **書籍數位化器** - 掃描書頁並整理章節
- 🎫 **名片掃描器** - 提取聯絡資訊
- 📄 **檔案分類器** - 自動分類檔案型別
- 🔍 **檔案搜尋引擎** - OCR+全文檢索

### 社群貢獻

歡迎提交你的示例專案！

**提交方式**:

1. Fork 專案
2. 建立你的示例
3. 提交 Pull Request

**示例要求**:

- 完整的程式碼
- 清晰的說明文件
- 使用範例
- (可選) 測試案例

---

## 🎯 使用場景

### 發票掃描器適合

- 📱 個人記帳管理
- 💼 報帳流程自動化
- 📊 消費資料分析
- 🏢 財務檔案處理

### 效能測試適合

- ⚡ 系統效能調優
- 📈 容量規劃
- 🔬 配置最佳化
- 📊 效能報告生成

### CLI美化適合

- 🎨 提升使用者體驗
- 💼 專業工具開發
- 📊 即時狀態展示
- ✨ 產品Demo

---

## 📚 學習資源

### 文件

- [主要README](../README.md)
- [CHANGELOG](../CHANGELOG.md)
- [開發路線圖](../artifacts/plans/ROADMAP_v1.1_to_v2.0.md)

### 教程

- 快速入門指南 (即將推出)
- API使用手冊 (即將推出)
- 最佳實踐指南 (即將推出)

---

## ❓ 常見問題

### Q: Rich庫是必需的嗎？

**A**: 不是。所有工具都有降級方案，沒有Rich時會使用純文字輸出。但強烈推薦安裝以獲得最佳體驗。

### Q: 發票掃描器支援哪些圖片格式？

**A**: 支援 JPG, PNG, JPEG 等常見格式。建議使用清晰、光線充足的照片。

### Q: 效能測試會修改我的PDF嗎？

**A**: 不會。測試使用臨時生成的PDF，不會影響你的檔案。

### Q: 如何提高OCR準確度？

**A**:

1. 提高DPI (200-300)
2. 使用高質量圖片
3. 確保文字清晰
4. 選擇合適的模式

### Q: 可以在生產環境使用嗎？

**A**: 可以！這些示例展示了生產級的程式碼質量，可以直接使用或作為基礎擴充套件。

---

## 🤝 貢獻

發現問題或有改進建議？

- 🐛 [報告Bug](https://github.com/danwin47-sys/paddleocr-toolkit/issues)
- 💡 [提出功能](https://github.com/danwin47-sys/paddleocr-toolkit/issues)
- 🔧 [提交PR](https://github.com/danwin47-sys/paddleocr-toolkit/pulls)

---

## 📄 授權

MIT License

---

## 🌟 致謝

- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - 強大的OCR引擎
- [Rich](https://github.com/Textualize/rich) - 美麗的終端輸出
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) - PDF處理

---

**建立時間**: 2024-12-15  
**最後更新**: 2024-12-15  
**版本**: v1.0.0  
**狀態**: ✅ 完成

**Happy Coding! 🎉**
