# -*- coding: utf-8 -*-
"""
並行 PDF 處理器測試
測試 paddleocr_toolkit/processors/parallel_pdf_processor.py
"""

from unittest.mock import MagicMock, patch

import pytest


class TestParallelPDFProcessor:
    """測試並行 PDF 處理器"""

    def test_import_parallel_processor(self):
        """測試匯入並行處理器"""
        from paddleocr_toolkit.processors.parallel_pdf_processor import (
            ParallelPDFProcessor,
        )

        assert ParallelPDFProcessor is not None

    def test_processor_init(self):
        """測試處理器初始化"""
        from paddleocr_toolkit.processors.parallel_pdf_processor import (
            ParallelPDFProcessor,
        )

        processor = ParallelPDFProcessor()
        assert processor.workers >= 1

    def test_processor_custom_workers(self):
        """測試自定義工作進程數"""
        from paddleocr_toolkit.processors.parallel_pdf_processor import (
            ParallelPDFProcessor,
        )

        processor = ParallelPDFProcessor(workers=2)
        assert processor.workers == 2

    def test_processor_split_pdf_pages(self):
        """測試分割 PDF 頁面"""
        from paddleocr_toolkit.processors.parallel_pdf_processor import (
            ParallelPDFProcessor,
        )

        processor = ParallelPDFProcessor()
        pages = processor._split_pdf_pages("test.pdf")
        assert isinstance(pages, list)
        assert len(pages) > 0

    def test_processor_process_page(self):
        """測試處理單頁"""
        from paddleocr_toolkit.processors.parallel_pdf_processor import (
            ParallelPDFProcessor,
        )

        processor = ParallelPDFProcessor()
        result = processor._process_page((0, "page_0"))
        assert result is not None
        assert result[0] == 0

    def test_processor_process_serial(self):
        """測試串行處理"""
        from paddleocr_toolkit.processors.parallel_pdf_processor import (
            ParallelPDFProcessor,
        )

        processor = ParallelPDFProcessor()
        results = processor._process_serial("test.pdf")
        assert isinstance(results, list)


class TestParallelProcessorBenchmark:
    """測試並行處理器基準測試"""

    def test_benchmark_exists(self):
        """測試基準測試方法存在"""
        from paddleocr_toolkit.processors.parallel_pdf_processor import (
            ParallelPDFProcessor,
        )

        processor = ParallelPDFProcessor()
        assert hasattr(processor, "benchmark_parallel_vs_serial")
        assert callable(processor.benchmark_parallel_vs_serial)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
