# PaddleOCR Facade API 使用指南

> 現代化 API 層，替代傳統的 paddle_ocr_tool.py

---

## 快速開始

### 基本使用

```python
from paddle_ocr_facade import PaddleOCRFacade

# 初始化（混合模式）
facade = PaddleOCRFacade(mode="hybrid")

# 處理 PDF
result = facade.process_hybrid(
    "input.pdf",
    output_path="output.pdf",
    markdown_output="output.md"
)

print(f"處理完成：{result['pages_processed']} 頁")
```

### 統一處理介面

```python
# 使用統一的 .process() 方法
facade = PaddleOCRFacade(mode="hybrid")
result = facade.process("document.pdf")
```

---

## 初始化引數

```python
PaddleOCRFacade(
    mode="basic",                      # OCR 模式
    use_orientation_classify=False,    # 檔案方向校正
    use_doc_unwarping=False,           # 檔案彎曲校正
    use_textline_orientation=False,    # 文字行方向偵測
    device="cpu",                      # 運算裝置 ('gpu' 或 'cpu')
    debug_mode=False,                  # 除錯模式
    compress_images=True,              # 圖片壓縮
    jpeg_quality=85,                   # JPEG 品質
    
    # v3.0 新增：語義處理（AI 增強）
    enable_semantic=False,             # 啟用語義處理
    llm_provider="ollama",             # LLM 提供商 ('ollama', 'openai')
    llm_model=None                     # LLM 模型（可選）
)
```

---

## 模式說明

### 1. Hybrid 模式（推薦）

結合 PP-StructureV3 版面分析與 PP-OCRv5 精確座標。

```python
facade = PaddleOCRFacade(mode="hybrid")

result = facade.process_hybrid(
    "input.pdf",
    output_path="output_searchable.pdf",
    markdown_output="output.md",
    json_output="output.json",
    dpi=150,
    show_progress=True
)
```

**輸出**：
- 可搜尋 PDF（原文）
- 擦除版 PDF
- Markdown 檔案
- JSON 結構化資料

### 2. 含翻譯的混合模式

```python
result = facade.process_hybrid(
    "input.pdf",
    translate_config={
        "source_lang": "zh",
        "target_lang": "en",
        "ollama_model": "qwen2.5:7b",
        "ollama_url": "http://localhost:11434",
        "no_mono": False,      # 生成純翻譯 PDF
        "no_dual": False,      # 生成雙語對照 PDF
        "dual_mode": "alternating",  # 'alternating' 或 'side-by-side'
    }
)
```

**輸出（額外）**：
- 純翻譯 PDF
- 雙語對照 PDF

---

## 與舊 API 的對比

### 舊 API (paddle_ocr_tool.py)

```python
from paddle_ocr_tool import PaddleOCRTool

tool = PaddleOCRTool(mode="hybrid", device="cpu")
result = tool.process_hybrid("input.pdf", "output.pdf")
```

### 新 API (paddle_ocr_facade.py)

```python
from paddle_ocr_facade import PaddleOCRFacade

facade = PaddleOCRFacade(mode="hybrid", device="cpu")
result = facade.process_hybrid("input.pdf", "output.pdf")
```

**向後相容**：新 API 與舊 API 完全相容，只需修改 import！

---

## v3.0 新功能：語義處理

### 啟用 AI 驅動的 OCR 後處理

```python
# 啟用語義處理
facade = PaddleOCRFacade(
    mode="basic",
    enable_semantic=True,          # 🔥 啟用語義處理
    llm_provider="ollama",         # LLM 提供商
    llm_model="qwen2.5:7b"         # 模型（可選）
)

# 1. 修正 OCR 錯誤
ocr_text = "這個文建包含銷多錯沒"
corrected = facade.correct_text(ocr_text)
print(corrected)  # "這個檔案包含很多錯誤"

# 2. 提取結構化資料
business_card = """
張小明
工程師
Email: zhang@example.com
"""

schema = {"name": "姓名", "title": "職稱", "email": "Email"}
data = facade.extract_structured_data(business_card, schema)
# {"name": "張小明", "title": "工程師", "email": "zhang@example.com"}
```

**詳細說明**：請參閱 [SemanticProcessor 使用指南](SEMANTIC_PROCESSOR_GUIDE.md)

---

## 進階用法

### 直接訪問引擎

```python
facade = PaddleOCRFacade(mode="hybrid")

# 獲取底層引擎
engine = facade.get_engine()

# 直接預測
result = facade.predict(image_array)
```

### 自訂 DPI 和壓縮

```python
facade = PaddleOCRFacade(
    mode="hybrid",
    compress_images=True,
    jpeg_quality=95  # 更高品質
)

result = facade.process_hybrid(
    "input.pdf",
    dpi=300  # 更高解析度
)
```

---

## 架構優勢

### 模組化設計

```
PaddleOCRFacade (輕量 API 層)
    ├─> OCREngineManager (引擎管理)
    ├─> HybridPDFProcessor (混合模式)
    ├─> TranslationProcessor (翻譯)
    └─> StructureProcessor (結構化，待實作)
```

### 好處

1. **輕量化**：Facade 僅 265 行
2. **解耦**：每個 Processor 獨立可測試
3. **擴充性**：新增模式只需加入新 Processor
4. **維護性**：職責明確，易於理解

---

## 遷移指南

### 從舊 API 遷移

**步驟 1**：修改 import
```python
# 舊
from paddle_ocr_tool import PaddleOCRTool

# 新
from paddle_ocr_facade import PaddleOCRFacade
```

**步驟 2**：修改類別名稱
```python
# 舊
tool = PaddleOCRTool(mode="hybrid")

# 新
facade = PaddleOCRFacade(mode="hybrid")
```

**步驟 3**：方法呼叫保持不變
```python
# 完全相同的 API
result = facade.process_hybrid("input.pdf")
```

### 向後相容別名

如果暫時無法修改程式碼，可使用別名：

```python
from paddle_ocr_facade import PaddleOCRTool  # 等同於 PaddleOCRFacade

tool = PaddleOCRTool(mode="hybrid")  # 仍然可用
```

---

## 常見問題

### Q: 新舊 API 有什麼區別？

**A**: 功能完全相同，新 API 採用模組化架構，更易維護和擴充。

### Q: 需要重新安裝依賴嗎？

**A**: 不需要，依賴完全相同。

### Q: 效能有影響嗎？

**A**: 無影響，委派呼叫的開銷可忽略不計。

### Q: 舊程式碼還能用嗎？

**A**: 可以，paddle_ocr_tool.py 仍然保留且向後相容。

---

## 完整範例

```python
from paddle_ocr_facade import PaddleOCRFacade

# 1. 初始化
facade = PaddleOCRFacade(
    mode="hybrid",
    device="gpu",
    compress_images=True,
    jpeg_quality=85
)

# 2. 處理 PDF（含翻譯）
result = facade.process_hybrid(
    input_path="document.pdf",
    output_path="searchable.pdf",
    markdown_output="document.md",
    dpi=150,
    show_progress=True,
    translate_config={
        "source_lang": "zh",
        "target_lang": "en",
        "ollama_model": "qwen2.5:7b",
    }
)

# 3. 檢查結果
if result.get("error"):
    print(f"錯誤：{result['error']}")
else:
    print(f"✅ 處理完成：{result['pages_processed']} 頁")
    print(f"  可搜尋 PDF: {result['searchable_pdf']}")
    print(f"  Markdown: {result['markdown_file']}")
    if result.get('translated_pdf'):
        print(f"  翻譯 PDF: {result['translated_pdf']}")
```

---

## 更多資訊

- 📖 [完整檔案](docs/API_GUIDE.md)
- 🏗️ [架構說明](ARCHITECTURE.md)
- 🧪 [測試範例](tests/)
