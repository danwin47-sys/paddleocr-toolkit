# -*- coding: utf-8 -*-
"""
Batch Processor 單元測試（整合版）
"""

import os
import sys
import tempfile
import time
import importlib
import builtins

import numpy as np
import pytest
from unittest.mock import MagicMock, patch

# 新增專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import fitz

    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

from paddleocr_toolkit.processors.batch_processor import (
    BatchProcessor,
    batch_process_images,
    get_optimal_workers,
    pdf_to_images_parallel,
)


class TestGetOptimalWorkers:
    """測試 get_optimal_workers"""

    def test_returns_positive(self):
        """測試返回正整數"""
        result = get_optimal_workers()

        assert isinstance(result, int)
        assert result > 0

    def test_max_limit(self):
        """測試最大限制"""
        result = get_optimal_workers()

        cpu_count = os.cpu_count() or 4
        assert result <= cpu_count

    def test_mocked_scenarios(self):
        """覆蓋更多 CPU 核心數場景"""
        # Test low CPU count
        with patch("os.cpu_count", return_value=1):
            assert get_optimal_workers() == 2  # max(2, 0) -> 2

        # Test medium CPU count
        with patch("os.cpu_count", return_value=8):
            assert get_optimal_workers() == 4  # 8 // 2 = 4

        # Test high CPU count (capped at 8)
        with patch("os.cpu_count", return_value=32):
            assert get_optimal_workers() == 8  # min(16, 8) -> 8

        # Test None CPU count
        with patch("os.cpu_count", return_value=None):
            assert get_optimal_workers() == 2  # 4 // 2 = 2


class TestBatchProcessImages:
    """測試 batch_process_images"""

    def test_basic_processing(self):
        """測試基本批次處理"""
        images = [np.zeros((10, 10, 3), dtype=np.uint8) for _ in range(5)]

        def process_func(img):
            return img.sum()

        results = batch_process_images(
            images=images, process_func=process_func, batch_size=2
        )

        assert len(results) == 5
        assert all(r == 0 for r in results)

    def test_with_different_images(self):
        """測試不同圖片"""
        images = []
        for i in range(3):
            img = np.ones((10, 10, 3), dtype=np.uint8) * (i + 1)
            images.append(img)

        def process_func(img):
            return img[0, 0, 0]

        results = batch_process_images(images=images, process_func=process_func)

        assert results == [1, 2, 3]

    def test_empty_list(self):
        """測試空列表"""
        results = batch_process_images(images=[], process_func=lambda x: x)

        assert results == []

    def test_single_image(self):
        """測試單張圖片"""
        image = np.ones((10, 10), dtype=np.uint8) * 42

        results = batch_process_images(images=[image], process_func=lambda x: x.max())

        assert len(results) == 1
        assert results[0] == 42

    def test_exception_handling(self):
        """覆蓋異常處理邏輯"""
        # 3 Mock images
        images = [np.zeros((10, 10)) for _ in range(3)]
        images[1] = np.zeros((1, 1))  # This one fails

        def processor(img):
            # Fail if shape is (1,1)
            if img.shape == (1, 1):
                raise ValueError("Fail")
            return "Success"

        mock_cb = MagicMock()

        res = batch_process_images(
            images, processor, max_workers=2, progress_callback=mock_cb
        )

        assert len(res) == 3
        assert res[0] == "Success"
        assert res[1] is None  # Failed
        assert res[2] == "Success"

        # Verify callback called to cover internal progress wrapper
        assert mock_cb.call_count > 0


class TestBatchProcessor:
    """測試 BatchProcessor 類別"""

    def test_initialization(self):
        """測試初始化"""
        processor = BatchProcessor(max_workers=4, batch_size=8)

        assert processor.max_workers == 4
        assert processor.batch_size == 8

    def test_default_initialization(self):
        """測試預設初始化"""
        processor = BatchProcessor()

        assert processor.max_workers > 0
        assert processor.batch_size > 0

    def test_process_images(self):
        """測試處理圖片"""
        processor = BatchProcessor(max_workers=2, batch_size=4)

        images = [np.zeros((10, 10), dtype=np.uint8) for _ in range(6)]

        def process_func(img):
            return img.shape

        results = processor.process_images(images, process_func)

        assert len(results) == 6
        assert all(r == (10, 10) for r in results)

    def test_process_with_args(self):
        """測試帶引數的處理"""
        processor = BatchProcessor(max_workers=2)

        images = [np.ones((5, 5), dtype=np.uint8) * i for i in range(3)]

        def process_func(img):
            return img.sum()

        results = processor.process_images(images, process_func)

        assert len(results) == 3

    def test_process_many_images(self):
        """測試處理大量圖片"""
        processor = BatchProcessor(max_workers=4, batch_size=10)

        images = [np.ones((5, 5), dtype=np.uint8) for _ in range(50)]

        def quick_process(img):
            return 1

        results = processor.process_images(images, quick_process)

        assert len(results) == 50
        assert sum(results) == 50

    def test_progress_callbacks_internal(self):
        """Cover lines 199-202 and 215-218 (internal progress wrappers)"""
        proc = BatchProcessor()
        mock_cb = MagicMock()
        proc.set_progress_callback(mock_cb)

        # 1. Trigger pdf_to_images internal progress wrapper
        with patch(
            "paddleocr_toolkit.processors.batch_processor.pdf_to_images_parallel"
        ) as mock_parallel:
            mock_parallel.return_value = []
            proc.pdf_to_images("dummy.pdf")

            args, kwargs = mock_parallel.call_args
            internal_progress = kwargs.get("progress_callback")

            internal_progress(1, 10)
            mock_cb.assert_called_with(1, 10, "PDF 轉圖片")

        # 2. Trigger process_images internal progress wrapper
        with patch(
            "paddleocr_toolkit.processors.batch_processor.batch_process_images"
        ) as mock_batch:
            mock_batch.return_value = []
            proc.process_images([], lambda x: x)

            args, kwargs = mock_batch.call_args
            internal_progress = kwargs.get("progress_callback")

            internal_progress(5, 5)
            mock_cb.assert_called_with(5, 5, "處理圖片")

    def test_report_progress_print(self):
        """Cover lines 188-192 (print progress)"""
        # show_progress=True, no callback
        proc = BatchProcessor(show_progress=True)

        with patch("builtins.print") as mock_print:
            proc._report_progress(50, 100, "Test")
            mock_print.assert_called()

            # 100% case
            proc._report_progress(100, 100, "Done")
            assert mock_print.call_count >= 2

    def test_streaming_enabled_paths(self):
        """Cover lines 256 and 289 (HAS_STREAMING = True paths)"""
        proc = BatchProcessor(batch_size=4)

        # Mock HAS_STREAMING = True
        with patch("paddleocr_toolkit.processors.batch_processor.HAS_STREAMING", True):
            with patch(
                "paddleocr_toolkit.processors.batch_processor.pdf_pages_generator",
                return_value=iter([(1, "img")]),
            ) as mock_pg_gen:
                list(proc.pdf_pages_stream("test.pdf"))
                mock_pg_gen.assert_called_once()

            with patch(
                "paddleocr_toolkit.processors.batch_processor.batch_pages_generator",
                return_value=iter([[(1, "img")]]),
            ) as mock_batch_gen:
                list(proc.pdf_batch_stream("test.pdf"))
                mock_batch_gen.assert_called_once_with("test.pdf", 150, 4, None)

    def test_streaming_disabled_paths(self):
        """Cover lines 251-254 and 284-287 (HAS_STREAMING = False)"""
        proc = BatchProcessor()
        import numpy as np

        # Mock HAS_STREAMING = False
        with patch("paddleocr_toolkit.processors.batch_processor.HAS_STREAMING", False):
            # We need to mock pdf_to_images so it returns something
            with patch.object(
                proc, "pdf_to_images", return_value=[(1, np.zeros((10, 10)))]
            ):
                # pdf_pages_stream fallback
                res = list(proc.pdf_pages_stream("test.pdf"))
                assert len(res) == 1
                assert res[0][0] == 1

                # pdf_batch_stream fallback
                res_batch = list(proc.pdf_batch_stream("test.pdf", batch_size=2))
                assert len(res_batch) == 1
                assert len(res_batch[0]) == 1


class TestPdfToImagesParallel:
    """測試 pdf_to_images_parallel"""

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_convert_pdf(self):
        """測試轉換 PDF"""
        # 建立測試 PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            doc = fitz.open()
            for i in range(3):
                page = doc.new_page(width=100, height=100)
                page.insert_text((10, 50), f"Page {i+1}")
            doc.save(temp_path)
            doc.close()

            results = pdf_to_images_parallel(temp_path, dpi=72)

            assert len(results) == 3
            assert all(isinstance(r, tuple) for r in results)
            assert all(len(r) == 2 for r in results)

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_convert_specific_pages(self):
        """測試轉換指定頁面"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            doc = fitz.open()
            for i in range(5):
                doc.new_page(width=100, height=100)
            doc.save(temp_path)
            doc.close()

            results = pdf_to_images_parallel(temp_path, pages=[0, 2, 4])

            assert len(results) == 3
            page_nums = [r[0] for r in results]
            assert 0 in page_nums
            assert 2 in page_nums
            assert 4 in page_nums

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_with_progress_callback(self):
        """測試進度回撥"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            doc = fitz.open()
            for i in range(3):
                doc.new_page(width=100, height=100)
            doc.save(temp_path)
            doc.close()

            progress_calls = []

            def on_progress(current, total):
                progress_calls.append((current, total))

            results = pdf_to_images_parallel(temp_path, progress_callback=on_progress)

            assert len(results) == 3
            assert len(progress_calls) == 3

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_pdf_to_images_parallel_exceptions(self):
        """Cover lines 102-104 (Exception inside thread loop)"""
        mock_cb = MagicMock()
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2

        # Page 1 works, Page 2 fails
        mock_page_ok = MagicMock()
        mock_pixmap = MagicMock()
        mock_pixmap.samples = b"\x00" * 300  # RGB 10x10
        mock_pixmap.height = 10
        mock_pixmap.width = 10
        mock_pixmap.n = 3
        mock_page_ok.get_pixmap.return_value = mock_pixmap

        mock_page_fail = MagicMock()
        mock_page_fail.get_pixmap.side_effect = Exception("Rendering failed")

        mock_doc.__getitem__.side_effect = [mock_page_ok, mock_page_fail]

        with patch("fitz.open", return_value=mock_doc), patch(
            "paddleocr_toolkit.processors.batch_processor.HAS_FITZ", True
        ), patch("paddleocr_toolkit.processors.batch_processor.HAS_NUMPY", True):
            res = pdf_to_images_parallel("test.pdf", progress_callback=mock_cb)

            assert len(res) == 1
            mock_cb.assert_called()

    def test_checks_fail(self):
        """Cover lines 60-62 (if not HAS_FITZ / HAS_NUMPY)"""
        with patch("paddleocr_toolkit.processors.batch_processor.HAS_FITZ", False):
            with pytest.raises(ImportError, match="PyMuPDF"):
                pdf_to_images_parallel("test.pdf")

        with patch(
            "paddleocr_toolkit.processors.batch_processor.HAS_FITZ", True
        ), patch("paddleocr_toolkit.processors.batch_processor.HAS_NUMPY", False):
            with pytest.raises(ImportError, match="NumPy"):
                pdf_to_images_parallel("test.pdf")

    def test_rgba_conversion(self):
        """Cover line 83 (pixmap.n == 4)"""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_page = MagicMock()
        mock_pixmap = MagicMock()
        mock_pixmap.samples = b"\x00" * 400  # 10x10 RGBA -> 400 bytes
        mock_pixmap.height = 10
        mock_pixmap.width = 10
        mock_pixmap.n = 4  # RGBA
        mock_page.get_pixmap.return_value = mock_pixmap
        mock_doc.__getitem__.return_value = mock_page

        with patch("fitz.open", return_value=mock_doc), patch(
            "paddleocr_toolkit.processors.batch_processor.HAS_FITZ", True
        ), patch("paddleocr_toolkit.processors.batch_processor.HAS_NUMPY", True):
            res = pdf_to_images_parallel("test.pdf")
            assert len(res) == 1
            assert res[0][1].shape == (10, 10, 3)


class TestBatchProcessorPerformance:
    """測試 BatchProcessor 效能"""

    def test_processing_completes(self):
        """測試處理完成"""
        processor = BatchProcessor(max_workers=2)

        images = [
            np.random.randint(0, 255, (20, 20), dtype=np.uint8) for _ in range(10)
        ]

        def slow_process(img):
            return img.mean()

        start = time.time()
        results = processor.process_images(images, slow_process)
        elapsed = time.time() - start

        assert len(results) == 10
        assert elapsed < 10


def test_import_time_fallbacks():
    """Cover Import time fallbacks"""
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name in ["numpy", "fitz", "paddleocr_toolkit.core.streaming_utils"]:
            raise ImportError(f"Mock fail {name}")
        return real_import(name, *args, **kwargs)

    # Remove from sys.modules temporarily
    for mod in [
        "paddleocr_toolkit.processors.batch_processor",
        "paddleocr_toolkit.core.streaming_utils",
    ]:
        if mod in sys.modules:
            del sys.modules[mod]

    with patch("builtins.__import__", side_effect=mock_import):
        import paddleocr_toolkit.processors.batch_processor as bp

        assert bp.HAS_NUMPY is False
        assert bp.HAS_FITZ is False
        assert bp.HAS_STREAMING is False
        assert hasattr(bp.np, "ndarray")

    # Restore normal module
    if "paddleocr_toolkit.processors.batch_processor" in sys.modules:
        del sys.modules["paddleocr_toolkit.processors.batch_processor"]
    importlib.import_module("paddleocr_toolkit.processors.batch_processor")
