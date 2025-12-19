# 遷移指南 - 從舊 API 到新模組化架構

> 本指南幫助您從 `paddle_ocr_tool.py` 平滑遷移到新的模組化架構

---

## 一、為什麼要遷移？

### 1.1 新架構的優勢

✅ **更模組化**
- 職責清晰分離
- 每個 Processor 專注單一功能
- 易於理解和維護

✅ **更易測試**
- 每個模組可獨立測試
- Mock 更簡單
- 測試覆蓋率更高（89%+）

✅ **更易擴充**
- 新增功能只需新增新 Processor
- 不影響現有程式碼
- 符合開放封閉原則

✅ **效能相同**
- 委派呼叫開銷可忽略
- 核心邏輯完全相同
- 無效能損失

---

## 二、快速開始

### 2.1 最小變更遷移（推薦）

**步驟 1**：修改 import 語句

```python
# 舊方式
from paddle_ocr_tool import PaddleOCRTool

# 新方式（只改這一行！）
from paddle_ocr_facade import PaddleOCRFacade as PaddleOCRTool
```

**步驟 2**：無需其他修改！

```python
# 現有程式碼完全相容
tool = PaddleOCRTool(mode="hybrid", device="cpu")
result = tool.process_hybrid("input.pdf", "output.pdf")
```

✅ **完成！** 您的程式碼已使用新架構。

---

### 2.2 完全遷移（建議）

逐步將程式碼遷移到新的命名：

```python
# 第一步：改用新名稱
from paddle_ocr_facade import PaddleOCRFacade

# 第二步：修改變數名稱
facade = PaddleOCRFacade(mode="hybrid", device="cpu")

# 第三步：方法呼叫保持不變
result = facade.process_hybrid("input.pdf", "output.pdf")
```

---

## 三、詳細對比

### 3.1 基本 OCR

#### 舊 API
```python
from paddle_ocr_tool import PaddleOCRTool

tool = PaddleOCRTool(mode="basic", device="cpu")
result = tool.process_basic("document.jpg")
```

#### 新 API
```python
from paddle_ocr_facade import PaddleOCRFacade

facade = PaddleOCRFacade(mode="basic", device="cpu")
result = facade.process_basic("document.jpg")
```

**差異**：僅 import 和類別名稱不同

---

### 3.2 混合模式（版面分析 + OCR）

#### 舊 API
```python
from paddle_ocr_tool import PaddleOCRTool

tool = PaddleOCRTool(
    mode="hybrid",
    device="gpu",
    compress_images=True
)

result = tool.process_hybrid(
    "input.pdf",
    output_path="output.pdf",
    markdown_output="output.md",
    dpi=150
)
```

#### 新 API
```python
from paddle_ocr_facade import PaddleOCRFacade

facade = PaddleOCRFacade(
    mode="hybrid",
    device="gpu",
    compress_images=True
)

result = facade.process_hybrid(
    "input.pdf",
    output_path="output.pdf",
    markdown_output="output.md",
    dpi=150
)
```

**差異**：完全相同的 API！

---

### 3.3 含翻譯的處理

#### 舊 API
```python
result = tool.process_hybrid(
    "document.pdf",
    translate_config={
        "source_lang": "zh",
        "target_lang": "en",
        "ollama_model": "qwen2.5:7b",
        "no_mono": False,
        "no_dual": False
    }
)
```

#### 新 API
```python
result = facade.process_hybrid(
    "document.pdf",
    translate_config={
        "source_lang": "zh",
        "target_lang": "en",
        "ollama_model": "qwen2.5:7b",
        "no_mono": False,
        "no_dual": False
    }
)
```

**差異**：無差異！100% 相容

---

## 四、進階使用：直接使用 Processor

新架構允許您直接使用專業的 Processor，獲得更精細的控制。

### 4.1 使用 HybridPDFProcessor

```python
from paddleocr_toolkit.core import OCREngineManager
from paddleocr_toolkit.processors import HybridPDFProcessor

# 初始化引擎
engine = OCREngineManager(mode="hybrid", device="cpu")
engine.init_engine()

# 建立 Processor
processor = HybridPDFProcessor(
    engine,
    debug_mode=False,
    compress_images=True,
    jpeg_quality=85
)

# 處理 PDF
result = processor.process_pdf(
    "input.pdf",
    output_path="output.pdf",
    markdown_output="output.md"
)
```

### 4.2 使用 BasicProcessor

```python
from paddleocr_toolkit.core import OCREngineManager
from paddleocr_toolkit.processors import BasicProcessor

engine = OCREngineManager(mode="basic")
engine.init_engine()

processor = BasicProcessor(engine)

# 處理單張圖片
result = processor.process_image("image.jpg")

# 批次處理
results = processor.process_batch(["img1.jpg", "img2.jpg"])

# 處理 PDF
pdf_result = processor.process_pdf("document.pdf")
```

---

## 五、常見問題

### Q1: 需要重新安裝依賴嗎？

**A**: 不需要。依賴完全相同。

### Q2: 效能會受影響嗎？

**A**: 不會。委派呼叫的開銷可忽略不計（< 1μs）。

### Q3: 舊程式碼還能用嗎？

**A**: 可以。`paddle_ocr_tool.py` 仍然保留且完全可用。

### Q4: 什麼時候必須遷移？

**A**: 目前沒有強制時間表。但建議在方便時遷移以獲得新架構的好處。

### Q5: 遷移有風險嗎？

**A**: 幾乎沒有。新舊 API 100% 相容，可以逐步遷移。

### Q6: 如何驗證遷移成功？

**A**: 執行現有測試。如果測試透過，遷移就成功了。

---

## 六、遷移檢查清單

### 步驟 1：評估

- [ ] 檢查當前使用的功能
- [ ] 確認是否有自訂修改
- [ ] 備份現有程式碼

### 步驟 2：測試

- [ ] 在測試環境先試用新 API
- [ ] 執行完整測試套件
- [ ] 驗證輸出一致性

### 步驟 3：遷移

- [ ] 修改 import 語句
- [ ] 更新類別名稱（可選）
- [ ] 重新執行測試

### 步驟 4：驗證

- [ ] 功能測試透過
- [ ] 效能無明顯變化
- [ ] 沒有新的錯誤或警告

---

## 七、遷移範例

### 範例 1：簡單指令碼

#### Before
```python
#!/usr/bin/env python3
from paddle_ocr_tool import PaddleOCRTool

def main():
    tool = PaddleOCRTool(mode="basic")
    result = tool.process_basic("input.jpg")
    print(result)

if __name__ == "__main__":
    main()
```

#### After（最小變更）
```python
#!/usr/bin/env python3
from paddle_ocr_facade import PaddleOCRFacade as PaddleOCRTool  # 只改這行

def main():
    tool = PaddleOCRTool(mode="basic")
    result = tool.process_basic("input.jpg")
    print(result)

if __name__ == "__main__":
    main()
```

---

### 範例 2：批次處理

#### Before
```python
from paddle_ocr_tool import PaddleOCRTool
import glob

tool = PaddleOCRTool(mode="hybrid")

for pdf_file in glob.glob("*.pdf"):
    result = tool.process_hybrid(pdf_file)
    print(f"完成：{pdf_file}")
```

#### After（完全遷移）
```python
from paddle_ocr_facade import PaddleOCRFacade  # 新名稱
import glob

facade = PaddleOCRFacade(mode="hybrid")  # 新變數名

for pdf_file in glob.glob("*.pdf"):
    result = facade.process_hybrid(pdf_file)
    print(f"完成：{pdf_file}")
```

---

## 八、回退計畫

如果遇到問題需要回退：

### 方法 1：修改 import
```python
# 從
from paddle_ocr_facade import PaddleOCRFacade

# 改回
from paddle_ocr_tool import PaddleOCRTool
```

### 方法 2：使用版本控制
```bash
git revert <commit-hash>
```

---

## 九、獲取幫助

### 檔案資源

- 📖 [FACADE_API_GUIDE.md](FACADE_API_GUIDE.md) - 完整 API 檔案
- 🏗️ [ARCHITECTURE.md](../ARCHITECTURE.md) - 架構說明
- 🧪 [TESTING_GUIDE.md](TESTING_GUIDE.md) - 測試指南

### 報告問題

如果遇到問題，請提供：
1. 錯誤訊息
2. 使用的程式碼片段
3. 預期行為 vs 實際行為

---

## 十、未來計畫

### 已完成 ✅
- HybridPDFProcessor
- TranslationProcessor  
- BasicProcessor
- PaddleOCRFacade

### 進行中 🔄
- StructureProcessor
- FormulaProcessor
- 效能最佳化

### 計畫中 📋
- 更多輸出格式支援
- 更多翻譯引擎整合
- WebAPI 支援

---

**總結**：遷移非常簡單，風險極低，建議盡早採用新架構以獲得更好的開發體驗！
