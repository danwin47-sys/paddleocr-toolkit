# -*- coding: utf-8 -*-
"""
PDF 工具函數單元測試
"""

import pytest
import sys
import os
import numpy as np

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paddleocr_toolkit.core.pdf_utils import (
    pixmap_to_numpy,
    numpy_to_pdf_bytes,
    get_dpi_matrix,
    create_pdf,
    add_image_page,
)


class TestPixmapToNumpy:
    """測試 pixmap_to_numpy"""
    
    def test_basic_conversion(self):
        """測試基本轉換（模擬 Pixmap）"""
        # 建立模擬的 Pixmap 物件
        class MockPixmap:
            def __init__(self):
                self.width = 100
                self.height = 50
                self.n = 3  # RGB
                self.samples = np.zeros((50, 100, 3), dtype=np.uint8).tobytes()
        
        pixmap = MockPixmap()
        result = pixmap_to_numpy(pixmap)
        
        assert result.shape == (50, 100, 3)
        assert result.dtype == np.uint8
    
    def test_rgba_to_rgb(self):
        """測試 RGBA → RGB 轉換"""
        class MockPixmapRGBA:
            def __init__(self):
                self.width = 10
                self.height = 10
                self.n = 4  # RGBA
                self.samples = np.zeros((10, 10, 4), dtype=np.uint8).tobytes()
        
        pixmap = MockPixmapRGBA()
        result = pixmap_to_numpy(pixmap)
        
        assert result.shape == (10, 10, 3)  # 應該是 RGB


class TestNumpyToPdfBytes:
    """測試 numpy_to_pdf_bytes"""
    
    def test_png_format(self):
        """測試 PNG 格式"""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image[50, 50] = [255, 0, 0]  # 紅點
        
        result = numpy_to_pdf_bytes(image, format="PNG")
        
        assert result is not None
        assert result.read(4) == b'\x89PNG'  # PNG 魔術數字
    
    def test_jpeg_format(self):
        """測試 JPEG 格式"""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        result = numpy_to_pdf_bytes(image, format="JPEG", jpeg_quality=85)
        
        assert result is not None
        data = result.read(2)
        assert data == b'\xff\xd8'  # JPEG 魔術數字


class TestGetDpiMatrix:
    """測試 get_dpi_matrix"""
    
    def test_default_dpi(self):
        """測試預設 DPI"""
        try:
            import fitz
            matrix = get_dpi_matrix(150)
            assert matrix is not None
        except ImportError:
            pytest.skip("PyMuPDF not installed")
    
    def test_high_dpi(self):
        """測試高 DPI"""
        try:
            import fitz
            matrix = get_dpi_matrix(300)
            assert matrix is not None
        except ImportError:
            pytest.skip("PyMuPDF not installed")


class TestCreatePdf:
    """測試 create_pdf"""
    
    def test_create_empty_pdf(self):
        """測試建立空白 PDF"""
        try:
            doc = create_pdf()
            assert doc is not None
            assert len(doc) == 0
            doc.close()
        except ImportError:
            pytest.skip("PyMuPDF not installed")


class TestAddImagePage:
    """測試 add_image_page"""
    
    def test_add_page(self):
        """測試添加圖片頁面"""
        try:
            doc = create_pdf()
            image = np.zeros((100, 200, 3), dtype=np.uint8)
            
            page = add_image_page(doc, image)
            
            assert len(doc) == 1
            assert page is not None
            doc.close()
        except ImportError:
            pytest.skip("PyMuPDF not installed")
    
    def test_add_compressed_page(self):
        """測試添加壓縮頁面"""
        try:
            doc = create_pdf()
            image = np.zeros((100, 200, 3), dtype=np.uint8)
            
            page = add_image_page(doc, image, compress=True, jpeg_quality=75)
            
            assert len(doc) == 1
            doc.close()
        except ImportError:
            pytest.skip("PyMuPDF not installed")


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
