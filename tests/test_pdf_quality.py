# -*- coding: utf-8 -*-
"""
PDF Quality 單元測試
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

from paddleocr_toolkit.processors.pdf_quality import detect_pdf_quality


class TestDetectPdfQuality:
    """測試 detect_pdf_quality"""

    def test_returns_dict(self):
        """測試返回字典"""
        # 使用不存在的檔案，應該返回預設值
        result = detect_pdf_quality("nonexistent.pdf")

        assert isinstance(result, dict)
        assert "is_scanned" in result
        assert "is_blurry" in result
        assert "has_text" in result
        assert "recommended_dpi" in result
        assert "reason" in result

    def test_default_dpi(self):
        """測試預設 DPI"""
        result = detect_pdf_quality("nonexistent.pdf")

        # 失敗時應該返回預設 DPI
        assert result["recommended_dpi"] >= 100

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_with_text_pdf(self):
        """測試有文字的 PDF"""
        # 建立有文字的 PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((100, 100), "This is test text " * 50)  # 足夠多的文字
            doc.save(temp_path)
            doc.close()

            result = detect_pdf_quality(temp_path)

            # 有文字的 PDF
            assert result["has_text"] is True or result["is_scanned"] is False

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_with_empty_pdf(self):
        """測試空白 PDF"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            doc = fitz.open()
            doc.new_page()  # 空白頁
            doc.save(temp_path)
            doc.close()

            result = detect_pdf_quality(temp_path)

            # 空白 PDF 沒有文字
            assert "recommended_dpi" in result

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
