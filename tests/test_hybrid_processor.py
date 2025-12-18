# -*- coding: utf-8 -*-
"""
測試 HybridPDFProcessor
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from paddleocr_toolkit.core import OCRMode, OCRResult
from paddleocr_toolkit.core.ocr_engine import OCREngineManager
from paddleocr_toolkit.core.result_parser import OCRResultParser
from paddleocr_toolkit.processors.hybrid_processor import HybridPDFProcessor


class TestHybridPDFProcessorInitialization:
    """測試 HybridPDFProcessor 初始化"""

    def test_init_with_hybrid_engine(self):
        """測試使用 hybrid 引擎初始化"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.HYBRID

        processor = HybridPDFProcessor(mock_engine)

        assert processor.engine_manager == mock_engine
        assert processor.debug_mode is False
        assert processor.compress_images is True
        assert processor.jpeg_quality == 85

    def test_init_with_non_hybrid_engine_raises_error(self):
        """測試使用非 hybrid 引擎初始化時拋出錯誤"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.BASIC

        with pytest.raises(ValueError, match="需要 hybrid 模式引擎"):
            HybridPDFProcessor(mock_engine)

    def test_init_with_custom_settings(self):
        """測試使用自訂設定初始化"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.HYBRID

        processor = HybridPDFProcessor(
            mock_engine, debug_mode=True, compress_images=False, jpeg_quality=95
        )

        assert processor.debug_mode is True
        assert processor.compress_images is False
        assert processor.jpeg_quality == 95


class TestHybridPDFProcessorProcessPDF:
    """測試 process_pdf 方法"""

    @pytest.fixture
    def mock_engine(self):
        """建立 mock 引擎"""
        engine = Mock(spec=OCREngineManager)
        engine.get_mode.return_value = OCRMode.HYBRID
        return engine

    @pytest.fixture
    def processor(self, mock_engine):
        """建立 processor 實例"""
        return HybridPDFProcessor(mock_engine)

    @patch("paddleocr_toolkit.processors.hybrid_processor.fitz")
    @patch("paddleocr_toolkit.processors.hybrid_processor.detect_pdf_quality")
    def test_process_pdf_basic(self, mock_detect, mock_fitz, processor):
        """測試基本 PDF 處理"""
        # 設定 mock
        mock_pdf = MagicMock()
        mock_pdf.__len__.return_value = 1
        mock_fitz.open.return_value = mock_pdf

        mock_detect.return_value = {
            "is_scanned": False,
            "is_blurry": False,
            "reason": "清晰的數位PDF",
            "recommended_dpi": 150,
        }

        # 建立臨時 PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf_path = tmp.name

        try:
            with patch.object(processor, "_process_pdf_internal") as mock_internal:
                mock_internal.return_value = {
                    "input": pdf_path,
                    "mode": "hybrid",
                    "pages_processed": 1,
                    "searchable_pdf": "output.pdf",
                    "error": None,
                }

                result = processor.process_pdf(pdf_path)

                assert result["mode"] == "hybrid"
                assert result["pages_processed"] == 1
                assert mock_internal.called
        finally:
            Path(pdf_path).unlink(missing_ok=True)

    @patch("paddleocr_toolkit.processors.hybrid_processor.detect_pdf_quality")
    def test_process_pdf_with_dpi_adjustment(self, mock_detect, processor):
        """測試根據 PDF 品質調整 DPI"""
        mock_detect.return_value = {
            "is_scanned": True,
            "is_blurry": True,
            "reason": "掃描件且模糊",
            "recommended_dpi": 300,
        }

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf_path = tmp.name

        try:
            with patch.object(processor, "_process_pdf_internal") as mock_internal:
                mock_internal.return_value = {"mode": "hybrid"}

                processor.process_pdf(pdf_path, dpi=150)

                # 驗證 DPI 被調整為 300
                call_args = mock_internal.call_args
                # call_args 是 (args, kwargs) 的形式
                assert call_args.kwargs["dpi"] == 300 or call_args[1]["dpi"] == 300
        finally:
            Path(pdf_path).unlink(missing_ok=True)


class TestHybridPDFProcessorExtractAndMergeResults:
    """測試 _extract_and_merge_results 方法"""

    @pytest.fixture
    def processor(self):
        """建立 processor 實例"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.HYBRID
        return HybridPDFProcessor(mock_engine)

    def test_extract_with_markdown_attribute(self, processor):
        """測試提取包含 markdown 屬性的結果"""
        mock_result = Mock()
        mock_result.markdown = "# 標題\n\n內容"

        structure_output = [mock_result]

        with patch.object(processor.result_parser, "parse_structure_result") as mock_parse:
            mock_parse.return_value = [
                OCRResult(text="測試", confidence=0.9, bbox=[[0, 0], [100, 0], [100, 30], [0, 30]])
            ]

            ocr_results, markdown = processor._extract_and_merge_results(structure_output, 0)

            assert len(ocr_results) == 1
            assert "第 1 頁" in markdown
            assert "標題" in markdown

    def test_extract_without_markdown(self, processor):
        """測試提取沒有 markdown 的結果"""
        mock_result = Mock()
        # 沒有 markdown 屬性
        del mock_result.markdown

        structure_output = [mock_result]

        with patch.object(processor.result_parser, "parse_structure_result") as mock_parse:
            mock_parse.return_value = [
                OCRResult(text="測試文字", confidence=0.9, bbox=[[0, 0], [100, 0], [100, 30], [0, 30]])
            ]

            ocr_results, markdown = processor._extract_and_merge_results(structure_output, 0)

            assert len(ocr_results) == 1
            assert "第 1 頁" in markdown
            assert "測試文字" in markdown


class TestHybridPDFProcessorGenerateDualPDFs:
    """測試 _generate_dual_pdfs 方法"""

    @pytest.fixture
    def processor(self):
        """建立 processor 實例"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.HYBRID
        return HybridPDFProcessor(mock_engine)

    @patch("paddleocr_toolkit.processors.hybrid_processor.HAS_TRANSLATOR", False)
    def test_generate_without_inpainter(self, processor):
        """測試沒有 inpainter 時生成雙 PDF"""
        mock_pixmap = Mock()
        img_array = np.zeros((100, 100, 3), dtype=np.uint8)
        ocr_results = [
            OCRResult(text="測試", confidence=0.9, bbox=[[10, 10], [50, 10], [50, 30], [10, 30]])
        ]

        pdf_gen = Mock()
        erased_gen = Mock()

        processor._generate_dual_pdfs(
            mock_pixmap, img_array, ocr_results, pdf_gen, erased_gen, None
        )

        pdf_gen.add_page_from_pixmap.assert_called_once_with(mock_pixmap, ocr_results)
        erased_gen.add_page_from_pixmap.assert_called_once_with(mock_pixmap, ocr_results)


class TestHybridPDFProcessorSaveOutputs:
    """測試 _save_outputs 方法"""

    @pytest.fixture
    def processor(self):
        """建立 processor 實例"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.HYBRID
        return HybridPDFProcessor(mock_engine)

    def test_save_markdown_output(self, processor):
        """測試儲存 Markdown 輸出"""
        all_markdown = ["## 第 1 頁\n\n內容 1", "## 第 2 頁\n\n內容 2"]
        all_ocr_results = []
        result_summary = {}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as tmp:
            markdown_output = tmp.name

        try:
            processor._save_outputs(
                all_markdown,
                all_ocr_results,
                markdown_output,
                None,
                None,
                "test.pdf",
                result_summary,
            )

            assert result_summary["markdown_file"] == markdown_output
            assert Path(markdown_output).exists()

            # 驗證內容
            with open(markdown_output, "r", encoding="utf-8") as f:
                content = f.read()
                assert "第 1 頁" in content
                assert "第 2 頁" in content
        finally:
            Path(markdown_output).unlink(missing_ok=True)

    def test_save_without_markdown_output(self, processor):
        """測試不儲存 Markdown 時"""
        result_summary = {}

        processor._save_outputs([], [], None, None, None, "test.pdf", result_summary)

        assert "markdown_file" not in result_summary
