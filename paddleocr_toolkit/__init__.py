# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - 多功能文件辨識與處理套件

本套件使用 PaddleOCR 3.x 進行文字識別，支援多種 OCR 模式：
- basic: PP-OCRv5 基本文字識別
- structure: PP-StructureV3 結構化文件解析
- vl: PaddleOCR-VL 視覺語言模型
- hybrid: 混合模式（版面分析 + 精確 OCR）

使用方法：
    # 方式 1：使用 get_paddle_ocr_tool() 取得類別
    from paddleocr_toolkit import get_paddle_ocr_tool, OCRResult
    PaddleOCRTool = get_paddle_ocr_tool()
    tool = PaddleOCRTool(mode="hybrid")
    
    # 方式 2：直接從 paddle_ocr_tool 匯入
    from paddle_ocr_tool import PaddleOCRTool
    tool = PaddleOCRTool(mode="hybrid")

命令列使用：
    python -m paddleocr_toolkit input.pdf --mode hybrid
"""

__version__ = "1.0.0"
__author__ = "PaddleOCR Toolkit Team"

# 核心模組
from .core.models import (SUPPORTED_IMAGE_FORMATS, SUPPORTED_PDF_FORMAT,
                          OCRMode, OCRResult)
from .core.pdf_generator import PDFGenerator
from .processors.pdf_quality import detect_pdf_quality
# 處理器
from .processors.text_processor import fix_english_spacing

# 延遲匯入 PaddleOCRTool（避免循環相依）
_paddle_ocr_tool_class = None


def get_paddle_ocr_tool():
    """
    取得 PaddleOCRTool 類別（延遲載入）

    使用延遲載入以避免循環依賴。

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

        # 添加父目錄到路徑
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from paddle_ocr_tool import PaddleOCRTool

        _paddle_ocr_tool_class = PaddleOCRTool
    return _paddle_ocr_tool_class


# 公開 API
__all__ = [
    # 版本資訊
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

# 注意：不再嘗試直接 import PaddleOCRTool
# 這避免了循環依賴問題
# 用戶應使用 get_paddle_ocr_tool() 或直接從 paddle_ocr_tool 匯入
