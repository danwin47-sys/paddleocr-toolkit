# -*- coding: utf-8 -*-
"""
PDF 處理器測試
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from paddleocr_toolkit.core.models import OCRResult
from paddleocr_toolkit.processors.pdf_processor import PDFProcessor


class TestPDFProcessorInit:
    """測試初始化"""

    def test_init_basic(self):
        """測試基本初始化"""
        mock_ocr = Mock()
        processor = PDFProcessor(ocr_func=mock_ocr)

        assert processor.ocr_func == mock_ocr
        assert processor.debug_mode is False
        assert processor.result_parser is None

    def test_init_with_parser(self):
        """測試帶解析器的初始化"""
        mock_ocr = Mock()
        mock_parser = Mock()

        processor = PDFProcessor(ocr_func=mock_ocr, result_parser=mock_parser)

        assert processor.result_parser == mock_parser

    def test_init_with_debug(self):
        """測試DEBUG模式初始化"""
        mock_ocr = Mock()
        processor = PDFProcessor(ocr_func=mock_ocr, debug_mode=True)

        assert processor.debug_mode is True


class TestGetText:
    """測試文字提取"""

    def test_get_text_basic(self):
        """測試基本文字提取"""
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

    def test_get_text_empty_results(self):
        """測試空結果"""
        mock_ocr = Mock()
        processor = PDFProcessor(ocr_func=mock_ocr)

        text = processor.get_text([])
        assert text == ""

    def test_get_text_skip_empty(self):
        """測試跳過空文字"""
        mock_ocr = Mock()
        processor = PDFProcessor(ocr_func=mock_ocr)

        results = [
            OCRResult("Text", 0.95, [[0, 0], [100, 0], [100, 50], [0, 50]]),
            OCRResult("  ", 0.92, [[0, 60], [100, 60], [100, 110], [0, 110]]),
            OCRResult("More", 0.90, [[0, 120], [100, 120], [100, 170], [0, 170]]),
        ]

        text = processor.get_text(results)
        assert text == "Text\nMore"


class TestExtractAllText:
    """測試提取所有文字"""

    def test_extract_all_text_basic(self):
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

    def test_extract_all_text_custom_separator(self):
        """測試自定義頁面分隔符"""
        mock_ocr = Mock()
        processor = PDFProcessor(ocr_func=mock_ocr)

        all_results = [
            [OCRResult("Text1", 0.95, [[0, 0], [100, 0], [100, 50], [0, 50]])],
            [OCRResult("Text2", 0.92, [[0, 0], [100, 0], [100, 50], [0, 50]])],
        ]

        text = processor.extract_all_text(all_results, page_separator="\n---\n")
        assert "\n---\n" in text

    def test_extract_all_text_skip_empty_pages(self):
        """測試跳過空頁"""
        mock_ocr = Mock()
        processor = PDFProcessor(ocr_func=mock_ocr)

        all_results = [
            [OCRResult("Page1", 0.95, [[0, 0], [100, 0], [100, 50], [0, 50]])],
            [],  # 空頁
            [OCRResult("Page3", 0.92, [[0, 0], [100, 0], [100, 50], [0, 50]])],
        ]

        text = processor.extract_all_text(all_results)
        assert "=== 第 1 頁 ===" in text
        assert "=== 第 2 頁 ===" not in text  # 跳過
        assert "=== 第 3 頁 ===" in text


class TestSetupPDFGenerator:
    """測試PDF生成器設定"""

    def test_setup_no_generator_when_not_searchable(self):
        """測試非可搜尋模式不建立生成器"""
        mock_ocr = Mock()
        processor = PDFProcessor(ocr_func=mock_ocr)

        output, generator = processor._setup_pdf_generator(
            "test.pdf", None, searchable=False
        )

        assert generator is None

    @patch("paddleocr_toolkit.processors.pdf_processor.PDFGenerator")
    def test_setup_generator_auto_path(self, mock_generator_class):
        """測試自動生成輸出路徑"""
        mock_ocr = Mock()
        processor = PDFProcessor(ocr_func=mock_ocr)

        output, generator = processor._setup_pdf_generator(
            "test.pdf", None, searchable=True
        )

        assert "test_searchable.pdf" in output
        mock_generator_class.assert_called_once()

    @patch("paddleocr_toolkit.processors.pdf_processor.PDFGenerator")
    def test_setup_generator_custom_path(self, mock_generator_class):
        """測試自定義輸出路徑"""
        mock_ocr = Mock()
        processor = PDFProcessor(ocr_func=mock_ocr)

        output, generator = processor._setup_pdf_generator(
            "test.pdf", "custom_output.pdf", searchable=True
        )

        assert output == "custom_output.pdf"
        mock_generator_class.assert_called_once_with(
            output_path="custom_output.pdf", debug_mode=False
        )


class TestProcessSinglePage:
    """測試單頁處理"""

    @patch("paddleocr_toolkit.processors.pdf_processor.pixmap_to_numpy")
    @patch("paddleocr_toolkit.processors.pdf_processor.fitz")
    def test_process_single_page_basic(self, mock_fitz, mock_pixmap_to_numpy):
        """測試基本單頁處理"""
        # 設定mock
        mock_page = Mock()
        mock_pixmap = Mock()
        mock_page.get_pixmap.return_value = mock_pixmap

        mock_img_array = Mock()
        mock_pixmap_to_numpy.return_value = mock_img_array

        # OCR返回結果
        mock_ocr_result = [
            OCRResult("Test", 0.95, [[0, 0], [100, 0], [100, 50], [0, 50]])
        ]

        mock_ocr = Mock(return_value=mock_ocr_result)
        processor = PDFProcessor(ocr_func=mock_ocr)

        # 執行
        results = processor._process_single_page(mock_page, 0, 1, 200, None, True)

        # 驗證
        assert len(results) == 1
        assert results[0].text == "Test"
        mock_ocr.assert_called_once_with(mock_img_array)

    @patch("paddleocr_toolkit.processors.pdf_processor.pixmap_to_numpy")
    def test_process_single_page_with_parser(self, mock_pixmap_to_numpy):
        """測試使用解析器的單頁處理"""
        mock_page = Mock()
        mock_pixmap = Mock()
        mock_page.get_pixmap.return_value = mock_pixmap

        mock_img_array = Mock()
        mock_pixmap_to_numpy.return_value = mock_img_array

        # 解析器返回解析後的結果
        parsed_results = [
            OCRResult("Parsed", 0.90, [[0, 0], [100, 0], [100, 50], [0, 50]])
        ]

        mock_parser = Mock(return_value=parsed_results)
        mock_ocr = Mock(return_value={"raw": "data"})

        processor = PDFProcessor(ocr_func=mock_ocr, result_parser=mock_parser)

        results = processor._process_single_page(mock_page, 0, 1, 200, None, True)

        assert results == parsed_results
        mock_parser.assert_called_once()

    @patch("paddleocr_toolkit.processors.pdf_processor.pixmap_to_numpy")
    def test_process_single_page_scale_coordinates(self, mock_pixmap_to_numpy):
        """測試坐標縮放"""
        mock_page = Mock()
        mock_pixmap = Mock()
        mock_page.get_pixmap.return_value = mock_pixmap

        mock_pixmap_to_numpy.return_value = Mock()

        # 原始坐標（DPI空間）
        mock_ocr_result = [
            OCRResult("Test", 0.95, [[0, 0], [200, 0], [200, 100], [0, 100]])
        ]

        mock_ocr = Mock(return_value=mock_ocr_result)
        processor = PDFProcessor(ocr_func=mock_ocr)

        results = processor._process_single_page(mock_page, 0, 1, 200, None, True)

        # 驗證縮放（200 DPI → 72 DPI, scale = 72/200 = 0.36）
        scale = 72.0 / 200.0
        assert results[0].bbox[0][0] == 0 * scale
        assert results[0].bbox[1][0] == 200 * scale


class TestProcessPDF:
    """測試完整PDF處理"""

    @patch("paddleocr_toolkit.processors.pdf_processor.fitz")
    def test_process_pdf_error_handling(self, mock_fitz):
        """測試PDF處理錯誤處理"""
        mock_fitz.open.side_effect = Exception("Cannot open PDF")

        mock_ocr = Mock()
        processor = PDFProcessor(ocr_func=mock_ocr)

        results, output = processor.process_pdf("nonexistent.pdf")

        assert results == []
        assert output is None

    @patch("paddleocr_toolkit.processors.pdf_processor.fitz")
    @patch.object(PDFProcessor, "_setup_pdf_generator")
    @patch.object(PDFProcessor, "_process_single_page")
    def test_process_pdf_basic(self, mock_process_page, mock_setup, mock_fitz):
        """測試基本PDF處理"""
        # 設定mock PDF
        mock_doc = MagicMock()
        mock_doc.__len__ = Mock(return_value=2)
        mock_doc.__getitem__.side_effect = [Mock(), Mock()]
        mock_doc.close = Mock()
        mock_fitz.open.return_value = mock_doc

        # 設定處理結果
        mock_setup.return_value = (None, None)
        mock_process_page.side_effect = [
            [OCRResult("Page1", 0.95, [[0, 0], [100, 0], [100, 50], [0, 50]])],
            [OCRResult("Page2", 0.90, [[0, 0], [100, 0], [100, 50], [0, 50]])],
        ]

        mock_ocr = Mock()
        processor = PDFProcessor(ocr_func=mock_ocr)

        results, output = processor.process_pdf("test.pdf", show_progress=False)

        assert len(results) == 2
        assert len(results[0]) == 1
        assert results[0][0].text == "Page1"

    @patch("paddleocr_toolkit.processors.pdf_processor.fitz")
    @patch.object(PDFProcessor, "_setup_pdf_generator")
    @patch.object(PDFProcessor, "_process_single_page")
    def test_process_pdf_with_progress_callback(
        self, mock_process_page, mock_setup, mock_fitz
    ):
        """測試進度回撥"""
        mock_doc = MagicMock()
        mock_doc.__len__ = Mock(return_value=3)
        mock_doc.__getitem__.side_effect = [Mock(), Mock(), Mock()]
        mock_doc.close = Mock()
        mock_fitz.open.return_value = mock_doc

        mock_setup.return_value = (None, None)
        mock_process_page.return_value = []

        callback = Mock()
        mock_ocr = Mock()
        processor = PDFProcessor(ocr_func=mock_ocr)

        processor.process_pdf(
            "test.pdf", progress_callback=callback, show_progress=False
        )

        # 驗證回撥被呼叫3次
        assert callback.call_count == 3
        callback.assert_has_calls([call(1, 3), call(2, 3), call(3, 3)])

    @patch("paddleocr_toolkit.processors.pdf_processor.fitz")
    @patch.object(PDFProcessor, "_setup_pdf_generator")
    @patch.object(PDFProcessor, "_process_single_page")
    def test_process_pdf_page_error_handling(
        self, mock_process_page, mock_setup, mock_fitz
    ):
        """測試頁面錯誤處理"""
        mock_doc = MagicMock()
        mock_doc.__len__ = Mock(return_value=3)
        mock_doc.__getitem__.side_effect = [Mock(), Mock(), Mock()]
        mock_doc.close = Mock()
        mock_fitz.open.return_value = mock_doc

        mock_setup.return_value = (None, None)

        # 第2頁處理失敗
        mock_process_page.side_effect = [
            [OCRResult("Page1", 0.95, [[0, 0], [100, 0], [100, 50], [0, 50]])],
            Exception("Page processing error"),
            [OCRResult("Page3", 0.90, [[0, 0], [100, 0], [100, 50], [0, 50]])],
        ]

        mock_ocr = Mock()
        processor = PDFProcessor(ocr_func=mock_ocr)

        results, output = processor.process_pdf("test.pdf", show_progress=False)

        # 驗證錯誤頁面返回空列表
        assert len(results) == 3
        assert len(results[0]) == 1  # Page 1 成功
        assert len(results[1]) == 0  # Page 2 失敗
        assert len(results[2]) == 1  # Page 3 成功
