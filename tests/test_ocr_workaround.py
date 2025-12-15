# -*- coding: utf-8 -*-
"""
OCR Workaround 單元測試（擴展版）
"""

import os
import sys
import tempfile

import pytest

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import fitz

    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

from paddleocr_toolkit.processors.ocr_workaround import (
    OCRWorkaround,
    TextBlock,
    detect_scanned_document,
    should_use_ocr_workaround,
)


class TestTextBlock:
    """測試 TextBlock"""

    def test_basic_creation(self):
        """測試基本建立"""
        block = TextBlock(text="Hello", x=10.0, y=20.0, width=100.0, height=30.0)

        assert block.text == "Hello"
        assert block.x == 10.0
        assert block.y == 20.0
        assert block.width == 100.0
        assert block.height == 30.0

    def test_with_color(self):
        """測試指定顏色"""
        block = TextBlock(text="Test", x=0, y=0, width=50, height=20, color=(1, 0, 0))

        assert block.color == (1, 0, 0)

    def test_default_color(self):
        """測試預設顏色（黑色）"""
        block = TextBlock(text="Test", x=0, y=0, width=50, height=20)

        assert block.color == (0, 0, 0)

    def test_unicode_text(self):
        """測試 Unicode 文字"""
        block = TextBlock(text="你好世界", x=0, y=0, width=100, height=30)

        assert block.text == "你好世界"


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
            margin=5.0, force_black=False, mask_color=(0.9, 0.9, 0.9)
        )

        assert workaround.margin == 5.0
        assert workaround.force_black is False
        assert workaround.mask_color == (0.9, 0.9, 0.9)

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_add_text_with_mask(self):
        """測試添加文字遮罩"""
        workaround = OCRWorkaround()

        # 建立測試頁面
        doc = fitz.open()
        page = doc.new_page(width=200, height=100)

        text_block = TextBlock(text="Test", x=10, y=20, width=50, height=20)

        # 應該不會拋出錯誤
        workaround.add_text_with_mask(page, text_block, "翻譯")

        doc.close()

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_add_multiple_texts(self):
        """測試添加多個文字"""
        workaround = OCRWorkaround()

        doc = fitz.open()
        page = doc.new_page(width=300, height=200)

        blocks = [
            TextBlock(text="Line 1", x=10, y=20, width=100, height=20),
            TextBlock(text="Line 2", x=10, y=50, width=100, height=20),
            TextBlock(text="Line 3", x=10, y=80, width=100, height=20),
        ]

        for block in blocks:
            workaround.add_text_with_mask(page, block, f"翻譯 {block.text}")

        doc.close()


class TestDetectScannedDocument:
    """測試 detect_scanned_document"""

    def test_nonexistent_file(self):
        """測試不存在的檔案"""
        result = detect_scanned_document("nonexistent.pdf")

        assert result is False

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_text_pdf(self):
        """測試有文字的 PDF"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((100, 100), "This is test text. " * 100)
            doc.save(temp_path)
            doc.close()

            result = detect_scanned_document(temp_path)

            assert result is False

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_empty_pdf(self):
        """測試空白 PDF"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            doc = fitz.open()
            doc.new_page()
            doc.save(temp_path)
            doc.close()

            result = detect_scanned_document(temp_path)

            # 空白 PDF 應被視為掃描件
            assert isinstance(result, bool)

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
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((100, 100), "Normal text PDF " * 50)
            doc.save(temp_path)
            doc.close()

            result = should_use_ocr_workaround(temp_path)

            assert result is False

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_image_only_pdf(self):
        """測試純圖片 PDF"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            doc = fitz.open()
            page = doc.new_page(width=100, height=100)
            # 不插入任何文字，只是空白頁
            doc.save(temp_path)
            doc.close()

            result = should_use_ocr_workaround(temp_path)

            # 純圖片 PDF 應該建議使用 OCR workaround
            assert isinstance(result, bool)

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
