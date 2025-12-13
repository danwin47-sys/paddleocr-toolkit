# -*- coding: utf-8 -*-
"""
OCR Workaround 單元測試
"""

import pytest
import sys
import os

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

from paddleocr_toolkit.processors.ocr_workaround import (
    TextBlock,
    OCRWorkaround,
    detect_scanned_document,
    should_use_ocr_workaround,
)


class TestTextBlock:
    """測試 TextBlock"""
    
    def test_basic_creation(self):
        """測試基本建立"""
        block = TextBlock(
            text="Hello",
            x=10.0,
            y=20.0,
            width=100.0,
            height=30.0
        )
        
        assert block.text == "Hello"
        assert block.x == 10.0
        assert block.y == 20.0
        assert block.width == 100.0
        assert block.height == 30.0
    
    def test_with_color(self):
        """測試指定顏色"""
        block = TextBlock(
            text="Test",
            x=0,
            y=0,
            width=50,
            height=20,
            color=(1, 0, 0)  # 紅色
        )
        
        assert block.color == (1, 0, 0)
    
    def test_default_color(self):
        """測試預設顏色（黑色）"""
        block = TextBlock(text="Test", x=0, y=0, width=50, height=20)
        
        assert block.color == (0, 0, 0)


class TestOCRWorkaround:
    """測試 OCRWorkaround"""
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_initialization(self):
        """測試初始化"""
        workaround = OCRWorkaround()
        
        assert workaround is not None
        assert workaround.margin == 2.0
        assert workaround.force_black is True
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_custom_settings(self):
        """測試自訂設定"""
        workaround = OCRWorkaround(
            margin=5.0,
            force_black=False,
            mask_color=(0.9, 0.9, 0.9)
        )
        
        assert workaround.margin == 5.0
        assert workaround.force_black is False
        assert workaround.mask_color == (0.9, 0.9, 0.9)


class TestDetectScannedDocument:
    """測試 detect_scanned_document"""
    
    def test_nonexistent_file(self):
        """測試不存在的檔案"""
        result = detect_scanned_document("nonexistent.pdf")
        
        # 應該返回 False 而不是拋出錯誤
        assert result is False
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_text_pdf(self):
        """測試有文字的 PDF"""
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            # 建立有大量文字的 PDF
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((100, 100), "This is test text. " * 100)
            doc.save(temp_path)
            doc.close()
            
            result = detect_scanned_document(temp_path)
            
            # 有足夠文字的 PDF 不應該是掃描件
            assert result is False
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestShouldUseOcrWorkaround:
    """測試 should_use_ocr_workaround"""
    
    def test_nonexistent_file(self):
        """測試不存在的檔案"""
        result = should_use_ocr_workaround("nonexistent.pdf")
        
        assert result is False
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_text_pdf(self):
        """測試有文字的 PDF"""
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((100, 100), "Normal text PDF " * 50)
            doc.save(temp_path)
            doc.close()
            
            result = should_use_ocr_workaround(temp_path)
            
            # 有足夠文字的 PDF 不需要 OCR workaround
            assert result is False
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
