"""自定義異常類

這個模組定義了 PaddleOCR Toolkit 的所有自定義異常，
提供更精確的錯誤處理和更好的調試體驗。

使用範例:
    from paddleocr_toolkit.exceptions import FileProcessingError
    
    if not file.exists():
        raise FileProcessingError(f"File not found: {file}")
"""


class OCRToolkitError(Exception):
    """所有自定義異常的基類"""

    pass


class FileProcessingError(OCRToolkitError):
    """文件處理相關錯誤

    當文件讀取、寫入或轉換失敗時拋出
    """

    pass


class OCRProcessingError(OCRToolkitError):
    """OCR 處理相關錯誤

    當 OCR 引擎處理失敗時拋出
    """

    pass


class ModelLoadError(OCRToolkitError):
    """模型加載錯誤

    當 PaddleOCR 模型無法加載時拋出
    """

    pass


class ConfigurationError(OCRToolkitError):
    """配置錯誤

    當配置文件或環境變數有問題時拋出
    """

    pass


class APIError(OCRToolkitError):
    """API 調用錯誤

    當外部 API（如 Gemini、Claude）調用失敗時拋出
    """

    pass


__all__ = [
    "OCRToolkitError",
    "FileProcessingError",
    "OCRProcessingError",
    "ModelLoadError",
    "ConfigurationError",
    "APIError",
]
