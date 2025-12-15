# -*- coding: utf-8 -*-
"""
串流處理工具 - 記憶體優化的核心

提供生成器模式的 PDF 處理，避免一次載入所有頁面到記憶體。
"""

import gc
from contextlib import contextmanager
from typing import Generator, List, Optional, Tuple

import numpy as np

try:
    import fitz

    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False


@contextmanager
def open_pdf_context(pdf_path: str):
    """
    PDF 文件 context manager

    確保資源自動釋放，避免文件句柄洩漏。

    Args:
        pdf_path: PDF 檔案路徑

    Yields:
        fitz.Document: PDF 文件物件

    Example:
        with open_pdf_context('document.pdf') as pdf_doc:
            for page in pdf_doc:
                process(page)
        # 自動關閉並釋放資源
    """
    if not HAS_FITZ:
        raise ImportError("PyMuPDF 未安裝")

    pdf_doc = fitz.open(pdf_path)
    try:
        yield pdf_doc
    finally:
        pdf_doc.close()
        # 強制垃圾回收
        gc.collect()


def pdf_pages_generator(
    pdf_path: str, dpi: int = 150, pages: Optional[List[int]] = None
) -> Generator[Tuple[int, np.ndarray], None, None]:
    """
    以生成器方式逐頁處理 PDF（記憶體優化）

    優點：
    - 記憶體使用固定（僅 1 頁）
    - 支援大文件處理（1000+ 頁）
    - 自動資源管理

    Args:
        pdf_path: PDF 檔案路徑
        dpi: 解析度（預設 150）
        pages: 指定頁碼列表（None 表示全部）

    Yields:
        Tuple[int, np.ndarray]: (頁碼, 圖像陣列)

    Example:
        # 處理大文件，記憶體使用恆定
        for page_num, image in pdf_pages_generator('large.pdf'):
            result = ocr_process(image)
            save_result(result)
            # image 自動釋放，記憶體不累積
    """
    if not HAS_FITZ:
        raise ImportError("PyMuPDF 未安裝")

    with open_pdf_context(pdf_path) as pdf_doc:
        total_pages = len(pdf_doc)

        # 決定要處理的頁面
        page_list = pages if pages is not None else range(total_pages)

        # 縮放矩陣（預先計算）
        scale = dpi / 72.0
        matrix = fitz.Matrix(scale, scale)

        for page_num in page_list:
            # 載入頁面
            page = pdf_doc[page_num]

            # 轉換為圖像（不複製以節省記憶體）
            pixmap = page.get_pixmap(matrix=matrix)

            # 轉換為 numpy 陣列
            img_array = np.frombuffer(pixmap.samples, dtype=np.uint8)
            img_array = img_array.reshape(pixmap.height, pixmap.width, pixmap.n)

            # RGBA → RGB
            if pixmap.n == 4:
                img_array = img_array[:, :, :3]

            # 複製一份（因為 pixmap 會被釋放）
            image = img_array.copy()

            # 返回結果
            yield (page_num, image)

            # 立即釋放資源
            del img_array
            del pixmap
            del image


def batch_pages_generator(
    pdf_path: str,
    dpi: int = 150,
    batch_size: int = 8,
    pages: Optional[List[int]] = None,
) -> Generator[List[Tuple[int, np.ndarray]], None, None]:
    """
    批次生成器（用於 GPU 批次處理）

    將頁面分批返回，適合 GPU 批次處理。

    Args:
        pdf_path: PDF 檔案路徑
        dpi: 解析度
        batch_size: 批次大小（預設 8）
        pages: 指定頁碼列表

    Yields:
        List[Tuple[int, np.ndarray]]: 批次的頁面列表

    Example:
        # GPU 批次處理
        for batch in batch_pages_generator('doc.pdf', batch_size=8):
            results = gpu_ocr_batch(batch)
            save_batch_results(results)
    """
    batch = []

    for page_data in pdf_pages_generator(pdf_path, dpi, pages):
        batch.append(page_data)

        if len(batch) >= batch_size:
            yield batch
            batch = []
            # 強制垃圾回收
            gc.collect()

    # 返回剩餘的批次
    if batch:
        yield batch


class StreamingPDFProcessor:
    """
    串流 PDF 處理器

    使用生成器模式處理 PDF，記憶體使用恆定。
    """

    def __init__(self, pdf_path: str, dpi: int = 150):
        """
        初始化處理器

        Args:
            pdf_path: PDF 檔案路徑
            dpi: 解析度
        """
        self.pdf_path = pdf_path
        self.dpi = dpi

    def process_pages(
        self,
        process_func,
        pages: Optional[List[int]] = None,
        show_progress: bool = True,
    ):
        """
        逐頁處理（串流模式）

        Args:
            process_func: 處理函數 (image) -> result
            pages: 指定頁碼列表
            show_progress: 是否顯示進度

        Yields:
            處理結果
        """
        try:
            from tqdm import tqdm

            HAS_TQDM = True
        except ImportError:
            HAS_TQDM = False

        # 取得總頁數
        with open_pdf_context(self.pdf_path) as pdf_doc:
            total_pages = len(pdf_doc) if pages is None else len(pages)

        # 建立進度條
        iterator = pdf_pages_generator(self.pdf_path, self.dpi, pages)
        if show_progress and HAS_TQDM:
            iterator = tqdm(iterator, total=total_pages, desc="處理頁面")

        # 逐頁處理
        for page_num, image in iterator:
            result = process_func(image)
            yield (page_num, result)

            # 釋放資源
            del image

            # 定期垃圾回收（每 10 頁）
            if page_num % 10 == 0:
                gc.collect()
