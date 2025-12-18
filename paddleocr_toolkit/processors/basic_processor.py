# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - 基本模式處理器

本模組實作基本 OCR 模式的處理邏輯：
- 單張圖片 OCR
- 批次圖片處理
- 基本 PDF 處理（不含版面分析）
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import fitz  # PyMuPDF

if TYPE_CHECKING:
    from paddleocr_toolkit.core import OCREngineManager

try:
    from tqdm import tqdm

    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

from paddleocr_toolkit.core import OCRResult, PDFGenerator
from paddleocr_toolkit.core.pdf_utils import pixmap_to_numpy
from paddleocr_toolkit.core.result_parser import OCRResultParser


class BasicProcessor:
    """
    基本模式處理器

    處理基本 OCR 需求：
    - 單張圖片 OCR
    - 批次圖片處理
    - 簡單 PDF 轉可搜尋 PDF

    不包含版面分析，適合簡單文字識別場景。

    Attributes:
        engine_manager: OCR 引擎管理器
        result_parser: 結果解析器
        debug_mode: 除錯模式
        compress_images: 是否壓縮圖片
        jpeg_quality: JPEG 壓縮品質

    Example:
        >>> from paddleocr_toolkit.core import OCREngineManager
        >>> from paddleocr_toolkit.processors import BasicProcessor
        >>>
        >>> engine = OCREngineManager(mode="basic")
        >>> engine.init_engine()
        >>> processor = BasicProcessor(engine)
        >>> result = processor.process_image("document.jpg")
    """

    def __init__(
        self,
        engine_manager: "OCREngineManager",
        debug_mode: bool = False,
        compress_images: bool = True,
        jpeg_quality: int = 85,
    ):
        """
        初始化基本模式處理器

        Args:
            engine_manager: OCR 引擎管理器（必須為 basic 模式）
            debug_mode: 是否啟用除錯模式（顯示粉紅色文字層）
            compress_images: 是否啟用圖片壓縮
            jpeg_quality: JPEG 壓縮品質 (0-100)

        Raises:
            ValueError: 當引擎不是 basic 模式時
        """
        if engine_manager.get_mode().value != "basic":
            raise ValueError(
                f"BasicProcessor 需要 basic 模式引擎，當前: {engine_manager.get_mode().value}"
            )

        self.engine_manager = engine_manager
        self.result_parser = OCRResultParser()
        self.debug_mode = debug_mode
        self.compress_images = compress_images
        self.jpeg_quality = jpeg_quality

    def process_image(
        self, image_path: str, output_format: str = "dict"
    ) -> Dict[str, Any]:
        """
        處理單張圖片

        Args:
            image_path: 圖片路徑
            output_format: 輸出格式 ('dict', 'text', 'json')

        Returns:
            Dict[str, Any]: 處理結果
        """
        try:
            import cv2

            # 讀取圖片
            image = cv2.imread(image_path)
            if image is None:
                return {"error": f"無法讀取圖片: {image_path}"}

            # 執行 OCR
            ocr_output = self.engine_manager.predict(image)

            # 解析結果
            ocr_results = self.result_parser.parse_basic_result(ocr_output)

            # 格式化輸出
            if output_format == "text":
                return {"text": "\n".join([r.text for r in ocr_results])}
            elif output_format == "json":
                return {
                    "results": [
                        {
                            "text": r.text,
                            "confidence": r.confidence,
                            "bbox": r.bbox,
                        }
                        for r in ocr_results
                    ]
                }
            else:  # dict
                return {
                    "image": image_path,
                    "ocr_results": ocr_results,
                    "text_count": len(ocr_results),
                }

        except Exception as e:
            logging.error(f"處理圖片失敗: {e}")
            return {"error": str(e)}

    def process_batch(
        self, image_paths: List[str], show_progress: bool = True
    ) -> List[Dict[str, Any]]:
        """
        批次處理多張圖片

        Args:
            image_paths: 圖片路徑列表
            show_progress: 是否顯示進度條

        Returns:
            List[Dict[str, Any]]: 處理結果列表
        """
        results = []

        iterator = image_paths
        if show_progress and HAS_TQDM:
            iterator = tqdm(iterator, desc="批次處理", unit="圖片", ncols=80)

        for image_path in iterator:
            result = self.process_image(image_path)
            results.append(result)

        return results

    def process_pdf(
        self,
        pdf_path: str,
        output_path: Optional[str] = None,
        dpi: int = 150,
        show_progress: bool = True,
    ) -> Dict[str, Any]:
        """
        處理 PDF（基本模式）

        將 PDF 轉換為可搜尋 PDF，不進行版面分析。

        Args:
            pdf_path: PDF 路徑
            output_path: 輸出可搜尋 PDF 路徑
            dpi: PDF 轉圖片解析度
            show_progress: 是否顯示進度條

        Returns:
            Dict[str, Any]: 處理結果
        """
        result_summary = {
            "input": pdf_path,
            "mode": "basic",
            "pages_processed": 0,
            "searchable_pdf": None,
            "error": None,
        }

        try:
            # 設定輸出路徑
            if not output_path:
                pdf_path_obj = Path(pdf_path)
                output_path = str(
                    pdf_path_obj.parent / f"{pdf_path_obj.stem}_searchable.pdf"
                )

            # 打開 PDF
            pdf_doc = fitz.open(pdf_path)
            total_pages = len(pdf_doc)

            # 建立 PDF 生成器
            pdf_generator = PDFGenerator(
                output_path,
                debug_mode=self.debug_mode,
                compress_images=self.compress_images,
                jpeg_quality=self.jpeg_quality,
            )

            # 處理每一頁
            page_iterator = range(total_pages)
            if show_progress and HAS_TQDM:
                page_iterator = tqdm(
                    page_iterator, desc="處理 PDF", unit="頁", ncols=80
                )

            for page_num in page_iterator:
                try:
                    page = pdf_doc[page_num]
                    pixmap = page.get_pixmap(dpi=dpi)
                    img_array = pixmap_to_numpy(pixmap)

                    # OCR
                    ocr_output = self.engine_manager.predict(img_array)
                    ocr_results = self.result_parser.parse_basic_result(ocr_output)

                    # 加入 PDF
                    pdf_generator.add_page_from_pixmap(pixmap, ocr_results)
                    result_summary["pages_processed"] += 1

                except Exception as page_error:
                    logging.error(f"處理第 {page_num + 1} 頁失敗: {page_error}")
                    continue

            pdf_doc.close()

            # 儲存 PDF
            if pdf_generator.save():
                result_summary["searchable_pdf"] = output_path
                print(f"[OK] 可搜尋 PDF 已儲存：{output_path}")

            return result_summary

        except Exception as e:
            error_msg = f"PDF 處理失敗: {str(e)}"
            logging.error(error_msg)
            result_summary["error"] = str(e)
            return result_summary

    def get_text(
        self, ocr_results: List[OCRResult], separator: str = "\n"
    ) -> str:
        """
        從 OCR 結果提取純文字

        Args:
            ocr_results: OCR 結果列表
            separator: 文字分隔符

        Returns:
            str: 提取的文字
        """
        return separator.join([r.text for r in ocr_results])

    def filter_by_confidence(
        self, ocr_results: List[OCRResult], min_confidence: float = 0.5
    ) -> List[OCRResult]:
        """
        根據置信度過濾結果

        Args:
            ocr_results: OCR 結果列表
            min_confidence: 最小置信度閾值

        Returns:
            List[OCRResult]: 過濾後的結果
        """
        return [r for r in ocr_results if r.confidence >= min_confidence]
