#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能模組測試
測試GPU優化器、快取系統和並行處理器
"""

import tempfile
from pathlib import Path

import pytest


def test_gpu_optimizer_import():
    """測試GPU優化器匯入"""
    from paddleocr_toolkit.core.gpu_optimizer import GPUBatchProcessor

    processor = GPUBatchProcessor(batch_size=8)
    assert processor.batch_size == 8
    assert processor.stats["total_images"] == 0


def test_model_cache_singleton():
    """測試模型快取單例模式"""
    from paddleocr_toolkit.core.model_cache import ModelCache

    cache1 = ModelCache()
    cache2 = ModelCache()

    # 應該是同一個實例
    assert cache1 is cache2


def test_result_cache():
    """測試結果快取"""
    from paddleocr_toolkit.core.model_cache import ResultCache

    with tempfile.TemporaryDirectory() as tmpdir:
        cache = ResultCache(cache_dir=Path(tmpdir))

        # 測試統計
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0


def test_parallel_processor_init():
    """測試並行處理器初始化"""
    from paddleocr_toolkit.processors.parallel_pdf_processor import \
        ParallelPDFProcessor

    processor = ParallelPDFProcessor(workers=4)
    assert processor.workers == 4


def test_gpu_batch_creation():
    """測試批次建立"""
    from paddleocr_toolkit.core.gpu_optimizer import GPUBatchProcessor

    processor = GPUBatchProcessor(batch_size=4)
    images = list(range(10))

    batches = processor._create_batches(images, 4)
    assert len(batches) == 3  # 10個圖片，批次大小4，應該有3批
    assert len(batches[0]) == 4
    assert len(batches[1]) == 4
    assert len(batches[2]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
