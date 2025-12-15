# -*- coding: utf-8 -*-
"""
GPU 優化器測試
測試 paddleocr_toolkit/core/gpu_optimizer.py
"""

from unittest.mock import MagicMock, patch

import pytest


class TestGPUMemoryPool:
    """測試 GPU 記憶體池"""

    def test_import_gpu_memory_pool(self):
        """測試匯入 GPU 記憶體池"""
        from paddleocr_toolkit.core.gpu_optimizer import GPUMemoryPool

        assert GPUMemoryPool is not None

    def test_memory_pool_init(self):
        """測試記憶體池初始化"""
        from paddleocr_toolkit.core.gpu_optimizer import GPUMemoryPool

        pool = GPUMemoryPool()
        assert pool.allocated_memory == []
        assert pool.peak_usage == 0

    def test_memory_pool_allocate(self):
        """測試記憶體分配"""
        from paddleocr_toolkit.core.gpu_optimizer import GPUMemoryPool

        pool = GPUMemoryPool()
        memory = pool.allocate(100)
        assert memory is not None
        assert len(pool.allocated_memory) == 1

    def test_memory_pool_clear(self):
        """測試記憶體清理"""
        from paddleocr_toolkit.core.gpu_optimizer import GPUMemoryPool

        pool = GPUMemoryPool()
        pool.allocate(100)
        pool.clear()
        assert pool.allocated_memory == []

    def test_memory_pool_context_manager(self):
        """測試上下文管理器"""
        from paddleocr_toolkit.core.gpu_optimizer import GPUMemoryPool

        with GPUMemoryPool() as pool:
            pool.allocate(100)
            assert len(pool.allocated_memory) == 1
        # 退出後應該已清理
        assert pool.allocated_memory == []

    def test_memory_pool_peak_usage(self):
        """測試峰值使用量"""
        from paddleocr_toolkit.core.gpu_optimizer import GPUMemoryPool

        pool = GPUMemoryPool()
        pool.allocate(1000)
        usage_mb = pool.get_peak_usage_mb()
        assert usage_mb > 0


class TestGPUBatchProcessor:
    """測試 GPU 批次處理器"""

    def test_import_gpu_batch_processor(self):
        """測試匯入 GPU 批次處理器"""
        from paddleocr_toolkit.core.gpu_optimizer import GPUBatchProcessor

        assert GPUBatchProcessor is not None

    def test_batch_processor_init(self):
        """測試批次處理器初始化"""
        from paddleocr_toolkit.core.gpu_optimizer import GPUBatchProcessor

        processor = GPUBatchProcessor()
        assert processor.batch_size == 16

    def test_batch_processor_custom_batch_size(self):
        """測試自定義批次大小"""
        from paddleocr_toolkit.core.gpu_optimizer import GPUBatchProcessor

        processor = GPUBatchProcessor(batch_size=8)
        assert processor.batch_size == 8

    def test_batch_processor_memory_pool_enabled(self):
        """測試記憶體池啟用"""
        from paddleocr_toolkit.core.gpu_optimizer import GPUBatchProcessor

        processor = GPUBatchProcessor(enable_memory_pool=True)
        assert processor.memory_pool is not None

    def test_batch_processor_memory_pool_disabled(self):
        """測試記憶體池停用"""
        from paddleocr_toolkit.core.gpu_optimizer import GPUBatchProcessor

        processor = GPUBatchProcessor(enable_memory_pool=False)
        assert processor.memory_pool is None

    def test_batch_processor_create_batches(self):
        """測試創建批次"""
        from paddleocr_toolkit.core.gpu_optimizer import GPUBatchProcessor

        processor = GPUBatchProcessor(batch_size=3)
        images = [1, 2, 3, 4, 5, 6, 7]
        batches = processor._create_batches(images, 3)
        assert len(batches) == 3
        assert batches[0] == [1, 2, 3]
        assert batches[1] == [4, 5, 6]
        assert batches[2] == [7]

    def test_batch_processor_preprocess_batch(self):
        """測試預處理批次"""
        from paddleocr_toolkit.core.gpu_optimizer import GPUBatchProcessor

        processor = GPUBatchProcessor()
        batch = [1, 2, 3]
        result = processor._preprocess_batch(batch)
        assert result is not None

    def test_batch_processor_get_stats(self):
        """測試獲取統計資訊"""
        from paddleocr_toolkit.core.gpu_optimizer import GPUBatchProcessor

        processor = GPUBatchProcessor()
        stats = processor.get_performance_stats()
        assert "total_images" in stats
        assert "total_batches" in stats

    def test_batch_processor_reset_stats(self):
        """測試重置統計"""
        from paddleocr_toolkit.core.gpu_optimizer import GPUBatchProcessor

        processor = GPUBatchProcessor()
        processor.stats["total_images"] = 100
        processor.reset_stats()
        assert processor.stats["total_images"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
