# PaddleOCR Toolkit - Agent 開發規則

## 核心理念：測試驅動 + Artifact-First

你是 PaddleOCR Toolkit 專案的專業 Python 開發者。本專案是一個基於 PaddleOCR 的多功能檔案辨識與處理工具。

### Artifact 協議

1. **規劃**：在修改 `paddleocr_toolkit/` 或 `paddle_ocr_tool.py` 之前，先建立 `artifacts/plans/plan_[feature_name].md`。
2. **測試**：修改程式碼後，執行 `pytest --cov` 並將結果儲存到 `artifacts/logs/`。
3. **檔案**：更新 README.md 或相關檔案。

---

## 專案特定規則

### 編碼標準

1. **型別提示**：所有新函式必須有型別提示（使用 `typing` 模組）。
2. **檔案字串**：使用 Google-style docstrings。

   ```python
   def example_function(param: str) -> bool:
       """簡要描述。
       
       詳細說明（如果需要）。
       
       Args:
           param: 引數說明。
           
       Returns:
           返回值說明。
           
       Raises:
           ValueError: 錯誤情況說明。
       """
   ```

3. **模組組織**：
   - 核心功能 → `paddleocr_toolkit/core/`
   - 處理器 → `paddleocr_toolkit/processors/`
   - 輸出格式 → `paddleocr_toolkit/outputs/`

4. **匯入順序**：

   ```python
   # 1. 標準函式庫
   import os
   import sys
   
   # 2. 第三方套件
   import numpy as np
   import fitz
   
   # 3. 本地模組
   from paddleocr_toolkit.core import OCRResult
   ```

---

### 測試要求

1. **覆蓋率**：新功能必須有測試，保持 **76%+** 覆蓋率。
2. **測試位置**：`tests/test_[module_name].py`
3. **命名規範**：`test_[function_name]_[scenario]()`
4. **測試結構**：
   - 使用 `pytest` fixtures 重用測試設定
   - Mock 外部依賴（PyMuPDF, OpenCV, PaddleOCR）
   - 測試正常情況、邊界條件、錯誤處理

5. **執行測試**：

   ```bash
   # 執行所有測試
   pytest tests/ --cov=paddleocr_toolkit --cov-report=term-missing
   
   # 執行特定模組測試
   pytest tests/test_pdf_generator.py -v
   ```

---

### 架構原則

1. **避免迴圈依賴**：
   - 使用延遲載入模式（參考 `__init__.py` 中的 `get_paddle_ocr_tool()`）
   - 核心模組不應依賴主程式

2. **DRY 原則**：
   - 共用邏輯放在 `core/pdf_utils.py`
   - 重複的 PDF 操作使用工具函式（如 `pixmap_to_numpy()`, `page_to_numpy()`）

3. **設定優先順序**：
   - CLI 引數 > config.yaml > 預設值
   - 使用 `config_loader.py` 載入設定

4. **錯誤處理**：
   - 使用 `logging` 模組記錄錯誤，不要用 `print()`
   - 提供有意義的錯誤訊息
   - 在適當的地方使用 try-except

---

## 專案結構理解

```
paddleocr-toolkit/
├── paddle_ocr_tool.py        # ⚠️ 主程式（CLI，2600 行）- 修改要小心
├── paddleocr_toolkit/        # Python 套件
│   ├── core/                 # 核心功能（優先修改）
│   │   ├── models.py         # OCRResult, OCRMode 資料模型
│   │   ├── pdf_generator.py  # PDF 生成器
│   │   ├── pdf_utils.py      # 共用 PDF 工具（9 個函式）
│   │   └── config_loader.py  # YAML 設定載入
│   ├── processors/           # 資料處理器
│   │   ├── text_processor.py     # 文書處理（90% 覆蓋率 ✅）
│   │   ├── pdf_quality.py        # PDF 品質偵測（70% 覆蓋率）
│   │   ├── image_preprocessor.py # 影像前處理（66% 覆蓋率）
│   │   ├── batch_processor.py    # 批次處理（82% 覆蓋率 ✅）
│   │   ├── glossary_manager.py   # 術語管理（83% 覆蓋率 ✅）
│   │   ├── ocr_workaround.py     # OCR 替代方案（76% 覆蓋率）
│   │   └── stats_collector.py    # 統計收集（80% 覆蓋率 ✅）
│   └── outputs/              # 輸出格式
├── tests/                    # 測試（76% 覆蓋率，147 個測試）
├── config.yaml               # 設定檔範本
└── .agent/                   # Agent 規則（你正在閱讀的檔案）
```

---

## 關鍵設計決策

### 1. 迴圈依賴解決

**問題**：`paddleocr_toolkit` 需要 import `paddle_ocr_tool`  
**解決**：使用 `get_paddle_ocr_tool()` 延遲載入

### 2. 共用工具

**問題**：Pixmap → numpy 轉換在 5+ 處重複  
**解決**：建立 `pdf_utils.py`，提供 9 個共用函式

### 3. 設定檔支援

**問題**：CLI 引數過多  
**解決**：使用 `config.yaml` + `config_loader.py`

---

## 已知限制與改進方向

### 目前限制

1. **主程式過大**：`paddle_ocr_tool.py` 2600 行，待重構
2. **部分模組未充分整合**：`batch_processor`, `image_preprocessor` 可更好整合到主流程
3. **低覆蓋模組**：`pdf_generator.py` (69%), `image_preprocessor.py` (66%) 需更多測試

### 改進方向

1. **主程式重構**：拆分為多個模組
2. **提升覆蓋率**：目標 80%+
3. **Docker 容器化**：一鍵部署
4. **API 檔案**：使用 Sphinx 自動生成

---

## 許可權與限制

### ✅ 允許的操作

- 修改 `paddleocr_toolkit/` 下的模組
- 新增測試到 `tests/`
- 更新 `README.md` 和檔案
- 執行 `pytest` 和 `mypy`
- 新增功能到 `config.yaml`

### ⚠️ 需謹慎的操作

- 修改 `paddle_ocr_tool.py`（主程式很大，影響範圍廣）
- 修改 `core/models.py`（影響所有模組）
- 修改測試 fixtures（可能影響多個測試）

### ❌ 限制的操作

- ❌ 不要刪除現有測試（除非有充分理由）
- ❌ 不要降低測試覆蓋率
- ❌ 不要移除現有功能（除非已棄用）
- ❌ 不要使用 `print()` 替代 `logging`

---

## 開發工作流程

詳細工作流程請參考：

- `.agent/workflows/add_feature.md` - 新增功能
- `.agent/workflows/add_tests.md` - 新增測試
- `.agent/workflows/fix_bug.md` - 修復 Bug

---

## 上下文檔案

更多專案資訊請參考：

- `.agent/context/architecture.md` - 架構說明
- `.agent/context/coding_style.md` - 編碼風格
- `.agent/context/testing_guide.md` - 測試指南

---

*規則版本：v1.0*  
*最後更新：2024-12-13*
