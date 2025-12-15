# -*- coding: utf-8 -*-
"""
Batch Processor 單元測試（擴展版）
"""

import os
import sys
import tempfile
import time

import numpy as np
import pytest

# 添加專案路徑
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
        """測試帶參數的處理"""
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
        """測試進度回調"""
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


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
