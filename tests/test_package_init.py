# -*- coding: utf-8 -*-
"""
paddleocr_toolkit 套件初始化測試
"""

import os
import sys

import pytest

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPackageInit:
    """測試套件初始化"""

    def test_import_package(self):
        """測試匯入套件"""
        import paddleocr_toolkit

        assert paddleocr_toolkit is not None

    def test_version(self):
        """測試版本資訊"""
        from paddleocr_toolkit import __author__, __version__

        assert __version__ == "1.0.0"
        assert __author__ == "PaddleOCR Toolkit Team"

    def test_import_core_models(self):
        """測試匯入核心模型"""
        from paddleocr_toolkit import (SUPPORTED_IMAGE_FORMATS,
                                       SUPPORTED_PDF_FORMAT, OCRMode,
                                       OCRResult)

        assert OCRResult is not None
        assert OCRMode is not None

    def test_import_pdf_generator(self):
        """測試匯入 PDFGenerator"""
        from paddleocr_toolkit import PDFGenerator

        assert PDFGenerator is not None

    def test_import_processors(self):
        """測試匯入處理器"""
        from paddleocr_toolkit import detect_pdf_quality, fix_english_spacing

        assert fix_english_spacing is not None
        assert detect_pdf_quality is not None

    def test_get_paddle_ocr_tool_function(self):
        """測試 get_paddle_ocr_tool 函數存在"""
        from paddleocr_toolkit import get_paddle_ocr_tool

        assert callable(get_paddle_ocr_tool)

    def test_all_exports(self):
        """測試 __all__ 匯出"""
        import paddleocr_toolkit

        expected = [
            "__version__",
            "__author__",
            "OCRResult",
            "OCRMode",
            "PDFGenerator",
            "fix_english_spacing",
            "detect_pdf_quality",
            "SUPPORTED_IMAGE_FORMATS",
            "SUPPORTED_PDF_FORMAT",
            "get_paddle_ocr_tool",
        ]

        for name in expected:
            assert name in paddleocr_toolkit.__all__


class TestCoreImports:
    """測試核心模組匯入"""

    def test_import_from_core(self):
        """測試從 core 匯入"""
        from paddleocr_toolkit.core import (OCRMode, OCRResult, PDFGenerator,
                                            load_config, pixmap_to_numpy)

        assert OCRResult is not None
        assert load_config is not None


class TestProcessorImports:
    """測試處理器匯入"""

    def test_import_from_processors(self):
        """測試從 processors 匯入"""
        from paddleocr_toolkit.processors import (StatsCollector, TextBlock,
                                                  detect_pdf_quality,
                                                  fix_english_spacing)

        assert fix_english_spacing is not None
        assert StatsCollector is not None


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
