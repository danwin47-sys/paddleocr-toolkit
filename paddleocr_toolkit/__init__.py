# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - 專業級文件辨識與處理套件 (v3.3.0)

本套件使用 PaddleOCR 3.x 實現文字識別，支援多種 OCR 模式:
- basic: PP-OCRv5 基本文字識別
- structure: PP-StructureV3 結構化文件解析
- vl: PaddleOCR-VL 視覺語言模型
- hybrid: 混合模式（版面分析 + 精確 OCR）
- gemini: 整合 Gemini 3 語義校正
- claude: 整合 Claude 3.5 語義校正

使用範例:
    # 方法 1: 使用 get_paddle_ocr_tool() 取得類別
    from paddleocr_toolkit import get_paddle_ocr_tool, OCRResult
    PaddleOCRTool = get_paddle_ocr_tool()
    tool = PaddleOCRTool(mode="hybrid")

    # 方法 2: 直接從 paddle_ocr_tool 導入
    from paddle_ocr_tool import PaddleOCRTool
    tool = PaddleOCRTool(mode="hybrid")

命令列使用:
    python -m paddleocr_toolkit input.pdf --mode hybrid
"""

__version__ = "3.3.0"
__author__ = "Danwin47"


# ?��?模�?
from .core.models import (
    SUPPORTED_IMAGE_FORMATS,
    SUPPORTED_PDF_FORMAT,
    OCRMode,
    OCRResult,
)
from .core.pdf_generator import PDFGenerator
from .processors.pdf_quality import detect_pdf_quality

# 處理器
from .processors.text_processor import fix_english_spacing

# 延遲載入 PaddleOCRFacade（避免循環依賴）
_paddle_ocr_facade_class = None


def get_paddle_ocr_tool():
    """
    取得 PaddleOCRFacade 類別（延遲載入）

    使用延遲載入以避免循環依賴問題。
    注意：此函式現在返回現代化的 PaddleOCRFacade，而非遺留的 PaddleOCRTool。

    Returns:
        PaddleOCRFacade 類別

    Example:
        PaddleOCRFacade = get_paddle_ocr_tool()
        tool = PaddleOCRFacade(mode="hybrid")
    """
    global _paddle_ocr_facade_class
    if _paddle_ocr_facade_class is None:
        import os
        import sys

        # 添加父目錄到路徑
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from paddle_ocr_facade import PaddleOCRFacade

        _paddle_ocr_facade_class = PaddleOCRFacade
    return _paddle_ocr_facade_class


# 公開 API
__all__ = [
    # 基本資訊
    "__version__",
    "__author__",
    # 核心類別
    "OCRResult",
    "OCRMode",
    "PDFGenerator",
    # 處理器
    "fix_english_spacing",
    "detect_pdf_quality",
    # 常數
    "SUPPORTED_IMAGE_FORMATS",
    "SUPPORTED_PDF_FORMAT",
    # 工具函數（延遲載入）
    "get_paddle_ocr_tool",
]

# 注意：請勿嘗試直接 import PaddleOCRTool
# 為避免循環依賴問題
# 用戶應使用 get_paddle_ocr_tool() 或直接從 paddle_ocr_facade 導入
