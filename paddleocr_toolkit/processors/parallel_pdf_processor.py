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
        self.workers = workers or max(1, cpu_count() - 1)
        print(f"初始化並行處理器: 使用 {self.workers} 個工作進程")

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

            # 解析並簡化結果，只保留可序列化的數據 (避免 pickle 錯誤)
            safe_result = []
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict):
                        # PaddleX 格式: 提取 rec_texts, rec_scores
                        safe_item = {}
                        if 'rec_texts' in item:
                            safe_item['rec_texts'] = item['rec_texts']
                        if 'rec_scores' in item:
                            safe_item['rec_scores'] = item['rec_scores']
                        if 'rec_boxes' in item and hasattr(item['rec_boxes'], 'tolist'):
                            safe_item['rec_boxes'] = item['rec_boxes'].tolist()
                        
                        # 如果沒有標準鍵，嘗試保留所有字串/數字類型的鍵
                        if not safe_item:
                             for k, v in item.items():
                                 if isinstance(v, (str, int, float, list, dict)) and k not in ['vis_fonts', 'doc_preprocessor_res']:
                                     safe_item[k] = v
                        safe_result.append(safe_item)
                    elif isinstance(item, (list, tuple)):
                        # 標準 PaddleOCR 格式: [box, (text, score)]
                        # 這通常是可序列化的，但為了安全可以檢查
                        safe_result.append(item)
                    else:
                        safe_result.append(str(item))
            elif isinstance(result, dict):
                # 單個字典結果
                safe_item = {}
                if 'rec_texts' in result:
                    safe_item['rec_texts'] = result['rec_texts']
                if 'rec_scores' in result:
                    safe_item['rec_scores'] = result['rec_scores']
                 # 避免返回大圖片或不可序列化的對象
                safe_result = [safe_item]
            else:
                safe_result = str(result)

            return (page_num, safe_result)
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
        print(f"開始並行處理: {Path(pdf_path).name}")

        # 1. 將 PDF 轉換為圖片對列
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"總頁數: {total_pages}")

        task_args = []
        for i in range(total_pages):
            page = doc.load_page(i)
            # 渲染為 200 DPI 的圖片
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_bytes = pix.tobytes("png")
            task_args.append((i, img_bytes, config))

        doc.close()

        # 2. 啟動進程池
        print(f"啟動進程池 (Workers: {self.workers})...")
        with Pool(processes=self.workers) as pool:
            results = pool.map(self._process_single_page, task_args)

        # 3. 排序結果
        results.sort(key=lambda x: x[0])

        elapsed = time.time() - start_time
        print(f"並行處理完成！總耗時: {elapsed:.2f}s ({elapsed/total_pages:.2f}s/頁)")

        return [r[1] for r in results]

    def benchmark(self, pdf_path: str, ocr_config: Optional[Dict[str, Any]] = None):
        """
        執行效能比較：並行 vs 序列
        """
        print("\n" + "=" * 50)
        print("🚀 效能基準測試：並行 vs 序列")
        print("=" * 50)

        config = ocr_config or {"mode": "basic", "device": "cpu"}

        # 序列測試
        print("\n[1/2] 正在進行序列處理...")
        start_serial = time.time()
        # 簡單模擬序列邏輯
        doc = fitz.open(pdf_path)
        for i in range(min(5, len(doc))):  # 僅測試前 5 頁以節省時間
            self._process_single_page((i, b"fake_data", config))
        serial_time = (time.time() - start_serial) * (len(doc) / 5)
        print(f"預估序列總耗時: {serial_time:.2f}s")

        # 並行測試
        print("\n[2/2] 正在進行並行處理...")
        start_parallel = time.time()
        self.process_pdf_parallel(pdf_path, config)
        parallel_time = time.time() - start_parallel
        print(f"實際並行總耗時: {parallel_time:.2f}s")

        speedup = serial_time / parallel_time if parallel_time > 0 else 0
        print("\n" + "-" * 30)
        print(f"加速比: {speedup:.2f}x")
        print(f"核心利用率: {(speedup/self.workers)*100:.1f}%")
        print("-" * 30)


if __name__ == "__main__":
    # 測試腳本
    test_pdf = "example.pdf"
    if os.path.exists(test_pdf):
        processor = ParallelPDFProcessor()
        processor.benchmark(test_pdf)
    else:
        print("請提供測試用的 PDF 檔案以執行 benchmark")
