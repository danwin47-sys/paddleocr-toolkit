# -*- coding: utf-8 -*-
"""
Batch Processor 單元測試
"""

import pytest
import sys
import os
import numpy as np

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paddleocr_toolkit.processors.batch_processor import (
    get_optimal_workers,
    batch_process_images,
    BatchProcessor,
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
        
        # 通常不會超過 CPU 數量
        assert result <= os.cpu_count() or os.cpu_count() is None


class TestBatchProcessImages:
    """測試 batch_process_images"""
    
    def test_basic_processing(self):
        """測試基本批次處理"""
        images = [np.zeros((10, 10, 3), dtype=np.uint8) for _ in range(5)]
        
        def process_func(img):
            return img.sum()
        
        results = batch_process_images(
            images=images,
            process_func=process_func,
            batch_size=2
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
        
        results = batch_process_images(
            images=images,
            process_func=process_func
        )
        
        assert results == [1, 2, 3]


class TestBatchProcessor:
    """測試 BatchProcessor 類別"""
    
    def test_initialization(self):
        """測試初始化"""
        processor = BatchProcessor(max_workers=4, batch_size=8)
        
        assert processor.max_workers == 4
        assert processor.batch_size == 8
    
    def test_process_images(self):
        """測試處理圖片"""
        processor = BatchProcessor(max_workers=2, batch_size=4)
        
        images = [np.zeros((10, 10), dtype=np.uint8) for _ in range(6)]
        
        def process_func(img):
            return img.shape
        
        results = processor.process_images(images, process_func)
        
        assert len(results) == 6
        assert all(r == (10, 10) for r in results)


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
