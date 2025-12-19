# PaddleOCR Toolkit 編碼風格指南

> 最後更新：2024-12-13

---

## Python 風格基礎

### 基本原則

- 遵循 **PEP 8**
- 但使用 **120 字元**行長（而非 PEP 8 的 80）
- **簡潔勝於複雜**（Zen of Python）
- **可讀性很重要**

---

## 命名規範

### 模組

```python
# ✅ 正確
image_preprocessor.py
pdf_generator.py
stats_collector.py

# ❌ 錯誤
ImagePreprocessor.py
pdfGenerator.py
Stats-Collector.py
```

### 類別

```python
# ✅ 正確
class PDFGenerator:
    pass

class OCRResult:
    pass

# ❌ 錯誤
class pdf_generator:
    pass

class OcrResult:  # 縮寫應全大寫
    pass
```

### 函式與方法

```python
# ✅ 正確
def process_document():
    pass

def convert_to_numpy():
    pass

# ❌ 錯誤
def ProcessDocument():
    pass

def convertToNumpy():
    pass
```

### 常數

```python
# ✅ 正確
MAX_PAGES = 1000
DEFAULT_DPI = 150
SUPPORTED_FORMATS = ['pdf', 'jpg', 'png']

# ❌ 錯誤
maxPages = 1000
default_dpi = 150
```

### 私有成員

```python
class Example:
    def __init__(self):
        self._internal_state = 0    # 受保護（慣例）
        self.__private_data = []    # 私有（名稱改寫）
    
    def _helper_method(self):       # 內部方法
        pass
```

---

## 型別提示

### 基本型別

```python
from typing import List, Dict, Optional, Union, Tuple

def process_text(text: str) -> str:
    """處理文字"""
    return text.upper()

def get_results(count: int = 10) -> List[str]:
    """取得結果列表"""
    return ["result"] * count
```

### Optional 型別

```python
from typing import Optional

def find_user(user_id: int) -> Optional[User]:
    """查詢使用者，可能返回 None"""
    if user_id in database:
        return database[user_id]
    return None
```

### Union 型別

```python
from typing import Union

def process_input(data: Union[str, int, float]) -> str:
    """處理多種型別的輸入"""
    return str(data)
```

### 複雜型別

```python
from typing import List, Dict, Tuple, Callable

# 字典
user_data: Dict[str, int] = {"age": 30}

# 列表
results: List[OCRResult] = []

# 元組
coordinates: Tuple[float, float, float, float] = (0, 0, 100, 100)

# 回呼函式
def apply_callback(callback: Callable[[int], str]) -> str:
    return callback(42)
```

---

## 檔案字串（Docstrings）

### 模組層級

```python
# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - PDF 生成器

此模組提供 PDF 生成功能，可將 OCR 結果疊加到原始 PDF 上，
生成可搜尋的 PDF 檔案。
"""
```

### 函式檔案字串（Google Style）

```python
def convert_pdf_to_images(
    pdf_path: str,
    dpi: int = 150,
    output_dir: Optional[str] = None
) -> List[str]:
    """將 PDF 轉換為圖片檔案。
    
    將輸入的 PDF 檔案的每一頁轉換為單獨的圖片檔案，
    並儲存到指定目錄。
    
    Args:
        pdf_path: PDF 檔案路徑。
        dpi: 圖片解析度，預設為 150。
        output_dir: 輸出目錄，如果為 None 則使用臨時目錄。
    
    Returns:
        生成的圖片檔案路徑列表。
        
    Raises:
        FileNotFoundError: 當 PDF 檔案不存在時。
        ValueError: 當 DPI 值無效時（< 50 或 > 600）。
        
    Examples:
        >>> images = convert_pdf_to_images("document.pdf", dpi=300)
        >>> print(len(images))
        10
    """
    pass
```

### 類別檔案字串

```python
class PDFGenerator:
    """PDF 生成器，用於建立可搜尋的 PDF。
    
    此類別可將 OCR 辨識結果疊加到原始圖片或 PDF 上，
    生成包含隱形文字層的可搜尋 PDF 檔案。
    
    Attributes:
        output_path: 輸出 PDF 的檔案路徑。
        debug_mode: 是否啟用除錯模式（顯示粉紅色文字層）。
        
    Examples:
        >>> generator = PDFGenerator("output.pdf")
        >>> generator.add_page("page1.png", ocr_results)
        >>> generator.save()
    """
    
    def __init__(self, output_path: str, debug_mode: bool = False):
        """初始化 PDF 生成器。
        
        Args:
            output_path: 輸出 PDF 的檔案路徑。
            debug_mode: 是否啟用除錯模式，預設為 False。
        """
        self.output_path = output_path
        self.debug_mode = debug_mode
```

---

## 匯入順序

### 標準順序

```python
# 1. 標準函式庫
import os
import sys
from pathlib import Path
from typing import List, Optional

# 2. 第三方套件（按字母順序）
import cv2
import fitz
import numpy as np
from paddleocr import PaddleOCR

# 3. 本地模組（相對匯入）
from .core import OCRResult
from .processors import fix_english_spacing
from .utils import logger
```

### 避免的匯入

```python
# ❌ 避免 * 匯入
from module import *

# ✅ 明確匯入需要的東西
from module import function_a, function_b

# ❌ 避免過長的相對匯入
from .....core.utils import helper

# ✅ 使用絕對匯入
from paddleocr_toolkit.core.utils import helper
```

---

## 日誌記錄

### 使用 logging 而非 print

```python
import logging

logger = logging.getLogger(__name__)

# ✅ 正確
logger.info("開始處理 PDF")
logger.warning("頁面 5 沒有文字")
logger.error(f"無法開啟檔案：{file_path}")

# ❌ 錯誤
print("開始處理 PDF")
```

### 日誌層級

```python
logger.debug("詳細除錯資訊")      # 開發時使用
logger.info("一般資訊")           # 正常流程
logger.warning("警告訊息")        # 可能的問題
logger.error("錯誤訊息")          # 確定的錯誤
logger.critical("嚴重錯誤")       # 系統崩潰級別
```

---

## 錯誤處理

### 具體的異常處理

```python
# ✅ 正確：捕捉具體異常
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
except FileNotFoundError:
    logger.error(f"檔案不存在：{file_path}")
    return None
except UnicodeDecodeError:
    logger.error(f"檔案編碼錯誤：{file_path}")
    return None

# ❌ 錯誤：捕捉所有異常
try:
    content = open(file_path).read()
except Exception:
    pass
```

### 資源管理

```python
# ✅ 正確：使用 with 語句
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# ✅ 正確：PDF 檔案也要正確關閉
doc = fitz.open(pdf_path)
try:
    # 處理 PDF
    pass
finally:
    doc.close()
```

---

## 註解風格

### 好的註解

```python
# 計算信賴度的加權平均，給予高信賴度更大權重
weighted_avg = sum(c * c for c in confidences) / sum(confidences)

# Bug #123 修復：處理空字串的情況
if not text:
    return ""
```

### 避免的註解

```python
# ❌ 不要寫明顯的註解
x = x + 1  # x 加 1

# ❌ 不要註解掉程式碼（應該刪除）
# old_function()
new_function()

# ✅ 如果需要說明為何註解，使用 FIXME 或 TODO
# TODO: 實作更高效的演演算法
# FIXME: 這個方法在空列表時會出錯
```

---

## 程式碼組織

### 函式長度

- 建議：< 50 行
- 極限：< 100 行
- 超過 100 行應拆分

### 類別長度

- 建議：< 300 行
- 超過 500 行考慮拆分

### 模組長度

- 建議：< 500 行
- 超過 1000 行應拆分
- `paddle_ocr_tool.py` 的 2600 行是技術債

---

## 測試風格

### 測試命名

```python
class TestPDFGenerator:
    """測試 PDFGenerator 類別"""
    
    def test_initialization(self):
        """測試初始化"""
        generator = PDFGenerator("output.pdf")
        assert generator.output_path == "output.pdf"
    
    def test_add_page_with_valid_image(self):
        """測試使用有效圖片新增頁面"""
        # 測試邏輯
        pass
    
    def test_add_page_raises_error_when_image_not_found(self):
        """測試圖片不存在時丟擲錯誤"""
        with pytest.raises(FileNotFoundError):
            generator.add_page("nonexistent.png", [])
```

### Arrange-Act-Assert 模式

```python
def test_process_text(self):
    """測試文書處理"""
    # Arrange（準備）
    input_text = "HelloWorld"
    expected = "Hello World"
    
    # Act（執行）
    result = fix_spacing(input_text)
    
    # Assert（驗證）
    assert result == expected
```

---

## 格式化工具

### 推薦工具

- **Black**：自動格式化（行長 120）
- **isort**：自動排序 import
- **flake8**：程式碼檢查
- **mypy**：型別檢查

### 設定範例（pyproject.toml）

```toml
[tool.black]
line-length = 120
target-version = ['py38', 'py39', 'py310', 'py311', 'py312']

[tool.isort]
profile = "black"
line_length = 120

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
```

---

## 檢查清單 ✓

新程式碼提交前檢查：

- [ ] 所有函式都有型別提示
- [ ] 所有公開 API 都有 docstrings
- [ ] 使用 `logging` 而非 `print()`
- [ ] 異常處理明確且完整
- [ ] import 順序正確
- [ ] 遵循命名規範
- [ ] 行長 < 120 字元
- [ ] 函式長度合理（< 100 行）

---

*編碼風格版本：v1.0*
