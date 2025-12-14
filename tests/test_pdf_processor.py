# -*- coding: utf-8 -*-
"""
PDF 處理器測試
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from paddleocr_toolkit.processors.pdf_processor import PDFProcessor
from paddleocr_toolkit.core.models import OCRResult


class TestPDFProcessor:
    """測試 PDF 處理器"""
    
    def test_init(self):
        """測試初始化"""
        mock_ocr = Mock()
        processor = PDFProcessor(ocr_func=mock_ocr)
        
        assert processor.ocr_func == mock_ocr
        assert processor.debug_mode is False
    
    def test_get_text(self):
        """測試提取文字"""
        mock_ocr = Mock()
        processor = PDFProcessor(ocr_func=mock_ocr)
        
        results = [
            OCRResult("Hello", 0.95, [[0, 0], [100, 0], [100, 50], [0, 50]]),
            OCRResult("World", 0.92, [[0, 60], [100, 60], [100, 110], [0, 110]]),
        ]
        
        text = processor.get_text(results)
        assert text == "Hello\nWorld"
    
    def test_get_text_custom_separator(self):
        """測試自定義分隔符"""
        mock_ocr = Mock()
        processor = PDFProcessor(ocr_func=mock_ocr)
        
        results = [
            OCRResult("Line1", 0.95, [[0, 0], [100, 0], [100, 50], [0, 50]]),
            OCRResult("Line2", 0.92, [[0, 60], [100, 60], [100, 110], [0, 110]]),
        ]
        
        text = processor.get_text(results, separator=" ")
        assert text == "Line1 Line2"
    
    def test_extract_all_text(self):
        """測試提取所有頁面文字"""
        mock_ocr = Mock()
        processor = PDFProcessor(ocr_func=mock_ocr)
        
        all_results = [
            [OCRResult("Page1", 0.95, [[0, 0], [100, 0], [100, 50], [0, 50]])],
            [OCRResult("Page2", 0.92, [[0, 0], [100, 0], [100, 50], [0, 50]])],
        ]
        
        text = processor.extract_all_text(all_results)
        
        assert "=== 第 1 頁 ===" in text
        assert "Page1" in text
        assert "=== 第 2 頁 ===" in text
        assert "Page2" in text
