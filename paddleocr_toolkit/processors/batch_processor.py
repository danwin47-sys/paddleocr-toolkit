# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - 批次處理優化

提供多執行緒和批次處理功能以提升效能。
支援串流處理模式以優化記憶體使用。
"""

import logging
from typing import List, Tuple, Optional, Callable, Any, Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

# 串流處理工具
try:
    from ..core.streaming_utils import (
        pdf_pages_generator,
        batch_pages_generator,
        open_pdf_context
    )
    HAS_STREAMING = True
except ImportError:
    HAS_STREAMING = False


def pdf_to_images_parallel(
    pdf_path: str,
    dpi: int = 150,
    max_workers: int = 4,
    pages: Optional[List[int]] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> List[Tuple[int, np.ndarray]]:
    """
    多執行緒將 PDF 轉換為圖片陣列
    
    Args:
        pdf_path: PDF 檔案路徑
        dpi: 解析度（預設 150）
        max_workers: 最大執行緒數（預設 4）
        pages: 指定頁碼列表（None 表示全部）
        progress_callback: 進度回調函數 (current, total)
        
    Returns:
        List[(page_num, image_array)]: 頁碼和圖片陣列的列表
    """
    if not HAS_FITZ:
        raise ImportError("PyMuPDF (fitz) 未安裝")
    if not HAS_NUMPY:
        raise ImportError("NumPy 未安裝")
    
    pdf_doc = fitz.open(pdf_path)
    total_pages = len(pdf_doc)
    
    if pages is None:
        pages = list(range(total_pages))
    
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    
    def convert_page(page_num: int) -> Tuple[int, np.ndarray]:
        """轉換單頁"""
        page = pdf_doc[page_num]
        pixmap = page.get_pixmap(matrix=matrix)
        
        # 轉換為 numpy 陣列
        img_array = np.frombuffer(pixmap.samples, dtype=np.uint8)
        img_array = img_array.reshape(pixmap.height, pixmap.width, pixmap.n)
        
        if pixmap.n == 4:  # RGBA -> RGB
            img_array = img_array[:, :, :3]
        
        return (page_num, img_array)
    
    results = []
    completed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(convert_page, p): p for p in pages}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                completed += 1
                
                if progress_callback:
                    progress_callback(completed, len(pages))
                    
            except Exception as e:
                page_num = futures[future]
                logging.error(f"轉換第 {page_num + 1} 頁失敗: {e}")
    
    pdf_doc.close()
    
    # 按頁碼排序
    results.sort(key=lambda x: x[0])
    return results


def batch_process_images(
    images: List[np.ndarray],
    process_func: Callable[[np.ndarray], Any],
    batch_size: int = 8,
    max_workers: int = 4,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> List[Any]:
    """
    批次處理圖片（多執行緒）
    
    Args:
        images: 圖片陣列列表
        process_func: 處理函數
        batch_size: 批次大小
        max_workers: 最大執行緒數
        progress_callback: 進度回調
        
    Returns:
        處理結果列表
    """
    results = [None] * len(images)
    completed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        
        for i, image in enumerate(images):
            future = executor.submit(process_func, image)
            futures[future] = i
        
        for future in as_completed(futures):
            idx = futures[future]
            try:
                results[idx] = future.result()
                completed += 1
                
                if progress_callback:
                    progress_callback(completed, len(images))
                    
            except Exception as e:
                logging.error(f"處理圖片 {idx} 失敗: {e}")
                results[idx] = None
    
    return results


class BatchProcessor:
    """
    批次處理器 - 統一管理批次處理邏輯
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        batch_size: int = 8,
        show_progress: bool = True
    ):
        """
        初始化批次處理器
        
        Args:
            max_workers: 最大執行緒數
            batch_size: GPU 批次大小
            show_progress: 是否顯示進度
        """
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.show_progress = show_progress
        self._progress_callback = None
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """設定進度回調函數 (current, total, message)"""
        self._progress_callback = callback
    
    def _report_progress(self, current: int, total: int, message: str = ""):
        """回報進度"""
        if self._progress_callback:
            self._progress_callback(current, total, message)
        elif self.show_progress:
            pct = current / total * 100 if total > 0 else 0
            print(f"\r進度: {current}/{total} ({pct:.1f}%) {message}", end="", flush=True)
            if current >= total:
                print()  # 換行
    
    def pdf_to_images(
        self,
        pdf_path: str,
        dpi: int = 150,
        pages: Optional[List[int]] = None
    ) -> List[Tuple[int, np.ndarray]]:
        """多執行緒 PDF 轉圖片"""
        def progress(current, total):
            self._report_progress(current, total, "PDF 轉圖片")
        
        return pdf_to_images_parallel(
            pdf_path=pdf_path,
            dpi=dpi,
            max_workers=self.max_workers,
            pages=pages,
            progress_callback=progress
        )
    
    def process_images(
        self,
        images: List[np.ndarray],
        process_func: Callable[[np.ndarray], Any]
    ) -> List[Any]:
        """批次處理圖片"""
        def progress(current, total):
            self._report_progress(current, total, "處理圖片")
        
        return batch_process_images(
            images=images,
            process_func=process_func,
            batch_size=self.batch_size,
            max_workers=self.max_workers,
            progress_callback=progress
        )
    
    def pdf_pages_stream(
        self,
        pdf_path: str,
        dpi: int = 150,
        pages: Optional[List[int]] = None
    ) -> Generator[Tuple[int, np.ndarray], None, None]:
        """
        串流處理 PDF 頁面（記憶體優化）
        
        使用生成器逐頁返回，記憶體使用恆定。
        適合處理大文件（1000+ 頁）。
        
        Args:
            pdf_path: PDF 檔案路徑
            dpi: 解析度
            pages: 指定頁碼列表
        
        Yields:
            Tuple[int, np.ndarray]: (頁碼, 圖像)
        
        Example:
            processor = BatchProcessor()
            for page_num, image in processor.pdf_pages_stream('large.pdf'):
                result = process(image)
                save(result)
        """
        if not HAS_STREAMING:
            # 降級到舊方法
            logging.warning("串流工具未安裝，使用傳統方法")
            results = self.pdf_to_images(pdf_path, dpi, pages)
            for page_num, image in results:
                yield (page_num, image)
        else:
            yield from pdf_pages_generator(pdf_path, dpi, pages)
    
    def pdf_batch_stream(
        self,
        pdf_path: str,
        dpi: int = 150,
        batch_size: Optional[int] = None,
        pages: Optional[List[int]] = None
    ) -> Generator[List[Tuple[int, np.ndarray]], None, None]:
        """
        批次串流處理 PDF（GPU 優化）
        
        分批返回頁面，適合 GPU 批次處理。
        
        Args:
            pdf_path: PDF 檔案路徑
            dpi: 解析度
            batch_size: 批次大小（None 使用預設）
            pages: 指定頁碼列表
        
        Yields:
            List[Tuple[int, np.ndarray]]: 批次頁面列表
        """
        if batch_size is None:
            batch_size = self.batch_size
        
        if not HAS_STREAMING:
            # 降級到舊方法
            logging.warning("串流工具未安裝，使用傳統方法")
            results = self.pdf_to_images(pdf_path, dpi, pages)
            for i in range(0, len(results), batch_size):
                yield results[i:i+batch_size]
        else:
            yield from batch_pages_generator(pdf_path, dpi, batch_size, pages)


def get_optimal_workers() -> int:
    """
    根據系統資源計算最佳執行緒數
    
    Returns:
        建議的執行緒數
    """
    import os
    cpu_count = os.cpu_count() or 4
    
    # 通常使用 CPU 核心數的一半較佳（避免過度競爭）
    optimal = max(2, cpu_count // 2)
    
    # 上限為 8（避免過多執行緒造成開銷）
    return min(optimal, 8)
