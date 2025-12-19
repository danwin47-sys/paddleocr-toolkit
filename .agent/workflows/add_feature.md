# 新增功能工作流程

## 目標

為 PaddleOCR Toolkit 新增新功能，同時維持程式碼品質和測試覆蓋率。

---

## 步驟

### 1. 建立實作計畫 📋

**檔案位置**：`artifacts/plans/plan_[feature_name].md`

**內容包含**：

- **功能描述**：這個功能要解決什麼問題？
- **影響範圍**：會修改哪些模組？
- **實作方法**：技術方案說明
- **測試策略**：如何測試這個功能？
- **預期工作量**：預估需要多少時間

**範本**：

```markdown
# 功能：[功能名稱]

## 問題描述
[描述要解決的問題或需求]

## 影響範圍
- [ ] `paddleocr_toolkit/core/[module].py`
- [ ] `paddleocr_toolkit/processors/[module].py`
- [ ] `tests/test_[module].py`
- [ ] `README.md`

## 實作方法
1. 步驟一
2. 步驟二
3. 步驟三

## 測試策略
- 單元測試：測試 XXX 功能
- 整合測試：測試與現有模組的整合
- 邊界測試：測試極端情況

## 預期工作量
約 X 小時
```

---

### 2. 實作功能 💻

**位置選擇**：

- 核心功能 → `paddleocr_toolkit/core/[new_module].py`
- 處理器 → `paddleocr_toolkit/processors/[new_module].py`
- 輸出格式 → `paddleocr_toolkit/outputs/[new_module].py`

**編碼要求**：

- ✅ 使用型別提示
- ✅ 撰寫 Google-style docstrings
- ✅ 遵循 PEP 8（行長 120 字元）
- ✅ 使用 `logging` 而非 `print()`

**範例**：

```python
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

def process_data(input_data: List[str], threshold: float = 0.5) -> Optional[str]:
    """處理輸入資料並返回結果。
    
    Args:
        input_data: 要處理的資料列表。
        threshold: 處理閾值，預設為 0.5。
        
    Returns:
        處理後的結果字串，如果失敗則返回 None。
        
    Raises:
        ValueError: 當 input_data 為空時。
    """
    if not input_data:
        raise ValueError("輸入資料不能為空")
        
    logger.info(f"開始處理 {len(input_data)} 筆資料")
    # 實作邏輯...
    return result
```

---

### 3. 撰寫測試 ✅

**檔案位置**：`tests/test_[module_name].py`

**測試要求**：

- 目標覆蓋率：**> 80%**（針對新程式碼）
- 測試正常情況
- 測試邊界條件
- 測試錯誤處理

**範例**：

```python
import pytest
from paddleocr_toolkit.core.new_module import process_data

class TestProcessData:
    """測試 process_data 函式"""
    
    def test_normal_case(self):
        """測試正常情況"""
        result = process_data(["a", "b", "c"<])
        assert result is not None
    
    def test_empty_input(self):
        """測試空輸入"""
        with pytest.raises(ValueError):
            process_data([])
    
    def test_custom_threshold(self):
        """測試自訂閾值"""
        result = process_data(["a"], threshold=0.8)
        assert result is not None
```

---

### 4. 執行驗證 🧪

**執行測試**：

```bash
# 執行所有測試
pytest tests/ --cov=paddleocr_toolkit --cov-report=term-missing

# 只執行新模組的測試
pytest tests/test_new_module.py -v

# 儲存測試結果到 artifacts
pytest tests/ --cov=paddleocr_toolkit --cov-report=html
# 將 htmlcov/ 移至 artifacts/logs/coverage_YYYYMMDD/
```

**檢查點**：

- [ ] 所有測試透過
- [ ] 整體覆蓋率 ≥ 76%
- [ ] 新程式碼覆蓋率 ≥ 80%
- [ ] 沒有 linting 錯誤

---

### 5. 更新檔案 📚

**必須更新**（如果適用）：

1. **README.md**（如果是使用者可見功能）
   - 功能特色表格
   - 使用範例
   - 命令列引數

2. **config.yaml**（如果有新設定）
   - 新增設定專案
   - 註解說明

3. **requirements.txt**（如果有新依賴）
   - 新增套件及版本

4. **walkthrough.md**（如果影響架構）
   - 更新模組列表
   - 更新架構圖

---

### 6. 提交變更 🚀

**提交訊息格式**：

```bash
feat: [簡短描述功能]

- 詳細說明變更內容
- 影響範圍
- 測試覆蓋率

Closes #[issue號] (如果有)
```

**範例**：

```bash
git add -A
git commit -m "feat: 新增 PDF 批次處理功能

- 新增 BatchProcessor 類別支援多執行緒處理
- 新增 pdf_to_images_parallel 函式
- 測試覆蓋率從 74% 提升至 76%

Closes #42"

git push origin master
```

---

## 檢查清單 ✓

在提交前，確認以下專案：

- [ ] 已建立實作計畫（`artifacts/plans/plan_[name].md`）
- [ ] 程式碼有型別提示和 docstrings
- [ ] 已撰寫測試且覆蓋率 > 76%
- [ ] 所有測試透過
- [ ] 已更新相關檔案
- [ ] 提交訊息清晰明確

---

## 常見問題

**Q: 我不確定功能應該放在哪個模組？**  
A: 參考 `.agent/context/architecture.md`，或在 `artifacts/plans/` 中說明你的考慮，請求審查。

**Q: 測試寫起來很困難，可以跳過嗎？**  
A: 不行。測試是專案品質的保證。如果測試困難，可能表示程式碼設計需要改進。

**Q: 我的功能需要新的依賴套件怎麼辦？**  
A: 在 `artifacts/plans/` 中說明為何需要這個依賴，並評估對專案的影響。

---

*工作流程版本：v1.0*
