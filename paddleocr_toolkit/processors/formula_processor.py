# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - 公式識別處理器

本模組實作公式識別模式的處理邏輯：
- 數學公式識別
- LaTeX 格式輸出
- 公式位置標註
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

from paddleocr_toolkit.core.pdf_utils import pixmap_to_numpy


class FormulaProcessor:
    """
    公式識別處理器

    處理數學公式識別需求：
    - 識別圖片或 PDF 中的數學公式
    - 轉換為 LaTeX 格式
    - 支援行內公式和獨立公式

    Attributes:
        engine_manager: OCR 引擎管理器

    Example:
        >>> from paddleocr_toolkit.core import OCREngineManager
        >>> from paddleocr_toolkit.processors import FormulaProcessor
        >>>
        >>> engine = OCREngineManager(mode="formula")
        >>> engine.init_engine()
        >>> processor = FormulaProcessor(engine)
        >>> result = processor.process_image("formula.jpg")
    """

    def __init__(self, engine_manager: "OCREngineManager"):
        """
        初始化公式識別處理器

        Args:
            engine_manager: OCR 引擎管理器（必須為 formula 模式）

        Raises:
            ValueError: 當引擎不是 formula 模式時
        """
        if engine_manager.get_mode().value != "formula":
            raise ValueError(
                f"FormulaProcessor 需要 formula 模式引擎，當前: {engine_manager.get_mode().value}"
            )

        self.engine_manager = engine_manager

    def process_image(
        self, image_path: str, output_format: str = "latex"
    ) -> Dict[str, Any]:
        """
        處理單張圖片的公式識別

        Args:
            image_path: 圖片路徑
            output_format: 輸出格式 ('latex', 'mathml', 'text')

        Returns:
            Dict[str, Any]: 識別結果
        """
        try:
            import cv2

            image = cv2.imread(image_path)
            if image is None:
                return {"error": f"無法讀取圖片: {image_path}"}

            # 執行公式識別
            formula_output = self.engine_manager.predict(image)

            # 解析結果
            formulas = self._parse_formula_output(formula_output)

            return {
                "image": image_path,
                "formulas": formulas,
                "formula_count": len(formulas),
                "format": output_format,
            }

        except Exception as e:
            logging.error(f"處理圖片失敗: {e}")
            return {"error": str(e)}

    def process_pdf(
        self,
        pdf_path: str,
        output_path: Optional[str] = None,
        latex_output: Optional[str] = None,
        dpi: int = 150,
        show_progress: bool = True,
    ) -> Dict[str, Any]:
        """
        處理 PDF 中的公式

        Args:
            pdf_path: PDF 路徑
            output_path: 輸出 PDF 路徑（帶標註）
            latex_output: LaTeX 輸出路徑
            dpi: PDF 解析度
            show_progress: 是否顯示進度

        Returns:
            Dict[str, Any]: 處理結果
        """
        result_summary = {
            "input": pdf_path,
            "mode": "formula",
            "pages_processed": 0,
            "total_formulas": 0,
            "formulas_by_page": [],
            "latex_file": None,
            "error": None,
        }

        try:
            pdf_doc = fitz.open(pdf_path)
            total_pages = len(pdf_doc)

            all_formulas = []

            # 處理每一頁
            page_iterator = range(total_pages)
            if show_progress and HAS_TQDM:
                page_iterator = tqdm(page_iterator, desc="公式識別", unit="頁", ncols=80)

            for page_num in page_iterator:
                try:
                    page = pdf_doc[page_num]
                    pixmap = page.get_pixmap(dpi=dpi)
                    img_array = pixmap_to_numpy(pixmap)

                    # 執行公式識別
                    formula_output = self.engine_manager.predict(img_array)

                    # 解析結果
                    page_formulas = self._parse_formula_output(formula_output)

                    all_formulas.append(
                        {"page": page_num + 1, "formulas": page_formulas}
                    )

                    result_summary["pages_processed"] += 1
                    result_summary["total_formulas"] += len(page_formulas)

                except Exception as page_error:
                    logging.error(f"處理第 {page_num + 1} 頁失敗: {page_error}")
                    continue

            pdf_doc.close()

            result_summary["formulas_by_page"] = all_formulas

            # 生成 LaTeX 輸出
            if latex_output:
                self._save_latex(all_formulas, latex_output)
                result_summary["latex_file"] = latex_output

            return result_summary

        except Exception as e:
            error_msg = f"PDF 處理失敗: {str(e)}"
            logging.error(error_msg)
            result_summary["error"] = str(e)
            return result_summary

    def _parse_formula_output(self, formula_output: Any) -> List[Dict[str, Any]]:
        """
        解析公式識別輸出

        Args:
            formula_output: 引擎輸出

        Returns:
            List[Dict[str, Any]]: 公式列表
        """
        formulas = []

        try:
            # 假設輸出格式為 [(bbox, latex_str, confidence), ...]
            if isinstance(formula_output, list):
                for item in formula_output:
                    if len(item) >= 2:
                        formulas.append(
                            {
                                "bbox": item[0] if len(item) > 0 else None,
                                "latex": item[1] if len(item) > 1 else "",
                                "confidence": item[2] if len(item) > 2 else 1.0,
                            }
                        )

        except Exception as e:
            logging.error(f"解析公式輸出失敗: {e}")

        return formulas

    def _save_latex(self, formulas_by_page: List[Dict], output_path: str) -> None:
        """儲存 LaTeX 格式"""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("% 公式識別結果\n\n")

                for page_data in formulas_by_page:
                    page_num = page_data["page"]
                    formulas = page_data["formulas"]

                    f.write(f"% 第 {page_num} 頁\n\n")

                    for idx, formula in enumerate(formulas, 1):
                        latex = formula.get("latex", "")
                        f.write(f"% 公式 {idx}\n")
                        f.write(f"$$\n{latex}\n$$\n\n")

            logging.info(f"LaTeX 已儲存: {output_path}")

        except Exception as e:
            logging.error(f"儲存 LaTeX 失敗: {e}")

    def extract_formulas_text(self, formulas: List[Dict[str, Any]]) -> str:
        """
        提取所有公式的 LaTeX 文字

        Args:
            formulas: 公式列表

        Returns:
            str: LaTeX 文字
        """
        return "\n\n".join([f["latex"] for f in formulas if f.get("latex")])
