# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - 多�??��?件辨識�??��?套件

?��?件使??PaddleOCR 3.x ?��??��?識別，支?��?�?OCR 模�?�?
- basic: PP-OCRv5 ?�本?��?識別
- structure: PP-StructureV3 結�??��?件解??
- vl: PaddleOCR-VL 視覺語�?模�?
- hybrid: 混�?模�?（�??��???+ 精確 OCR�?

使用?��?�?
    # ?��? 1：使??get_paddle_ocr_tool() ?��?類別
    from paddleocr_toolkit import get_paddle_ocr_tool, OCRResult
    PaddleOCRTool = get_paddle_ocr_tool()
    tool = PaddleOCRTool(mode="hybrid")
    
    # ?��? 2：直?��? paddle_ocr_tool ?�入
    from paddle_ocr_tool import PaddleOCRTool
    tool = PaddleOCRTool(mode="hybrid")

?�令?�使?��?
    python -m paddleocr_toolkit input.pdf --mode hybrid
"""

__version__ = "1.2.0"
__author__ = "PaddleOCR Toolkit Team"

# ?��?模�?
from .core.models import (
    SUPPORTED_IMAGE_FORMATS,
    SUPPORTED_PDF_FORMAT,
    OCRMode,
    OCRResult,
)
from .core.pdf_generator import PDFGenerator
from .processors.pdf_quality import detect_pdf_quality

# ?��???
from .processors.text_processor import fix_english_spacing

# 延遲?�入 PaddleOCRTool（避?�循?�相依�?
_paddle_ocr_tool_class = None


def get_paddle_ocr_tool():
    """
    ?��? PaddleOCRTool 類別（延?��??��?

    使用延遲載入以避?�循?��?賴�?

    Returns:
        PaddleOCRTool 類別

    Example:
        PaddleOCRTool = get_paddle_ocr_tool()
        tool = PaddleOCRTool(mode="hybrid")
    """
    global _paddle_ocr_tool_class
    if _paddle_ocr_tool_class is None:
        import os
        import sys

        # 添�??�目?�到路�?
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from paddle_ocr_tool import PaddleOCRTool

        _paddle_ocr_tool_class = PaddleOCRTool
    return _paddle_ocr_tool_class


# ?��? API
__all__ = [
    # ?�本資�?
    "__version__",
    "__author__",
    # ?��?類別
    "OCRResult",
    "OCRMode",
    "PDFGenerator",
    # ?��???
    "fix_english_spacing",
    "detect_pdf_quality",
    # 常數
    "SUPPORTED_IMAGE_FORMATS",
    "SUPPORTED_PDF_FORMAT",
    # 工具?�數（延?��??��?
    "get_paddle_ocr_tool",
]

# 注�?：�??��?試直??import PaddleOCRTool
# ?�避?��?循環依賴?��?
# ?�戶?�使??get_paddle_ocr_tool() ?�直?��? paddle_ocr_tool ?�入
