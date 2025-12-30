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
        """測試自定義工作程式數"""
        from paddleocr_toolkit.processors.parallel_pdf_processor import (
            ParallelPDFProcessor,
        )

        processor = ParallelPDFProcessor(workers=2)
        assert processor.workers == 2

    def test_processor_has_process_pdf_parallel(self):
        """測試 process_pdf_parallel 方法存在"""
        from paddleocr_toolkit.processors.parallel_pdf_processor import (
            ParallelPDFProcessor,
        )

        processor = ParallelPDFProcessor()
        assert hasattr(processor, "process_pdf_parallel")
        assert callable(processor.process_pdf_parallel)

    def test_processor_has_process_single_page(self):
        """測試 _process_single_page 靜態方法存在"""
        from paddleocr_toolkit.processors.parallel_pdf_processor import (
            ParallelPDFProcessor,
        )

        assert hasattr(ParallelPDFProcessor, "_process_single_page")
        assert callable(ParallelPDFProcessor._process_single_page)

    def test_processor_workers_default(self):
        """測試工作進程數預設值"""
        from multiprocessing import cpu_count

        from paddleocr_toolkit.processors.parallel_pdf_processor import (
            ParallelPDFProcessor,
        )

        processor = ParallelPDFProcessor()
        expected_workers = max(1, cpu_count() - 1)
        assert processor.workers == expected_workers


class TestParallelProcessorBenchmark:
    """測試並行處理器基準測試"""

    def test_benchmark_exists(self):
        """測試基準測試方法 benchmark 存在"""
        from paddleocr_toolkit.processors.parallel_pdf_processor import (
            ParallelPDFProcessor,
        )

        processor = ParallelPDFProcessor()
        assert hasattr(processor, "benchmark")
        assert callable(processor.benchmark)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
