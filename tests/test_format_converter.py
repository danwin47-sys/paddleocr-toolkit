# -*- coding: utf-8 -*-
"""
測試 FormatConverter
"""

import os
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest
from paddleocr_toolkit.utils.format_converter import FormatConverter


class TestFormatConverter:
    """測試 FormatConverter 類別"""

    def test_text_to_docx_success(self):
        """測試成功轉換為 DOCX"""
        with patch("docx.Document") as mock_document_cls:
            mock_doc = Mock()
            mock_document_cls.return_value = mock_doc

            result = FormatConverter.text_to_docx("測試文字\n第二行", "output.docx")

            assert result is True
            mock_doc.add_heading.assert_called_with("OCR 辨識結果", 0)
            mock_doc.add_paragraph.assert_any_call("測試文字")
            mock_doc.add_paragraph.assert_any_call("第二行")
            mock_doc.save.assert_called_with("output.docx")

    def test_text_to_docx_failure(self):
        """測試轉換 DOCX 失敗"""
        with patch("docx.Document", side_effect=Exception("Mock Error")):
            result = FormatConverter.text_to_docx("Test", "output.docx")
            assert result is False

    def test_text_to_xlsx_success(self):
        """測試成功轉換為 XLSX"""
        with patch("openpyxl.Workbook") as mock_workbook_cls:
            mock_wb = MagicMock()
            mock_ws = MagicMock()
            mock_wb.active = mock_ws
            mock_workbook_cls.return_value = mock_wb

            # Setup cell Mock for ws['A1'] access
            mock_cell = Mock()
            mock_ws.__getitem__.return_value = mock_cell

            result = FormatConverter.text_to_xlsx("Row 1\nRow 2", "output.xlsx")

            assert result is True
            mock_ws.cell.assert_any_call(row=2, column=1, value="Row 1")
            mock_ws.cell.assert_any_call(row=3, column=1, value="Row 2")
            mock_wb.save.assert_called_with("output.xlsx")

    def test_text_to_xlsx_failure(self):
        """測試轉換 XLSX 失敗"""
        with patch("openpyxl.Workbook", side_effect=Exception("Mock Error")):
            result = FormatConverter.text_to_xlsx("Test", "output.xlsx")
            assert result is False

    def test_text_to_markdown_success(self, tmp_path):
        """測試成功轉換為 Markdown"""
        output_file = tmp_path / "output.md"
        metadata = {"date": "2023-01-01", "pages": 1, "confidence": 0.95}

        result = FormatConverter.text_to_markdown(
            "Markdown Content", str(output_file), metadata
        )

        assert result is True
        content = output_file.read_text(encoding="utf-8")
        assert "# OCR 辨識結果" in content
        assert "**辨識日期**: 2023-01-01" in content
        assert "**頁數**: 1" in content
        assert "**信心度**: 95%" in content
        assert "Markdown Content" in content

    def test_text_to_markdown_simple(self, tmp_path):
        """測試無元數據轉換 Markdown"""
        output_file = tmp_path / "output_simple.md"
        result = FormatConverter.text_to_markdown("Simple Content", str(output_file))
        assert result is True
        content = output_file.read_text(encoding="utf-8")
        assert "Simple Content" in content
        assert "辨識資訊" not in content

    def test_text_to_markdown_failure(self):
        """測試轉換 Markdown 失敗"""
        # 使用無效路徑觸發錯誤
        result = FormatConverter.text_to_markdown("Test", "/invalid/path/output.md")
        assert result is False

    def test_text_to_pdf_searchable_simple(self):
        """測試簡易版 PDF 生成 (無圖片)"""
        with patch("fitz.open") as mock_open:
            mock_doc = Mock()
            mock_page = Mock()
            mock_doc.new_page.return_value = mock_page
            mock_open.return_value = mock_doc

            result = FormatConverter.text_to_pdf_searchable("PDF Content", "output.pdf")

            assert result is True
            mock_page.insert_textbox.assert_called()
            mock_doc.save.assert_called_with("output.pdf")
            mock_doc.close.assert_called()

    def test_text_to_pdf_searchable_full(self):
        """測試完整版 PDF 生成 (有圖片和結果)"""
        with patch("paddleocr_toolkit.core.pdf_generator.PDFGenerator") as mock_gen_cls:
            mock_gen = Mock()
            mock_gen.save.return_value = True
            mock_gen_cls.return_value = mock_gen

            result = FormatConverter.text_to_pdf_searchable(
                "Text",
                "output.pdf",
                image_path="test.jpg",
                ocr_results=[{"text": "abc"}],
            )

            assert result is True
            mock_gen.add_page.assert_called_with("test.jpg", [{"text": "abc"}])
            mock_gen.save.assert_called()

    def test_text_to_pdf_searchable_failure(self):
        """測試 PDF 生成失敗"""
        with patch("fitz.open", side_effect=Exception("Mock Error")):
            result = FormatConverter.text_to_pdf_searchable("Test", "output.pdf")
            assert result is False
