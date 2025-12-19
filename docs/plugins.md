# PaddleOCR Toolkit 外掛開發指南

本指南將協助您開發 PaddleOCR Toolkit 的外掛，以擴充系統功能。

## 🔌 外掛架構

PaddleOCR Toolkit 的外掛系統基於 `OCRPlugin` 基類。外掛可以在 OCR 處理的兩個關鍵階段介入：

1. **前處理 (Pre-processing)**: 在圖片送入 OCR 引擎之前，對圖片進行修改（例如：旋轉、降噪、裁切）。
2. **後處理 (Post-processing)**: 在 OCR 引擎產生結果之後，對結果進行修改或分析（例如：過濾敏感詞、統計資料、格式轉換）。

## 🚀 快速開始

### 1. 建立外掛檔案

在 `paddleocr_toolkit/plugins/` 目錄下建立一個新的 Python 檔案，例如 `my_plugin.py`。

### 2. 繼承 OCRPlugin

您的外掛類別必須繼承自 `paddleocr_toolkit.plugins.base.OCRPlugin`。

```python
from typing import Any
from paddleocr_toolkit.plugins.base import OCRPlugin

class MyCustomPlugin(OCRPlugin):
    # 定義外掛後設資料
    name = "MyCustomPlugin"
    version = "1.0.0"
    author = "Your Name"
    description = "這是一個範例外掛"

    def on_init(self) -> bool:
        """初始化外掛"""
        self.logger.info("外掛已初始化")
        return True

    def on_before_ocr(self, image: Any) -> Any:
        """
        OCR 前處理鉤子
        
        Args:
            image: 輸入圖片 (通常是 numpy array 或檔案路徑)
            
        Returns:
            處理後的圖片
        """
        # 在這裡處理圖片...
        return image

    def on_after_ocr(self, results: Any) -> Any:
        """
        OCR 後處理鉤子
        
        Args:
            results: OCR 引擎的原始輸出
            
        Returns:
            處理後的結果
        """
        # 在這裡處理結果...
        self.logger.info(f"OCR 完成，結果長度: {len(results)}")
        return results
```

## 📖 API 參考

### `OCRPlugin` 方法

* `on_init(self) -> bool`: 外掛載入時呼叫。若返回 `False`，外掛將不會被啟用。
* `on_before_ocr(self, image: Any) -> Any`: OCR 執行前呼叫。您必須返回圖片物件（即使未修改）。
* `on_after_ocr(self, results: Any) -> Any`: OCR 執行後呼叫。您必須返回結果物件（即使未修改）。
* `on_error(self, error: Exception) -> None`: 當處理過程中發生錯誤時呼叫。
* `on_shutdown(self) -> None`: 系統關閉或外掛解除安裝時呼叫。

## 💡 最佳實踐

1. **錯誤處理**: 盡量在外掛內部捕獲並處理異常，避免讓單一外掛的錯誤導致整個 OCR 流程崩潰。
2. **效能**: 避免在鉤子中執行耗時的操作（如網路請求），這會拖慢 OCR 的速度。
3. **日誌**: 使用 `self.logger` 記錄重要資訊，方便除錯。

## 📦 安裝外掛

只需將您的 `.py` 檔案放入 `paddleocr_toolkit/plugins/` 目錄，系統啟動時會自動發現並載入。
