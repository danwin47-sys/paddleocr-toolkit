# 新增測試工作流程

## 目標

提升 PaddleOCR Toolkit 的測試覆蓋率至 **80%+**

當前狀態：**76%**（147 個測試）

---

## 步驟

### 1. 檢查當前覆蓋率 📊

**執行命令**：

```bash
pytest tests/ --cov=paddleocr_toolkit --cov-report=term-missing
```

**儲存結果**：

```bash
# 產生 HTML 報告
pytest tests/ --cov=paddleocr_toolkit --cov-report=html

# 手動將 htmlcov/ 資料夾移至 artifacts/logs/
# 或者直接輸出到指定位置
pytest tests/ --cov=paddleocr_toolkit --cov-report=html:artifacts/logs/coverage_$(Get-Date -Format "yyyyMMdd")
```

---

### 2. 識別低覆蓋模組 🎯

**優先順序**：

1. **< 70% 的模組**（急需改善）
2. **核心模組** (`core/`) > 處理器 > 輸出

**當前低覆蓋模組**（需優先處理）：

- `pdf_generator.py`: 69% ⚠️
- `image_preprocessor.py`: 66% ⚠️
- `pdf_utils.py`: 70% ⚠️
- `pdf_quality.py`: 70% ⚠️

---

### 3. 分析缺失的測試 🔍

**查看詳細報告**：

```bash
pytest tests/ --cov=paddleocr_toolkit --cov-report=term-missing | grep "TOTAL"
```

**記錄缺失行**：
在 `artifacts/plans/plan_improve_coverage_[module].md` 中記錄：

```markdown
# 提升 [模組名稱] 測試覆蓋率

## 當前狀態
- 覆蓋率：XX%
- 缺失行：XX-YY, ZZ-AA

## 缺失測試
- [ ] 函數 A 的錯誤處理
- [ ] 函數 B 的邊界條件
- [ ] 類別 C 的初始化

## 預期提升
從 XX% 提升至 YY%
```

---

### 4. 撰寫測試 ✍️

**測試結構**：

```python
import pytest
from unittest.mock import Mock, patch
from paddleocr_toolkit.core.module import TargetClass

class TestTargetClass:
    """測試 TargetClass 類別"""
    
    def test_initialization(self):
        """測試初始化"""
        obj = TargetClass(param=value)
        assert obj is not None
        
    def test_normal_operation(self):
        """測試正常操作"""
        # Arrange
        obj = TargetClass()
        
        # Act
        result = obj.method()
        
        # Assert
        assert result == expected
    
    def test_edge_case(self):
        """測試邊界條件"""
        obj = TargetClass()
        result = obj.method(edge_value)
        assert result is not None
    
    def test_error_handling(self):
        """測試錯誤處理"""
        obj = TargetClass()
        with pytest.raises(ValueError):
            obj.method(invalid_value)
```

---

### 5. Mock 外部依賴 🎭

**常見需要 Mock 的依賴**：

#### PyMuPDF (fitz)

```python
@pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
def test_with_fitz(self):
    doc = fitz.open()
    page = doc.new_page(width=100, height=100)
    # ... 測試邏輯
    doc.close()
```

#### OpenCV (cv2)

```python
@pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
def test_with_cv2(self):
    image = np.ones((100, 100, 3), dtype=np.uint8)
    result = process_image(image)
    assert result.shape == image.shape
```

#### 檔案系統

```python
import tempfile

def test_file_operation(self):
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        temp_path = f.name
    
    try:
        # 測試邏輯
        result = process_file(temp_path)
        assert result is True
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
```

---

### 6. 驗證覆蓋率提升 ✅

**執行特定模組測試**：

```bash
# 只測試新寫的測試
pytest tests/test_new_module.py -v

# 查看該模組的覆蓋率
pytest tests/test_new_module.py --cov=paddleocr_toolkit.core.new_module --cov-report=term-missing
```

**檢查整體覆蓋率**：

```bash
pytest tests/ --cov=paddleocr_toolkit --cov-report=term-missing
```

**目標**：

- ✅ 總覆蓋率從 76% → **80%+**
- ✅ 低覆蓋模組從 < 70% → **75%+**

---

### 7. 提交變更 🚀

**提交訊息格式**：

```bash
test: 提升 [模組名稱] 測試覆蓋率至 XX%

- 新增 N 個測試案例
- 涵蓋 [功能A], [功能B], [功能C]
- 整體覆蓋率從 YY% 提升至 ZZ%
```

**範例**：

```bash
git add tests/test_pdf_generator.py
git commit -m "test: 提升 pdf_generator 測試覆蓋率至 78%

- 新增 10 個測試案例
- 涵蓋壓縮模式、OCR 結果處理、錯誤處理
- 整體覆蓋率從 76% 提升至 77%"

git push origin master
```

---

## 測試撰寫技巧

### 1. 使用 Fixtures 重用設定

```python
# conftest.py
import pytest

@pytest.fixture
def sample_ocr_result():
    """提供測試用的 OCR 結果"""
    from paddleocr_toolkit.core import OCRResult
    return OCRResult(
        text="Test",
        confidence=0.95,
        bbox=[[0, 0], [100, 0], [100, 30], [0, 30]]
    )

# 在測試中使用
def test_with_fixture(sample_ocr_result):
    assert sample_ocr_result.text == "Test"
```

### 2. 參數化測試

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "Hello"),
    ("WORLD", "World"),
    ("", ""),
])
def test_capitalize(input, expected):
    result = capitalize(input)
    assert result == expected
```

### 3. 測試錯誤訊息

```python
def test_error_message(self):
    with pytest.raises(ValueError, match="不能為空"):
        process_data([])
```

---

## 檢查清單 ✓

- [ ] 已執行覆蓋率檢查並記錄結果
- [ ] 已識別低覆蓋模組
- [ ] 已建立測試計畫（`artifacts/plans/`）
- [ ] 已撰寫測試並通過
- [ ] 覆蓋率有明顯提升
- [ ] 所有測試通過
- [ ] 已提交變更

---

## 覆蓋率目標

### 短期目標（1-2 週）

- [ ] 整體覆蓋率 → **78%**
- [ ] 所有核心模組 → **75%+**

### 中期目標（1 個月）

- [ ] 整體覆蓋率 → **80%**
- [ ] 核心模組 → **85%+**
- [ ] 處理器 → **75%+**

### 長期目標（3 個月）

- [ ] 整體覆蓋率 → **85%**
- [ ] 所有模組 → **80%+**

---

*工作流程版本：v1.0*
