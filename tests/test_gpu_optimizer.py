# -*- coding: utf-8 -*-
"""
GPU 最佳化器測試
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
        """測試建立批次"""
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

    def test_batch_predict_flow(self):
        """測試完整批次預測流程"""
        from paddleocr_toolkit.core.gpu_optimizer import GPUBatchProcessor

        # 準備
        processor = GPUBatchProcessor(batch_size=2)
        images = [1, 2, 3, 4, 5]  # 5張圖，應該分成3批 (2, 2, 1)

        mock_engine = MagicMock()

        # 模擬 ocr 返回結果，每次調用返回對應數量的結果
        def side_effect(tensor, batch=True):
            return ["res"] * len(tensor)

        mock_engine.ocr.side_effect = side_effect

        # 執行
        results = processor.batch_predict(images, mock_engine)

        # 驗證
        assert len(results) == 5
        assert processor.stats["total_images"] == 5
        assert processor.stats["total_batches"] == 3
        assert processor.stats["total_time"] > 0
        assert mock_engine.ocr.call_count == 3

    def test_gpu_predict_with_pool(self):
        """測試帶記憶體池的預測"""
        from paddleocr_toolkit.core.gpu_optimizer import GPUBatchProcessor

        processor = GPUBatchProcessor(enable_memory_pool=True)
        mock_pool = MagicMock()
        processor.memory_pool = mock_pool

        mock_engine = MagicMock()
        batch_tensor = MagicMock()

        processor._gpu_predict_batch(batch_tensor, mock_engine)

        # 驗證使用了 memory pool 上下文
        mock_pool.__enter__.assert_called()
        mock_pool.__exit__.assert_called()
        mock_engine.ocr.assert_called_with(batch_tensor, batch=True)

    def test_performance_stats_calculation(self):
        """測試性能統計計算"""
        from paddleocr_toolkit.core.gpu_optimizer import GPUBatchProcessor

        processor = GPUBatchProcessor()
        # 手動注入統計數據
        processor.stats = {
            "total_images": 100,
            "total_batches": 10,
            "total_time": 10.0,
            "gpu_time": 5.0,
            "preprocessing_time": 2.0,
        }

        stats = processor.get_performance_stats()

        assert stats["avg_time_per_image"] == 0.1  # 10.0 / 100
        assert stats["avg_time_per_batch"] == 1.0  # 10.0 / 10
        assert stats["preprocessing_ratio"] == 0.2  # 2.0 / 10.0
        assert stats["gpu_ratio"] == 0.5  # 5.0 / 10.0

    def test_print_report(self):
        """測試報告打印"""
        from paddleocr_toolkit.core.gpu_optimizer import GPUBatchProcessor

        processor = GPUBatchProcessor()
        processor.stats["total_images"] = 10

        with patch("paddleocr_toolkit.core.gpu_optimizer.logger") as mock_logger:
            processor.print_performance_report()
            assert mock_logger.info.called

    def test_empty_stats_report(self):
        """測試空統計數據的報告"""
        from paddleocr_toolkit.core.gpu_optimizer import GPUBatchProcessor

        processor = GPUBatchProcessor()
        # 默認全0
        stats = processor.get_performance_stats()
        assert stats["total_images"] == 0
        # 應該直接返回 stats 而不是計算後的字典
        assert "avg_time_per_image" not in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
