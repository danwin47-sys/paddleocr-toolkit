# -*- coding: utf-8 -*-
"""
Parallel PDF Processor Tests
"""
import os
import sys
import pytest
import numpy as np
from unittest.mock import MagicMock, Mock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paddleocr_toolkit.processors.parallel_pdf_processor import ParallelPDFProcessor


class TestParallelPDFProcessor:
    def test_init_default_workers(self):
        """Test initialization with default workers from cpu_count"""
        with patch(
            "paddleocr_toolkit.processors.parallel_pdf_processor.cpu_count",
            return_value=8,
        ):
            with patch.dict(os.environ, {}, clear=True):
                processor = ParallelPDFProcessor()
                assert processor.workers == 7  # 8 - 1

    def test_init_env_workers(self):
        """Test initialization with OCR_WORKERS env var"""
        with patch.dict(os.environ, {"OCR_WORKERS": "4"}):
            processor = ParallelPDFProcessor()
            assert processor.workers == 4

    def test_init_explicit_workers(self):
        """Test initialization with explicit workers argument"""
        processor = ParallelPDFProcessor(workers=2)
        assert processor.workers == 2

    @patch("paddleocr_toolkit.core.ocr_engine.OCREngineManager")
    @patch("cv2.imdecode")
    def test_process_single_page_success(self, mock_imdecode, mock_engine_cls):
        """Test static _process_single_page success path"""
        mock_engine = MagicMock()
        mock_engine.predict.return_value = ["Standard Result"]
        mock_engine_cls.return_value = mock_engine

        mock_imdecode.return_value = MagicMock()  # Mock image array

        args = (0, b"fake_bytes", {"mode": "basic"})
        page_num, result = ParallelPDFProcessor._process_single_page(args)

        assert page_num == 0
        assert result == "Standard Result"
        mock_engine.init_engine.assert_called_once()

    def test_process_single_page_error(self):
        """Test static _process_single_page error handling"""
        # Triggers exception inside the method
        args = (1, None, None)  # None ocr_config will fail inside engine init or unpack

        page_num, result = ParallelPDFProcessor._process_single_page(args)

        assert page_num == 1
        assert "Error on page 1" in str(result)

    @patch("fitz.open")
    def test_process_pdf_parallel_serial_fallback(self, mock_fitz_open):
        """Test serial processing when page count is small"""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_page = MagicMock()
        mock_page.get_pixmap.return_value.tobytes.return_value = b"img"
        mock_doc.load_page.return_value = mock_page
        mock_fitz_open.return_value = mock_doc

        processor = ParallelPDFProcessor(workers=4)

        # Mock _process_single_page to avoid actual engine loading
        with patch.object(ParallelPDFProcessor, "_process_single_page") as mock_single:
            mock_single.return_value = (0, "Result 0")

            results = processor.process_pdf_parallel("dummy.pdf")

            assert results == ["Result 0"]
            assert mock_single.call_count == 1
            # Should NOT use Pool because total_pages (1) <= 2

    @patch("fitz.open")
    @patch("paddleocr_toolkit.processors.parallel_pdf_processor.Pool")
    def test_process_pdf_parallel_pool_usage(self, mock_pool_cls, mock_fitz_open):
        """Test parallel processing using Pool when page count is large"""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 5  # > 2
        mock_page = MagicMock()
        mock_page.get_pixmap.return_value.tobytes.return_value = b"img"
        mock_doc.load_page.return_value = mock_page
        mock_fitz_open.return_value = mock_doc

        # Setup Pool Mock
        mock_pool = MagicMock()
        mock_pool.__enter__.return_value = mock_pool
        mock_pool.map.return_value = [
            (0, "R0"),
            (1, "R1"),
            (2, "R2"),
            (3, "R3"),
            (4, "R4"),
        ]
        mock_pool_cls.return_value = mock_pool

        processor = ParallelPDFProcessor(workers=4)

        results = processor.process_pdf_parallel("dummy.pdf")

        assert len(results) == 5
        assert results[0] == "R0"
        mock_pool.map.assert_called_once()

    @patch("fitz.open")
    def test_benchmark_run(self, mock_fitz_open):
        """Test benchmark method execution"""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2
        mock_fitz_open.return_value = mock_doc

        processor = ParallelPDFProcessor(workers=1)

        with patch.object(processor, "_process_single_page", return_value=(0, "ok")):
            with patch.object(processor, "process_pdf_parallel", return_value=["ok"]):
                processor.benchmark("dummy.pdf")
                # Just ensure it doesn't crash and calls internal methods


# Added from Ultra Coverage
from paddleocr_toolkit.processors.parallel_pdf_processor import ParallelPDFProcessor
from unittest.mock import MagicMock, patch
import pytest
import os
import numpy as np


class TestParallelProcessorUltra:
    def test_parallel_processor_branches(self):
        with patch.dict(os.environ, {"OCR_WORKERS": "invalid"}):
            proc = ParallelPDFProcessor()
            assert proc.workers >= 1
        with patch(
            "paddleocr_toolkit.processors.parallel_pdf_processor.HAS_PYMUPDF", False
        ):
            with pytest.raises(ImportError):
                proc.process_pdf_parallel("test.pdf")
        with patch(
            "paddleocr_toolkit.processors.parallel_pdf_processor.Pool",
            side_effect=Exception("Pool error"),
        ):
            proc = ParallelPDFProcessor(workers=4)
            mock_doc = MagicMock()
            mock_doc.__len__.return_value = 4
            with patch("fitz.open", return_value=mock_doc), patch.object(
                proc, "_process_single_page", return_value=(0, [])
            ):
                res = proc.process_pdf_parallel("test.pdf")
                assert len(res) == 4

    def test_process_single_page_not_list(self):
        proc = ParallelPDFProcessor()
        mock_engine = MagicMock()
        mock_engine.predict.return_value = "string_result"
        with patch(
            "paddleocr_toolkit.core.ocr_engine.OCREngineManager"
        ) as mock_mgr_cls, patch("cv2.imdecode", return_value=np.zeros((10, 10, 3))):
            mock_mgr_cls.return_value = mock_engine
            res = proc._process_single_page((0, b"data", {}))
            assert res[1] == "string_result"

    def test_parallel_block_simulation(self):
        import runpy

        with patch(
            "paddleocr_toolkit.processors.parallel_pdf_processor.ParallelPDFProcessor.benchmark"
        ):
            with patch("os.path.exists", return_value=True):
                with patch("fitz.open") as mock_fitz:
                    mock_doc = MagicMock()
                    mock_doc.__len__.return_value = 1
                    mock_fitz.return_value = mock_doc
                    runpy.run_module(
                        "paddleocr_toolkit.processors.parallel_pdf_processor",
                        run_name="__main__",
                    )
