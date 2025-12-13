# -*- coding: utf-8 -*-
"""
PDF Generator 單元測試（擴展版）
"""

import pytest
import sys
import os
import numpy as np
import tempfile

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

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
        assert gen.debug_mode is False
        assert gen.compress_images is False
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_init_with_compression(self):
        """測試壓縮設定"""
        gen = PDFGenerator("test.pdf", compress_images=True, jpeg_quality=75)
        assert gen.compress_images is True
        assert gen.jpeg_quality == 75
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_init_with_debug(self):
        """測試 debug 模式"""
        gen = PDFGenerator("test.pdf", debug_mode=True)
        assert gen.debug_mode is True
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_jpeg_quality_bounds(self):
        """測試 JPEG 品質邊界"""
        gen = PDFGenerator("test.pdf", jpeg_quality=150)  # 超過上限
        assert gen.jpeg_quality == 100
        
        gen2 = PDFGenerator("test.pdf", jpeg_quality=-10)  # 低於下限
        assert gen2.jpeg_quality == 0


class TestPDFGeneratorAddPage:
    """測試添加頁面"""
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_add_page_from_pixmap(self):
        """測試從 Pixmap 添加頁面"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            gen = PDFGenerator(temp_path)
            
            doc = fitz.open()
            page = doc.new_page(width=200, height=100)
            pixmap = page.get_pixmap()
            doc.close()
            
            result = gen.add_page_from_pixmap(pixmap, [])
            
            assert result is True
            assert len(gen.doc) == 1
            assert gen.page_count == 1
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    @pytest.mark.skipif(not HAS_FITZ or not HAS_PIL, reason="Dependencies not installed")
    def test_add_page_from_image_file(self):
        """測試從圖片檔案添加頁面"""
        # 建立測試圖片
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img_path = f.name
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            # 建立簡單圖片
            img = Image.new('RGB', (100, 100), color='white')
            img.save(img_path)
            
            gen = PDFGenerator(pdf_path)
            result = gen.add_page(img_path, [])
            
            assert result is True
            assert gen.page_count == 1
            
        finally:
            for path in [img_path, pdf_path]:
                if os.path.exists(path):
                    os.remove(path)
    
    @pytest.mark.skipif(not HAS_FITZ or not HAS_PIL, reason="Dependencies not installed")
    def test_add_page_with_compression(self):
        """測試壓縮模式添加頁面"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img_path = f.name
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            img = Image.new('RGB', (100, 100), color='red')
            img.save(img_path)
            
            gen = PDFGenerator(pdf_path, compress_images=True, jpeg_quality=50)
            result = gen.add_page(img_path, [])
            
            assert result is True
            
        finally:
            for path in [img_path, pdf_path]:
                if os.path.exists(path):
                    os.remove(path)
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_add_page_nonexistent_file(self):
        """測試添加不存在的檔案"""
        gen = PDFGenerator("test.pdf")
        
        result = gen.add_page("nonexistent.png", [])
        
        assert result is False


class TestPDFGeneratorWithOCR:
    """測試帶 OCR 結果的頁面"""
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_add_page_with_ocr_results(self):
        """測試添加帶 OCR 結果的頁面"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            gen = PDFGenerator(temp_path)
            
            doc = fitz.open()
            page = doc.new_page(width=200, height=100)
            pixmap = page.get_pixmap()
            doc.close()
            
            ocr_results = [
                OCRResult(
                    text="Hello World",
                    confidence=0.95,
                    bbox=[[10, 10], [100, 10], [100, 30], [10, 30]]
                ),
                OCRResult(
                    text="Test",
                    confidence=0.90,
                    bbox=[[10, 50], [50, 50], [50, 70], [10, 70]]
                )
            ]
            
            result = gen.add_page_from_pixmap(pixmap, ocr_results)
            
            assert result is True
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_add_page_with_empty_text(self):
        """測試空文字的 OCR 結果"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            gen = PDFGenerator(temp_path)
            
            doc = fitz.open()
            page = doc.new_page(width=100, height=100)
            pixmap = page.get_pixmap()
            doc.close()
            
            ocr_results = [
                OCRResult(
                    text="   ",  # 空白文字
                    confidence=0.95,
                    bbox=[[10, 10], [50, 10], [50, 30], [10, 30]]
                )
            ]
            
            result = gen.add_page_from_pixmap(pixmap, ocr_results)
            assert result is True
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestPDFGeneratorSave:
    """測試儲存功能"""
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_save_pdf(self):
        """測試儲存 PDF"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            gen = PDFGenerator(temp_path)
            
            doc = fitz.open()
            page = doc.new_page(width=100, height=100)
            pixmap = page.get_pixmap()
            doc.close()
            
            gen.add_page_from_pixmap(pixmap, [])
            
            result = gen.save()
            
            assert result is True
            assert os.path.exists(temp_path)
            
            # 驗證 PDF 可以開啟
            saved_doc = fitz.open(temp_path)
            assert len(saved_doc) == 1
            saved_doc.close()
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_save_empty_pdf(self):
        """測試儲存空 PDF"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            gen = PDFGenerator(temp_path)
            
            # 沒有添加頁面就儲存
            result = gen.save()
            
            # 空 PDF 儲存應該回傳 False
            assert result is False
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_save_multiple_pages(self):
        """測試儲存多頁 PDF"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            gen = PDFGenerator(temp_path)
            
            # 添加多頁
            for i in range(3):
                doc = fitz.open()
                page = doc.new_page(width=100, height=100)
                pixmap = page.get_pixmap()
                doc.close()
                gen.add_page_from_pixmap(pixmap, [])
            
            result = gen.save()
            
            assert result is True
            assert gen.page_count == 3
            
            # 驗證 PDF 可以開啟
            saved_doc = fitz.open(temp_path)
            assert len(saved_doc) == 3
            saved_doc.close()
            
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
        
        assert result.x == 0
        assert result.y == 0
        assert result.width == 100
        assert result.height == 50
    
    def test_rotated_bbox(self):
        """測試旋轉的邊界框"""
        result = OCRResult(
            text="test",
            confidence=0.9,
            bbox=[[10, 20], [110, 30], [108, 80], [8, 70]]
        )
        
        assert result.x == 8
        assert result.y == 20


class TestMissingDependencies:
    """測試缺少依賴時的行為"""
    
    def test_init_without_fitz(self, monkeypatch):
        """測試缺少 PyMuPDF 時拋出錯誤"""
        import paddleocr_toolkit.core.pdf_generator as module
        monkeypatch.setattr(module, "HAS_FITZ", False)
        
        with pytest.raises(ImportError, match="PyMuPDF"):
            PDFGenerator("test.pdf")
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_add_page_without_pil(self, monkeypatch):
        """測試缺少 Pillow 時的降級行為"""
        import paddleocr_toolkit.core.pdf_generator as module
        monkeypatch.setattr(module, "HAS_PIL", False)
        
        gen = PDFGenerator("test.pdf")
        result = gen.add_page("test.png", [])
        
        # 應該返回 False
        assert result is False


class TestImageFormats:
    """測試不同圖片格式"""
    
    @pytest.mark.skipif(not HAS_FITZ or not HAS_PIL, reason="Dependencies not installed")
    def test_add_page_rgba_image(self):
        """測試 RGBA 圖片（有 alpha 通道）"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img_path = f.name
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            # 建立 RGBA 圖片
            img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
            img.save(img_path)
            
            gen = PDFGenerator(pdf_path, compress_images=True)
            result = gen.add_page(img_path, [])
            
            # 應該成功轉換為 RGB
            assert result is True
            
        finally:
            for path in [img_path, pdf_path]:
                if os.path.exists(path):
                    os.remove(path)
    
    @pytest.mark.skipif(not HAS_FITZ or not HAS_PIL, reason="Dependencies not installed")
    def test_add_page_grayscale_image(self):
        """測試灰階圖片"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img_path = f.name
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            # 建立灰階圖片
            img = Image.new('L', (100, 100), color=128)
            img.save(img_path)
            
            gen = PDFGenerator(pdf_path, compress_images=True)
            result = gen.add_page(img_path, [])
            
            # 應該成功轉換為 RGB
            assert result is True
            
        finally:
            for path in [img_path, pdf_path]:
                if os.path.exists(path):
                    os.remove(path)


class TestPixmapCompression:
    """測試 Pixmap 壓縮"""
    
    @pytest.mark.skipif(not HAS_FITZ or not HAS_PIL, reason="Dependencies not installed")
    def test_add_page_from_pixmap_with_compression(self):
        """測試從 pixmap 新增頁面並壓縮"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            gen = PDFGenerator(temp_path, compress_images=True, jpeg_quality=60)
            
            doc = fitz.open()
            page = doc.new_page(width=200, height=100)
            pixmap = page.get_pixmap()
            doc.close()
            
            result = gen.add_page_from_pixmap(pixmap, [])
            
            assert result is True
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestTextInsertionEdgeCases:
    """測試文字插入的邊界條件"""
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_very_small_text_area(self):
        """測試極小的文字區域"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            gen = PDFGenerator(temp_path)
            
            doc = fitz.open()
            page = doc.new_page(width=100, height=100)
            pixmap = page.get_pixmap()
            doc.close()
            
            # 極小的文字區域（高度 < 6）
            ocr_results = [
                OCRResult(
                    text="T",
                    confidence=0.9,
                    bbox=[[10, 10], [15, 10], [15, 12], [10, 12]]  # 高度只有 2
                )
            ]
            
            result = gen.add_page_from_pixmap(pixmap, ocr_results)
            assert result is True
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_very_large_text_area(self):
        """測試極大的文字區域"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            gen = PDFGenerator(temp_path)
            
            doc = fitz.open()
            page = doc.new_page(width=500, height=500)
            pixmap = page.get_pixmap()
            doc.close()
            
            # 極大的文字區域（高度 > 150）
            ocr_results = [
                OCRResult(
                    text="LARGE",
                    confidence=0.9,
                    bbox=[[10, 10], [400, 10], [400, 200], [10, 200]]  # 高度 190
                )
            ]
            
            result = gen.add_page_from_pixmap(pixmap, ocr_results)
            assert result is True
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_debug_mode_text_insertion(self):
        """測試 debug 模式的文字插入（粉紅色文字）"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            gen = PDFGenerator(temp_path, debug_mode=True)
            
            doc = fitz.open()
            page = doc.new_page(width=100, height=100)
            pixmap = page.get_pixmap()
            doc.close()
            
            ocr_results = [
                OCRResult(
                    text="DEBUG",
                    confidence=0.9,
                    bbox=[[10, 10], [50, 10], [50, 30], [10, 30]]
                )
            ]
            
            result = gen.add_page_from_pixmap(pixmap, ocr_results)
            assert result is True
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)



# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
