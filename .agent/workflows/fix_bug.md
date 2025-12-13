# Bug 修復工作流程

## 目標

系統化地修復 PaddleOCR Toolkit 中的 Bug，確保品質不降低。

---

## 步驟

### 1. 記錄 Bug 資訊 📝

**在 `artifacts/plans/bugfix_[issue].md` 建立報告**：

```markdown
# Bug 修復：[簡短描述]

## Bug 描述
[詳細說明問題現象]

## 重現步驟
1. 執行 `python paddle_ocr_tool.py document.pdf`
2. 使用參數 `--mode hybrid`
3. 觀察到錯誤：[錯誤訊息]

## 預期行為
[應該要發生什麼]

## 實際行為
[實際發生了什麼]

## 環境資訊
- Python 版本：3.12
- 作業系統：Windows 11
- 相關套件版本：paddleocr==3.0.0, PyMuPDF==1.23.0

## 錯誤訊息/堆疊追蹤
```

[貼上完整錯誤訊息]

```

## 可能原因
[初步分析]

## 修復計畫
1. 步驟一
2. 步驟二
```

---

### 2. 建立重現測試 🧪

**在修復前先寫測試**（TDD 原則）：

```python
# tests/test_bugfix_[issue].py
import pytest

class TestBugFix:
    """測試 Bug #XXX 的修復"""
    
    @pytest.mark.xfail(reason="Bug #XXX: 尚未修復")
    def test_bug_reproduction(self):
        """重現 Bug 的測試（預期失敗）"""
        # 執行會觸發 Bug 的操作
        result = problematic_function(input_data)
        # 預期行為
        assert result == expected_output
```

---

### 3. 修復 Bug 🔧

**修復原則**：

1. **最小化變更**：只修改必要的部分
2. **保持相容性**：不破壞現有功能
3. **加註解**：說明為何這樣修改

**範例**：

```python
def problematic_function(data: str) -> str:
    """處理資料。
    
    Args:
        data: 輸入資料。
        
    Returns:
        處理後的資料。
    """
    # Bug #XXX 修復：處理空字串的情況
    # 之前：直接 return data.upper()
    # 問題：data 為 None 時會拋出 AttributeError
    # 修復：先檢查 data 是否為 None
    if data is None:
        return ""
    
    return data.upper()
```

---

### 4. 更新測試 ✅

**移除 xfail 標記**：

```python
class TestBugFix:
    """測試 Bug #XXX 的修復"""
    
    def test_bug_fixed(self):
        """驗證 Bug 已修復"""
        result = problematic_function(None)
        assert result == ""  # 現在應該返回空字串
    
    def test_normal_case_still_works(self):
        """確保正常情況仍然正常"""
        result = problematic_function("hello")
        assert result == "HELLO"
```

---

### 5. 執行回歸測試 🔄

**確保沒有破壞其他功能**：

```bash
# 執行所有測試
pytest tests/ -v

# 執行與修改相關的測試
pytest tests/test_module.py -v

# 檢查覆蓋率沒有降低
pytest tests/ --cov=paddleocr_toolkit --cov-report=term-missing
```

**檢查點**：

- [ ] 所有測試通過
- [ ] 覆蓋率 ≥ 76%
- [ ] Bug 相關的測試從 xfail 變為 pass

---

### 6. 更新文件 📚

**如果 Bug 影響使用者**：

1. **更新 README.md**（如果行為改變）
2. **更新 CHANGELOG**（建議建立）：

   ```markdown
   ## [版本號] - YYYY-MM-DD
   
   ### Fixed
   - 修復 PDF 處理空頁面時的崩潰問題 (#123)
   - 修復 config.yaml 載入錯誤的問題 (#124)
   ```

3. **更新 docstring**（如果函數行為改變）

---

### 7. 提交變更 🚀

**提交訊息格式**：

```bash
fix: [簡短描述 Bug]

修復 [詳細說明]

- 根本原因：[說明原因]
- 修復方法：[說明方法]
- 測試：新增/更新測試以防止回歸

Fixes #[issue號]
```

**範例**：

```bash
git add -A
git commit -m "fix: 處理 PDF 生成時的空頁面錯誤

修復當輸入 PDF 包含空頁面時會拋出 AttributeError 的問題

- 根本原因：未檢查頁面是否包含內容
- 修復方法：在處理前加入 None 檢查
- 測試：新增 test_empty_page 測試案例

Fixes #123"

git push origin master
```

---

## 常見 Bug 類型與處理

### 1. None 值錯誤 ❌

**症狀**：`AttributeError: 'NoneType' object has no attribute 'X'`

**修復**：

```python
# 錯誤
result = data.property

# 修正
result = data.property if data is not None else default_value
```

### 2. 空列表/字串錯誤 ❌

**症狀**：索引錯誤或空值處理不當

**修復**：

```python
# 錯誤
first_item = items[0]

# 修正
first_item = items[0] if items else None
```

### 3. 編碼錯誤 ❌

**症狀**：`UnicodeDecodeError` 或亂碼

**修復**：

```python
# 錯誤
with open(file, 'r') as f:
    content = f.read()

# 修正
with open(file, 'r', encoding='utf-8') as f:
    content = f.read()
```

### 4. 路徑錯誤 ❌

**症狀**：`FileNotFoundError` 或路徑不存在

**修復**：

```python
# 使用 pathlib
from pathlib import Path

file_path = Path(input_path)
if not file_path.exists():
    raise FileNotFoundError(f"檔案不存在：{file_path}")
```

---

## 檢查清單 ✓

修復前：

- [ ] 已記錄 Bug 資訊（`artifacts/plans/bugfix_[issue].md`）
- [ ] 已建立重現測試（標記為 xfail）
- [ ] 已理解根本原因

修復後：

- [ ] Bug 已修復
- [ ] 測試從 xfail 變為 pass
- [ ] 所有測試通過
- [ ] 覆蓋率沒有降低
- [ ] 已更新相關文件
- [ ] 提交訊息清晰

---

## 預防 Bug 的最佳實踐

1. **使用類型提示**：讓 IDE 和 mypy 協助檢查

   ```python
   def process(data: Optional[str]) -> str:
       ...
   ```

2. **輸入驗證**：盡早檢查輸入

   ```python
   if not isinstance(data, str):
       raise TypeError("data 必須是字串")
   ```

3. **防禦性程式設計**：假設輸入可能無效

   ```python
   result = data.strip() if data else ""
   ```

4. **完整的錯誤處理**：

   ```python
   try:
       result = risky_operation()
   except SpecificError as e:
       logger.error(f"操作失敗：{e}")
       return default_value
   ```

---

*工作流程版本：v1.0*
