# -*- coding: utf-8 -*-
"""
PDF 工具函式單元測試
"""

import os
import sys

import numpy as np
import pytest

# 新增專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paddleocr_toolkit.core.pdf_utils import (
    add_image_page,
    create_pdf,
    get_dpi_matrix,
    numpy_to_pdf_bytes,
    pixmap_to_numpy,
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
        assert result.read(4) == b"\x89PNG"  # PNG 魔術數字

    def test_jpeg_format(self):
        """測試 JPEG 格式"""
        image = np.zeros((100, 100, 3), dtype=np.uint8)

        result = numpy_to_pdf_bytes(image, format="JPEG", jpeg_quality=85)

        assert result is not None
        data = result.read(2)
        assert data == b"\xff\xd8"  # JPEG 魔術數字


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
        """測試新增圖片頁面"""
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
        """測試新增壓縮頁面"""
        try:
            doc = create_pdf()
            image = np.zeros((100, 200, 3), dtype=np.uint8)

            page = add_image_page(doc, image, compress=True, jpeg_quality=75)

            assert len(doc) == 1
            doc.close()
        except ImportError:
            pytest.skip("PyMuPDF not installed")


class TestMissingDependencies:
    """測試缺少依賴時的錯誤處理"""

    def test_numpy_to_pdf_bytes_without_pil(self, monkeypatch):
        """測試缺少 Pillow 時丟擲錯誤"""
        import paddleocr_toolkit.core.pdf_utils as module

        monkeypatch.setattr(module, "HAS_PIL", False)

        image = np.zeros((100, 100, 3), dtype=np.uint8)

        with pytest.raises(ImportError, match="Pillow"):
            numpy_to_pdf_bytes(image)

    def test_add_image_page_without_fitz(self, monkeypatch):
        """測試缺少 PyMuPDF 時丟擲錯誤"""
        import paddleocr_toolkit.core.pdf_utils as module

        monkeypatch.setattr(module, "HAS_FITZ", False)

        image = np.zeros((100, 100, 3), dtype=np.uint8)

        with pytest.raises(ImportError, match="PyMuPDF"):
            from paddleocr_toolkit.core.pdf_utils import add_image_page

            add_image_page(None, image)

    def test_add_image_page_without_pil(self, monkeypatch):
        """測試 add_image_page 缺少 Pillow 時丟擲錯誤"""
        import paddleocr_toolkit.core.pdf_utils as module

        monkeypatch.setattr(module, "HAS_PIL", False)

        image = np.zeros((100, 100, 3), dtype=np.uint8)

        with pytest.raises(ImportError, match="Pillow"):
            from paddleocr_toolkit.core.pdf_utils import add_image_page

            add_image_page(None, image)


class TestRGBAConversion:
    """測試 RGBA 圖片轉換"""

    def test_numpy_to_pdf_bytes_rgba(self):
        """測試 RGBA numpy 陣列轉換為 JPEG"""
        # 建立 RGBA 圖片
        image = np.zeros((100, 100, 4), dtype=np.uint8)
        image[:, :, 3] = 255  # Alpha 通道

        # 使用 PIL 轉換
        from PIL import Image as PILImage

        pil_image = PILImage.fromarray(image, mode="RGBA")

        # 轉換為 numpy RGB（移除 alpha）
        rgb_image = np.array(pil_image.convert("RGB"))

        result = numpy_to_pdf_bytes(rgb_image, format="JPEG")

        assert result is not None
        data = result.read(2)
        assert data == b"\xff\xd8"  # JPEG 魔術數字


class TestAdditionalUtilities:
    """測試其他工具函式"""

    def test_page_to_numpy(self):
        """測試 page_to_numpy"""
        try:
            import fitz

            from paddleocr_toolkit.core.pdf_utils import page_to_numpy

            doc = fitz.open()
            page = doc.new_page(width=100, height=100)

            result = page_to_numpy(page, dpi=150)

            assert result is not None
            assert isinstance(result, np.ndarray)
            assert result.ndim == 3

            doc.close()
        except ImportError:
            pytest.skip("PyMuPDF not installed")

    def test_get_page_size(self):
        """測試 get_page_size"""
        try:
            import fitz

            from paddleocr_toolkit.core.pdf_utils import get_page_size

            doc = fitz.open()
            page = doc.new_page(width=200, height=300)

            width, height = get_page_size(page)

            assert width == 200
            assert height == 300

            doc.close()
        except ImportError:
            pytest.skip("PyMuPDF not installed")

    def test_copy_page(self):
        """測試 copy_page"""
        try:
            import fitz

            from paddleocr_toolkit.core.pdf_utils import copy_page

            src_doc = fitz.open()
            dst_doc = fitz.open()

            # 在來原始檔建立一頁
            src_doc.new_page(width=100, height=100)

            # 複製到目標檔案
            result_page = copy_page(src_doc, dst_doc, 0)

            assert len(dst_doc) == 1
            assert result_page is not None

            src_doc.close()
            dst_doc.close()
        except ImportError:
            pytest.skip("PyMuPDF not installed")


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
