# -*- coding: utf-8 -*-
"""
Batch Processor 擴展測試 - v1.1.0
補充測試以達到 90% 覆蓋率
"""

import os
import sys
import tempfile
import time
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

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


class TestBatchProcessorAdvanced:
    """進階批次處理器測試"""

    def test_error_handling_in_batch(self):
        """測試批次處理中的錯誤記錄"""
        processor = BatchProcessor(max_workers=2)

        images = [np.ones((5, 5), dtype=np.uint8) for _ in range(3)]

        error_count = [0]

        def error_on_second(img):
            error_count[0] += 1
            if error_count[0] == 2:
                raise ValueError("處理錯誤")
            return img.sum()

        # batch_process_images 會記錄錯誤但繼續處理
        results = processor.process_images(images, error_on_second)

        # 應該有一個 None 結果（失敗的）
        assert None in results
        assert len(results) == 3

    def test_process_with_timeout(self):
        """測試處理超時情況"""
        processor = BatchProcessor(max_workers=1, batch_size=2)

        images = [np.ones((5, 5), dtype=np.uint8) for _ in range(3)]

        def slow_process(img):
            time.sleep(0.1)
            return img.sum()

        start = time.time()
        results = processor.process_images(images, slow_process)
        elapsed = time.time() - start

        assert len(results) == 3
        assert elapsed >= 0.3  # 至少需要0.3秒

    def test_batch_size_effect(self):
        """測試批次大小影響"""
        images = [np.ones((10, 10), dtype=np.uint8) * i for i in range(20)]

        def count_process(img):
            return 1

        # 小批次
        processor_small = BatchProcessor(batch_size=5)
        results_small = processor_small.process_images(images, count_process)

        # 大批次
        processor_large = BatchProcessor(batch_size=20)
        results_large = processor_large.process_images(images, count_process)

        # 結果應該相同
        assert sum(results_small) == sum(results_large) == 20

    def test_worker_count_effect(self):
        """測試工作線程數影響"""
        images = [np.ones((5, 5), dtype=np.uint8) for _ in range(10)]

        def process_func(img):
            return img.shape[0]

        # 單線程
        processor_single = BatchProcessor(max_workers=1)
        results_single = processor_single.process_images(images, process_func)

        # 多線程
        processor_multi = BatchProcessor(max_workers=4)
        results_multi = processor_multi.process_images(images, process_func)

        # 結果應該相同
        assert results_single == results_multi


class TestPdfToImagesParallelAdvanced:
    """進階 PDF 轉圖片測試"""

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_different_dpi_settings(self):
        """測試不同 DPI 設置"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            doc = fitz.open()
            doc.new_page(width=100, height=100)
            doc.save(temp_path)
            doc.close()

            # 低 DPI
            results_low = pdf_to_images_parallel(temp_path, dpi=72)
            # 高 DPI
            results_high = pdf_to_images_parallel(temp_path, dpi=300)

            # 高 DPI 應該產生更大的圖片
            img_low = results_low[0][1]
            img_high = results_high[0][1]

            assert img_high.shape[0] > img_low.shape[0]
            assert img_high.shape[1] > img_low.shape[1]

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_max_workers_parameter(self):
        """測試最大工作線程參數"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            doc = fitz.open()
            for i in range(4):
                doc.new_page(width=100, height=100)
            doc.save(temp_path)
            doc.close()

            # 不同工作線程數
            results_1 = pdf_to_images_parallel(temp_path, max_workers=1)
            results_4 = pdf_to_images_parallel(temp_path, max_workers=4)

            # 結果數量應該相同
            assert len(results_1) == len(results_4) == 4

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_rgba_to_rgb_conversion(self):
        """測試 RGBA 到 RGB 轉換"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            doc = fitz.open()
            page = doc.new_page(width=100, height=100)
            doc.save(temp_path)
            doc.close()

            results = pdf_to_images_parallel(temp_path, dpi=72)

            # 檢查圖片是 RGB 格式（3通道）
            img = results[0][1]
            assert img.ndim == 3
            assert img.shape[2] == 3  # RGB

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_empty_pages_list(self):
        """測試空頁面列表"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            doc = fitz.open()
            for i in range(3):
                doc.new_page(width=100, height=100)
            doc.save(temp_path)
            doc.close()

            results = pdf_to_images_parallel(temp_path, pages=[])

            assert len(results) == 0

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestBatchProcessImagesAdvanced:
    """進階批次處理圖片測試"""

    def test_process_with_different_batch_sizes(self):
        """測試不同批次大小"""
        images = [np.ones((5, 5), dtype=np.uint8) * i for i in range(15)]

        def sum_func(img):
            return img.sum()

        # 測試不同批次大小
        for batch_size in [1, 5, 10, 15, 20]:
            results = batch_process_images(
                images=images, process_func=sum_func, batch_size=batch_size
            )
            assert len(results) == 15

    def test_process_with_kwargs(self):
        """測試帶額外參數的處理"""
        images = [np.ones((5, 5), dtype=np.uint8) for _ in range(3)]

        def process_with_multiplier(img, multiplier=1):
            return img.sum() * multiplier

        # 這個測試確認函數簽名
        results = batch_process_images(
            images=images,
            process_func=lambda x: process_with_multiplier(x, multiplier=2),
        )

        assert all(r == 50 for r in results)  # 25 * 2

    def test_preserves_order(self):
        """測試保持處理順序"""
        images = [np.ones((5, 5), dtype=np.uint8) * i for i in range(10)]

        def get_value(img):
            return img[0, 0]

        results = batch_process_images(
            images=images, process_func=get_value, batch_size=3
        )

        # 檢查順序
        expected = list(range(10))
        assert results == expected


class TestGetOptimalWorkersAdvanced:
    """進階最佳工作線程數測試"""

    def test_returns_reasonable_value(self):
        """測試返回合理的值"""
        workers = get_optimal_workers()

        # 應該在 1-32 之間
        assert 1 <= workers <= 32

    def test_consistent_results(self):
        """測試結果一致性"""
        # 多次調用應該返回相同結果
        result1 = get_optimal_workers()
        result2 = get_optimal_workers()

        assert result1 == result2


class TestBatchProcessorEdgeCases:
    """批次處理器邊界情況測試"""

    def test_very_large_batch(self):
        """測試非常大的批次"""
        processor = BatchProcessor(batch_size=1000)

        images = [np.ones((3, 3), dtype=np.uint8) for _ in range(100)]

        results = processor.process_images(images, lambda x: 1)

        assert len(results) == 100

    def test_very_small_batch(self):
        """測試非常小的批次"""
        processor = BatchProcessor(batch_size=1)

        images = [np.ones((3, 3), dtype=np.uint8) for _ in range(5)]

        results = processor.process_images(images, lambda x: 1)

        assert len(results) == 5

    def test_single_worker(self):
        """測試單個工作線程"""
        processor = BatchProcessor(max_workers=1)

        images = [np.ones((3, 3), dtype=np.uint8) for _ in range(10)]

        results = processor.process_images(images, lambda x: x.sum())

        assert len(results) == 10


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
