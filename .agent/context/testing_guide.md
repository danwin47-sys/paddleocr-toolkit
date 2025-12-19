# PaddleOCR Toolkit 測試指南

> 最後更新：2024-12-13

---

## 測試原則

### 核心原則

1. **測試驅動開發（TDD）**：先寫測試再寫程式碼
2. **獨立性**：每個測試應該獨立執行
3. **可重複性**：測試結果應該一致
4. **快速**：單元測試應該快速執行
5. **清晰**：測試應該清楚表達意圖

### 目標

- **短期**：保持 76%+ 覆蓋率
- **中期**：達到 80%+ 覆蓋率
- **長期**：達到 85%+ 覆蓋率

---

## 測試結構

### 檔案組織

```
tests/
├── conftest.py                    # 共用 fixtures
├── test_models.py                 # 測試 core/models.py
├── test_pdf_generator.py          # 測試 core/pdf_generator.py
├── test_pdf_utils.py              # 測試 core/pdf_utils.py
├── test_config_loader.py          # 測試 core/config_loader.py
├── test_text_processor.py         # 測試 processors/text_processor.py
├── test_pdf_quality.py            # 測試 processors/pdf_quality.py
├── test_image_preprocessor.py     # 測試 processors/image_preprocessor.py
├── test_batch_processor.py        # 測試 processors/batch_processor.py
├── test_glossary_manager.py       # 測試 processors/glossary_manager.py
├── test_ocr_workaround.py         # 測試 processors/ocr_workaround.py
├── test_stats_collector.py        # 測試 processors/stats_collector.py
└── test_package_init.py           # 測試 __init__.py
```

---

## 測試命名

### 類別命名

```python
class TestPDFGenerator:
    """測試 PDFGenerator 類別"""
    pass

class TestConfigLoader:
    """測試 ConfigLoader 功能"""
    pass
```

### 測試方法命名

```python
def test_[function_name]_[scenario]():
    """測試描述"""
    pass

# 範例
def test_add_page_with_valid_image():
    """測試使用有效圖片新增頁面"""
    pass

def test_add_page_raises_error_when_file_not_found():
    """測試檔案不存在時丟擲錯誤"""
    pass
```

---

## Fixtures

### 定義 Fixtures（conftest.py）

```python
import pytest
import tempfile
from pathlib import Path

@pytest.fixture
def sample_ocr_result():
    """提供測試用的 OCR 結果"""
    from paddleocr_toolkit.core import OCRResult
    return OCRResult(
        text="Test",
        confidence=0.95,
        bbox=[[0, 0], [100, 0], [100, 30], [0, 30]]
    )

@pytest.fixture
def temp_pdf_path():
    """提供臨時 PDF 檔案路徑"""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        temp_path = f.name
    yield temp_path
    # 清理
    if os.path.exists(temp_path):
        os.remove(temp_path)

@pytest.fixture
def mock_paddle_ocr(monkeypatch):
    """Mock PaddleOCR"""
    class MockOCR:
        def __call__(self, image):
            return [[
                [[0, 0], [100, 0], [100, 30], [0, 30]],
                ("Test", 0.95)
            ]]
    
    monkeypatch.setattr("paddleocr.PaddleOCR", lambda **kwargs: MockOCR())
    return MockOCR()
```

### 使用 Fixtures

```python
def test_with_fixture(sample_ocr_result):
    """使用 fixture 的測試"""
    assert sample_ocr_result.text == "Test"
    assert sample_ocr_result.confidence == 0.95
```

---

## Mock 與 Patch

### Mock 檔案操作

```python
from unittest.mock import mock_open, patch

def test_read_file():
    """測試讀取檔案"""
    mock_data = "test content"
    
    with patch("builtins.open", mock_open(read_data=mock_data)):
        result = read_file("test.txt")
        assert result == mock_data
```

### Mock PyMuPDF

```python
@pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
def test_with_real_fitz():
    """使用真實 PyMuPDF 的測試"""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    # 測試邏輯
    doc.close()
```

### Mock PaddleOCR

```python
def test_ocr_processing(monkeypatch):
    """測試 OCR 處理"""
    def mock_ocr_call(image):
        return [[
            [[10, 10], [100, 10], [100, 30], [10, 30]],
            ("Mocked Text", 0.98)
        ]]
    
    monkeypatch.setattr("module.ocr_instance", mock_ocr_call)
    result = process_with_ocr(image)
    assert "Mocked Text" in result
```

---

## 引數化測試

### 使用 pytest.mark.parametrize

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "Hello"),
    ("WORLD", "World"),
    ("", ""),
    ("123", "123"),
])
def test_capitalize(input, expected):
    """測試首字母大寫"""
    result = capitalize(input)
    assert result == expected
```

### 測試多組資料

```python
@pytest.mark.parametrize("bbox,expected_width,expected_height", [
    ([[0, 0], [100, 0], [100, 50], [0, 50]], 100, 50),
    ([[10, 10], [60, 10], [60, 35], [10, 35]], 50, 25),
])
def test_bbox_dimensions(bbox, expected_width, expected_height):
    """測試邊界框尺寸計算"""
    result = OCRResult(text="", confidence=1.0, bbox=bbox)
    assert result.width == expected_width
    assert result.height == expected_height
```

---

## 異常測試

### 測試預期的異常

```python
def test_raises_value_error():
    """測試丟擲 ValueError"""
    with pytest.raises(ValueError):
        process_data(None)

def test_raises_with_message():
    """測試異常訊息"""
    with pytest.raises(ValueError, match="不能為空"):
        process_data([])

def test_raises_file_not_found():
    """測試檔案不存在"""
    with pytest.raises(FileNotFoundError):
        open_pdf("nonexistent.pdf")
```

---

## 測試覆蓋率

### 執行測試並檢視覆蓋率

```bash
# 基本覆蓋率報告
pytest tests/ --cov=paddleocr_toolkit

# 詳細報告（顯示缺失行）
pytest tests/ --cov=paddleocr_toolkit --cov-report=term-missing

# HTML 報告
pytest tests/ --cov=paddleocr_toolkit --cov-report=html

# 只測試特定模組
pytest tests/test_pdf_generator.py --cov=paddleocr_toolkit.core.pdf_generator
```

### 覆蓋率目標

| 模組型別 | 最低覆蓋率 | 目標覆蓋率 |
|---------|-----------|-----------|
| 核心模組 (core/)| 75% | 85%+ |
| 處理器 (processors/) | 70% | 80%+ |
| 輸出 (outputs/) | 70% | 80%+ |
| **整體** | **76%** | **80%+** |

---

## 測試模式

### AAA 模式（Arrange-Act-Assert）

```python
def test_text_processing():
    """測試文書處理"""
    # Arrange（準備）
    input_text = "HelloWorld"
    expected_output = "Hello World"
    processor = TextProcessor()
    
    # Act（執行）
    result = processor.process(input_text)
    
    # Assert（驗證）
    assert result == expected_output
```

### Given-When-Then 模式

```python
def test_pdf_generation():
    """測試 PDF 生成
    
    Given: 有一個 PDF 生成器和 OCR 結果
    When: 新增頁面並儲存
    Then: 應該生成可搜尋的 PDF
    """
    # Given
    generator = PDFGenerator("output.pdf")
    ocr_results = [sample_result]
    
    # When
    generator.add_page("image.png", ocr_results)
    generator.save()
    
    # Then
    assert os.path.exists("output.pdf")
```

---

## 常見測試場景

### 測試檔案處理

```python
import tempfile

def test_file_processing():
    """測試檔案處理"""
    # 建立臨時檔案
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b"test content")
        temp_path = f.name
    
    try:
        # 測試邏輯
        result = process_file(temp_path)
        assert result is True
    finally:
        # 清理
        if os.path.exists(temp_path):
            os.remove(temp_path)
```

### 測試影像處理

```python
import numpy as np

def test_image_processing():
    """測試影像處理"""
    # 建立測試影像
    image = np.ones((100, 100, 3), dtype=np.uint8) * 255
    
    # 處理影像
    result = process_image(image)
    
    # 驗證
    assert result.shape == image.shape
    assert result.dtype == np.uint8
```

### 測試 PDF 處理

```python
def test_pdf_processing():
    """測試 PDF 處理"""
    import fitz
    
    # 建立測試 PDF
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 50), "Test")
    
    # 儲存到臨時檔案
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        temp_path = f.name
    doc.save(temp_path)
    doc.close()
    
    try:
        # 測試邏輯
        result = process_pdf(temp_path)
        assert result is not None
    finally:
        # 清理
        if os.path.exists(temp_path):
            os.remove(temp_path)
```

---

## 測試標記

### 使用 pytest.mark

```python
@pytest.mark.slow
def test_large_pdf_processing():
    """測試大型 PDF 處理（慢速）"""
    pass

@pytest.mark.skipif(not HAS_GPU, reason="需要 GPU")
def test_gpu_acceleration():
    """測試 GPU 加速"""
    pass

@pytest.mark.xfail(reason="已知 Bug #123")
def test_known_bug():
    """測試已知 Bug"""
    pass
```

### 執行特定標記的測試

```bash
# 只執行快速測試
pytest -m "not slow"

# 只執行慢速測試
pytest -m slow

# 跳過已知會失敗的測試
pytest --ignore-xfail
```

---

## 測試檢查清單 ✓

新增測試時檢查：

- [ ] 測試名稱清楚描述測試內容
- [ ] 測試獨立且可重複
- [ ] 有測試正常情況
- [ ] 有測試邊界條件
- [ ] 有測試錯誤處理
- [ ] Mock 了外部依賴
- [ ] 清理了臨時資源
- [ ] 覆蓋率有提升
- [ ] 所有測試透過

---

## 常見問題

### Q: 如何測試需要 GPU 的功能？

A: 使用 `pytest.mark.skipif` 跳過，或在 CI 環境中配置 GPU runner。

### Q: 測試執行很慢怎麼辦？

A:

1. 使用 `pytest.mark.slow` 標記慢速測試
2. 開發時執行 `pytest -m "not slow"`
3. CI 時執行完整測試套件

### Q: 如何測試 PaddleOCR 相關功能？

A: Mock PaddleOCR 的 `__call__` 方法，返回預定義的結果。

---

*測試指南版本：v1.0*
