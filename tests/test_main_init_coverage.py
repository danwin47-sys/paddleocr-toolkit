# -*- coding: utf-8 -*-
"""
Final coverage push tests - targeting __main__.py and __init__.py
"""
import pytest
from unittest.mock import patch, MagicMock
import sys


def test_main_module_execution():
    """Target __main__.py lines 2-22 (0% coverage)"""
    # Mock the main function to avoid actual execution
    with patch("paddle_ocr_tool.main") as mock_main:
        # Import and execute __main__
        import paddleocr_toolkit.__main__

        # The module should have added parent_dir to sys.path
        assert any("paddleocr-toolkit" in p for p in sys.path)


def test_init_module_imports():
    """Target __init__.py lines 63-74 (53% coverage)"""
    # Test the version and exports
    import paddleocr_toolkit

    assert hasattr(paddleocr_toolkit, "__version__")

    # Test the lazy loading function (lines 63-74)
    from paddleocr_toolkit import get_paddle_ocr_tool

    PaddleOCRFacade = get_paddle_ocr_tool()
    assert PaddleOCRFacade is not None

    # Test other exports
    from paddleocr_toolkit import OCRResult, OCRMode, PDFGenerator

    assert all([OCRResult, OCRMode, PDFGenerator])
