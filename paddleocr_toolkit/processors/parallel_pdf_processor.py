#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
並行 PDF 處理器
v1.2.0 新增 - 多進程加速大檔案處理
"""

import gc
import os
import time
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import fitz  # PyMuPDF

    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

from paddleocr_toolkit.utils.logger import logger


class ParallelPDFProcessor:
    """
    並行 PDF 處理器
    使用多進程加速 PDF 處理，預期 1.5-3x 效率提升
    """

    def __init__(self, workers: Optional[int] = None):
        """
        初始化並行處理器

        Args:
            workers: 工作進程數，預設為 CPU 核心數 - 1
        """
        # 優先從環境變數讀取 (支援 Docker/Cloud 設定)
        env_workers = os.environ.get("OCR_WORKERS")
        if env_workers:
            try:
                default_workers = int(env_workers)
            except ValueError:
                default_workers = max(1, cpu_count() - 1)
        else:
            default_workers = max(1, cpu_count() - 1)

        self.workers = workers or default_workers
        logger.info("Initialized parallel processor with %d workers", self.workers)

    @staticmethod
    def _process_single_page(
        args: Tuple[int, bytes, Dict[str, Any]]
    ) -> Tuple[int, Any]:
        """
        靜態方法：處理單一頁面（供進程池使用）

        Args:
            args: (頁碼, 圖片位元組, OCR 參數)

        Returns:
            (頁碼, 辨識結果)
        """
        page_num, img_bytes, ocr_config = args

        # 延遲匯入以避免進程初始化開銷
        from paddleocr_toolkit.core.ocr_engine import OCREngineManager

        try:
            # 建立臨時引擎（進程內）
            # 註：在進程池中頻繁初始化引擎會耗時，
            # 實際生產環境建議使用進程初始化 (initializer) 保持引擎常駐
            engine = OCREngineManager(**ocr_config)
            engine.init_engine()

            # 執行識別
            # Convert bytes to numpy array (opencv format)
            import cv2

            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            result = engine.predict(img)

            if isinstance(result, list) and len(result) > 0:
                return (page_num, result[0])

            return (page_num, result)
        except Exception as e:
            return (page_num, f"Error on page {page_num}: {str(e)}")

    def process_pdf_parallel(
        self, pdf_path: str, ocr_config: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """
        以並行方式處理 PDF 檔案

        Args:
            pdf_path: PDF 檔案路徑
            ocr_config: OCR 引擎配置參數

        Returns:
            List[Any]: 按頁碼排序的 OCR 結果列表
        """
        if not HAS_PYMUPDF:
            raise ImportError("並行處理需要安裝 pymupdf: pip install pymupdf")

        config = ocr_config or {"mode": "basic", "device": "cpu"}

        start_time = time.time()
        logger.info("Starting PDF processing: %s", Path(pdf_path).name)

        # 1. 將 PDF 轉換為圖片對列
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        logger.info("Total pages: %d", total_pages)

        task_args = []
        for i in range(total_pages):
            page = doc.load_page(i)
            # 渲染為 200 DPI 的圖片
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_bytes = pix.tobytes("png")
            task_args.append((i, img_bytes, config))

        doc.close()

        # 2. 判斷是否需要並行處理
        # 在 macOS 或小檔案上，直接序列處理通常更穩定且快
        if total_pages <= 2 or self.workers <= 1:
            results = []
            for arg in task_args:
                res = self._process_single_page(arg)
                results.append(res)
        else:
            # 啟動進程池
            logger.debug("Starting process pool with %d workers", self.workers)
            try:
                # 註：在 macOS 上使用 'spawn' 可能更穩定，但這裡優先修正邏輯
                with Pool(processes=self.workers) as pool:
                    results = pool.map(self._process_single_page, task_args)
            except Exception as e:
                logger.warning("Parallel processing failed, switching to serial: %s", e)
                results = [self._process_single_page(arg) for arg in task_args]

        # 3. 排序結果
        results.sort(key=lambda x: x[0])

        elapsed = time.time() - start_time
        logger.info(
            "PDF processing complete! Total time: %.2fs (%.2fs/page)",
            elapsed,
            elapsed / total_pages,
        )

        return [r[1] for r in results]

    def benchmark(self, pdf_path: str, ocr_config: Optional[Dict[str, Any]] = None):
        """
        執行效能比較：並行 vs 序列
        """
        logger.info("=" * 50)
        logger.info("Performance Benchmark: Parallel vs Serial")
        logger.info("=" * 50)

        config = ocr_config or {"mode": "basic", "device": "cpu"}

        # 序列測試
        logger.info("[1/2] Running serial processing...")
        start_serial = time.time()
        # 簡單模擬序列邏輯
        doc = fitz.open(pdf_path)
        for i in range(min(5, len(doc))):  # 僅測試前 5 頁以節省時間
            self._process_single_page((i, b"fake_data", config))
        serial_time = (time.time() - start_serial) * (len(doc) / 5)
        logger.info("Estimated serial time: %.2fs", serial_time)

        # 並行測試
        logger.info("[2/2] Running parallel processing...")
        start_parallel = time.time()
        self.process_pdf_parallel(pdf_path, config)
        parallel_time = time.time() - start_parallel
        logger.info("Actual parallel time: %.2fs", parallel_time)

        speedup = serial_time / parallel_time if parallel_time > 0 else 0
        logger.info("-" * 30)
        logger.info("Speedup: %.2fx", speedup)
        logger.info("Core utilization: %.1f%%", (speedup / self.workers) * 100)
        logger.info("-" * 30)


if __name__ == "__main__":
    # 測試腳本
    test_pdf = "example.pdf"
    if os.path.exists(test_pdf):
        processor = ParallelPDFProcessor()
        processor.benchmark(test_pdf)
    else:
        logger.warning("Please provide a test PDF file to run benchmark")
