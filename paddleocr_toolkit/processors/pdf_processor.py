# -*- coding: utf-8 -*-
"""
PDF 處理器 - 專用於 PDF 文件的 OCR 處理

本模組負責：
- PDF 文件處理
- 可搜索 PDF 生成
- PDF 轉圖像
- 批次處理
"""

import gc
import logging
from pathlib import Path
from typing import Callable, List, Optional, Tuple

try:
    import fitz

    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from paddleocr_toolkit.core.models import OCRResult
    from paddleocr_toolkit.core.pdf_generator import PDFGenerator
    from paddleocr_toolkit.core.pdf_utils import pixmap_to_numpy
except ImportError:
    # 降級導入
    from ..core.models import OCRResult
    from ..core.pdf_generator import PDFGenerator
    from ..core.pdf_utils import pixmap_to_numpy


class PDFProcessor:
    """
    PDF 專用處理器

    提供 PDF 文件的 OCR 處理功能，包括：
    - 逐頁 OCR 處理
    - 可搜索 PDF 生成
    - 進度報告

    Example:
        processor = PDFProcessor(ocr_func=ocr_engine.predict)
        results, output_path = processor.process_pdf(
            pdf_path='document.pdf',
            searchable=True,
            dpi=200
        )
    """

    def __init__(
        self, ocr_func: Callable, result_parser: Optional[Callable] = None, debug_mode: bool = False
    ):
        """
        初始化 PDF 處理器

        Args:
            ocr_func: OCR 處理函數（接受圖像，返回結果）
            result_parser: 結果解析函數（可選）
            debug_mode: DEBUG 模式
        """
        if not HAS_FITZ:
            raise ImportError("PyMuPDF 未安裝")
        if not HAS_NUMPY:
            raise ImportError("NumPy 未安裝")

        self.ocr_func = ocr_func
        self.result_parser = result_parser
        self.debug_mode = debug_mode

    def process_pdf(
        self,
        pdf_path: str,
        output_path: Optional[str] = None,
        searchable: bool = False,
        dpi: int = 200,
        show_progress: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Tuple[List[List[OCRResult]], Optional[str]]:
        """
        處理 PDF 文件進行 OCR

        Args:
            pdf_path: PDF 檔案路徑
            output_path: 輸出檔案路徑（可選）
            searchable: 是否生成可搜尋 PDF
            dpi: PDF 轉圖片的解析度
            show_progress: 是否顯示進度
            progress_callback: 進度回調函數 (current, total)

        Returns:
            Tuple[List[List[OCRResult]], Optional[str]]:
                (每頁的 OCR 結果列表, 輸出檔案路徑)
        """
        all_results = []

        try:
            # 打開 PDF
            logging.info(f"打開 PDF: {pdf_path}")
            pdf_doc = fitz.open(pdf_path)
            total_pages = len(pdf_doc)
            print(f"正在處理 PDF: {pdf_path} ({total_pages} 頁)")

            # 設定 PDF 生成器
            output_path, pdf_generator = self._setup_pdf_generator(
                pdf_path, output_path, searchable
            )

            # 處理每一頁
            for page_num in range(total_pages):
                try:
                    page = pdf_doc[page_num]
                    page_results = self._process_single_page(
                        page, page_num, total_pages, dpi, pdf_generator, show_progress
                    )
                    all_results.append(page_results)

                    # 報告進度
                    if progress_callback:
                        progress_callback(page_num + 1, total_pages)
                    elif show_progress:
                        print(f"  處理第 {page_num + 1}/{total_pages} 頁...")

                except Exception as page_error:
                    logging.error(f"處理第 {page_num + 1} 頁錯誤: {page_error}")
                    print(f"  [WARN] 處理第 {page_num + 1} 頁錯誤:{page_error}")
                    all_results.append([])
                    gc.collect()

            pdf_doc.close()

            # 保存可搜索 PDF
            if pdf_generator:
                pdf_generator.save()

            logging.info(f"[OK] 完成處理 {total_pages} 頁")
            return all_results, output_path

        except Exception as e:
            logging.error(f"處理 PDF 失敗 ({pdf_path}): {e}")
            print(f"錯誤：處理 PDF 失敗: {e}")
            return all_results, None

    def _setup_pdf_generator(
        self, pdf_path: str, output_path: Optional[str], searchable: bool
    ) -> Tuple[Optional[str], Optional[PDFGenerator]]:
        """設定 PDF 生成器"""
        if not searchable:
            return output_path, None

        # 生成輸出路徑
        if not output_path:
            pdf_file = Path(pdf_path)
            output_path = str(pdf_file.parent / f"{pdf_file.stem}_searchable.pdf")

        # 創建 PDF 生成器
        pdf_generator = PDFGenerator(output_path=output_path, debug_mode=self.debug_mode)

        return output_path, pdf_generator

    def _process_single_page(
        self,
        page,
        page_num: int,
        total_pages: int,
        dpi: int,
        pdf_generator: Optional[PDFGenerator],
        show_progress: bool,
    ) -> List[OCRResult]:
        """處理單個 PDF 頁面"""
        logging.info(f"開始處理第 {page_num + 1}/{total_pages} 頁")

        # 轉換為圖片
        zoom = dpi / 72.0
        pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        img_array = pixmap_to_numpy(pixmap)

        # 執行 OCR
        ocr_result = self.ocr_func(img_array)

        # 解析結果
        if self.result_parser:
            page_results = self.result_parser(ocr_result)
        else:
            # 假設已經是 OCRResult 列表
            page_results = ocr_result if isinstance(ocr_result, list) else []

        # 縮放座標（從 DPI 空間回到 PDF 空間）
        scale_factor = 72.0 / dpi
        for result in page_results:
            result.bbox = [[p[0] * scale_factor, p[1] * scale_factor] for p in result.bbox]

        # 添加到可搜索 PDF
        if pdf_generator:
            original_pixmap = page.get_pixmap()
            pdf_generator.add_page_from_pixmap(original_pixmap, page_results)
            del original_pixmap

        # 清理
        del pixmap, img_array
        gc.collect()

        return page_results

    def get_text(self, results: List[OCRResult], separator: str = "\n") -> str:
        """
        從 OCR 結果中提取純文字

        Args:
            results: OCR 結果列表
            separator: 行分隔符

        Returns:
            str: 合併的純文字
        """
        return separator.join(r.text for r in results if r.text.strip())

    def extract_all_text(
        self, all_results: List[List[OCRResult]], page_separator: str = "\n\n---\n\n"
    ) -> str:
        """
        提取所有頁面的文字

        Args:
            all_results: 所有頁面的 OCR 結果
            page_separator: 頁面分隔符

        Returns:
            str: 所有頁面的文字
        """
        page_texts = []
        for page_num, page_results in enumerate(all_results, 1):
            page_text = self.get_text(page_results)
            if page_text:
                page_texts.append(f"=== 第 {page_num} 頁 ===\n{page_text}")

        return page_separator.join(page_texts)
