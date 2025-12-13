# -*- coding: utf-8 -*-
"""
PDF Generator 單元測試
"""

import pytest
import sys
import os
import numpy as np

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

from paddleocr_toolkit.core.pdf_generator import PDFGenerator
from paddleocr_toolkit.core.models import OCRResult


class TestPDFGeneratorInit:
    """測試 PDFGenerator 初始化"""
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_basic_init(self):
        """測試基本初始化"""
        gen = PDFGenerator("test_output.pdf")
        assert gen is not None
        assert gen.output_path == "test_output.pdf"
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_init_with_compression(self):
        """測試壓縮設定"""
        gen = PDFGenerator("test.pdf", compress_images=True, jpeg_quality=75)
        assert gen.compress_images is True
        assert gen.jpeg_quality == 75


class TestPDFGeneratorAddPage:
    """測試添加頁面"""
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_add_page_from_pixmap(self):
        """測試從 Pixmap 添加頁面"""
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            gen = PDFGenerator(temp_path)
            
            # 建立測試 Pixmap
            doc = fitz.open()
            page = doc.new_page(width=200, height=100)
            pixmap = page.get_pixmap()
            doc.close()
            
            # 添加頁面
            result = gen.add_page_from_pixmap(pixmap, [])
            
            assert result is True
            assert len(gen.doc) == 1
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestPDFGeneratorSave:
    """測試儲存功能"""
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_save_pdf(self):
        """測試儲存 PDF"""
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            gen = PDFGenerator(temp_path)
            
            # 添加一頁
            doc = fitz.open()
            page = doc.new_page(width=100, height=100)
            pixmap = page.get_pixmap()
            doc.close()
            
            gen.add_page_from_pixmap(pixmap, [])
            
            # 儲存
            result = gen.save()
            
            assert result is True
            assert os.path.exists(temp_path)
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestOCRResultProperties:
    """測試 OCRResult 屬性計算"""
    
    def test_center_calculation(self):
        """測試中心點計算"""
        result = OCRResult(
            text="test",
            confidence=0.9,
            bbox=[[0, 0], [100, 0], [100, 50], [0, 50]]
        )
        
        # x, y, width, height
        assert result.x == 0
        assert result.y == 0
        assert result.width == 100
        assert result.height == 50
    
    def test_rotated_bbox(self):
        """測試旋轉的邊界框"""
        # 斜向邊界框
        result = OCRResult(
            text="test",
            confidence=0.9,
            bbox=[[10, 20], [110, 30], [108, 80], [8, 70]]
        )
        
        # 應該正確計算
        assert result.x == 8  # min x
        assert result.y == 20  # min y


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
