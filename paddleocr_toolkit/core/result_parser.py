# -*- coding: utf-8 -*-
"""
OCR 結果解析器 - 統一解析不同引擎的結果

本模組負責：
- 解析不同 OCR 引擎的輸出格式
- 統一結果格式為 OCRResult
- 結果驗證和清理
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    from paddleocr_toolkit.core.models import OCRResult
except ImportError:
    # 降級導入
    from ..models import OCRResult


class OCRResultParser:
    """
    OCR 結果解析器

    支援解析多種 OCR 引擎的輸出：
    - PaddleOCR (basic 模式)
    - PP-StructureV3 (structure/hybrid 模式)
    - PaddleOCR-VL (vl 模式)
    - PP-FormulaNet (formula 模式)

    Example:
        parser = OCRResultParser()
        results = parser.parse_basic_result(predict_output)
        results = parser.parse_structure_result(structure_output)
    """

    def __init__(self, strict_mode: bool = False):
        """
        初始化解析器

        Args:
            strict_mode: 嚴格模式，解析失敗時拋出異常而非返回空列表
        """
        self.strict_mode = strict_mode

    def parse_basic_result(self, predict_result: Any) -> List[OCRResult]:
        """
        解析基本 OCR 引擎結果

        適用於：PaddleOCR basic 模式

        Args:
            predict_result: PaddleOCR predict() 的返回結果

        Returns:
            List[OCRResult]: OCR 結果列表

        Raises:
            ValueError: 當 strict_mode=True 且解析失敗時
        """
        results = []

        try:
            # PaddleOCR 3.x 回傳結果是列表，每個元素代表一個輸入
            for res in predict_result:
                results.extend(self._parse_single_result(res))

            return results

        except Exception as e:
            error_msg = f"解析基本 OCR 結果失敗: {e}"
            logging.error(error_msg)

            if self.strict_mode:
                raise ValueError(error_msg) from e
            else:
                print(f"警告：{error_msg}")
                return []

    def _parse_single_result(self, res: Any) -> List[OCRResult]:
        """
        解析單個結果對象

        Args:
            res: 單個結果對象

        Returns:
            List[OCRResult]: 解析後的結果列表
        """
        results = []

        # 方法 1: 嘗試屬性訪問 (res.rec_texts)
        if hasattr(res, "rec_texts"):
            results.extend(self._parse_from_attributes(res))

        # 方法 2: 嘗試字典訪問 (res['rec_texts'])
        elif hasattr(res, "__getitem__") and isinstance(res, dict):
            results.extend(self._parse_from_dict(res))

        return results

    def _parse_from_attributes(self, res: Any) -> List[OCRResult]:
        """從屬性解析結果"""
        results = []

        texts = getattr(res, "rec_texts", [])
        scores = getattr(res, "rec_scores", [])
        polys = getattr(res, "dt_polys", [])

        for text, score, poly in zip(texts, scores, polys):
            result = self._create_ocr_result(text, score, poly)
            if result:
                results.append(result)

        return results

    def _parse_from_dict(self, res: Dict) -> List[OCRResult]:
        """從字典解析結果"""
        results = []

        texts = res.get("rec_texts", [])
        scores = res.get("rec_scores", [])
        polys = res.get("dt_polys", [])

        for text, score, poly in zip(texts, scores, polys):
            result = self._create_ocr_result(text, score, poly)
            if result:
                results.append(result)

        return results

    def _create_ocr_result(self, text: Any, score: Any, poly: Any) -> Optional[OCRResult]:
        """
        創建 OCRResult 對象

        Args:
            text: 識別文字
            score: 置信度
            poly: 多邊形座標

        Returns:
            Optional[OCRResult]: OCR 結果或 None
        """
        try:
            # 轉換 polygon 為 bbox 格式
            bbox = poly.tolist() if hasattr(poly, "tolist") else list(poly)

            return OCRResult(text=str(text), confidence=float(score), bbox=bbox)
        except Exception as e:
            logging.warning(f"創建 OCRResult 失敗: {e}")
            return None

    def parse_structure_result(
        self, structure_output: Any, extract_ocr: bool = True
    ) -> List[OCRResult]:
        """
        解析結構化引擎結果

        適用於：PP-StructureV3 (structure/hybrid 模式)

        策略：
        1. 優先使用 overall_ocr_res (行級精確座標)
        2. 如果不可用，使用 parsing_res_list (段落級座標)

        Args:
            structure_output: PP-StructureV3 的輸出
            extract_ocr: 是否提取 OCR 結果

        Returns:
            List[OCRResult]: OCR 結果列表
        """
        results = []

        try:
            for res in structure_output:
                # 方法 1: 優先使用 overall_ocr_res (精確座標)
                if hasattr(res, "overall_ocr_res") and extract_ocr:
                    ocr_res = res.overall_ocr_res
                    if ocr_res:
                        results.extend(self._parse_overall_ocr(ocr_res))
                        continue

                # 方法 2: 使用 parsing_res_list (段落級)
                if hasattr(res, "parsing_res_list"):
                    parsing_list = res.parsing_res_list
                    if parsing_list:
                        results.extend(self._parse_parsing_list(parsing_list))

            return results

        except Exception as e:
            error_msg = f"解析結構化結果失敗: {e}"
            logging.error(error_msg)

            if self.strict_mode:
                raise ValueError(error_msg) from e
            else:
                print(f"警告：{error_msg}")
                return []

    def _parse_overall_ocr(self, ocr_res: Any) -> List[OCRResult]:
        """解析 overall_ocr_res (行級結果)"""
        results = []

        # overall_ocr_res 通常是 PaddleOCR 的標準輸出格式
        # 嘗試使用基本解析器
        try:
            results = self.parse_basic_result([ocr_res])
        except Exception as e:
            logging.warning(f"解析 overall_ocr_res 失敗: {e}")

        return results

    def _parse_parsing_list(self, parsing_list: List) -> List[OCRResult]:
        """解析 parsing_res_list (段落級結果)"""
        results = []

        for block in parsing_list:
            try:
                bbox = getattr(block, "bbox", None)
                content = getattr(block, "content", None)

                if bbox is not None and content and str(content).strip():
                    content_str = str(content).strip()

                    if len(bbox) >= 4:
                        # 轉換為標準格式 [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
                        x1, y1, x2, y2 = (
                            float(bbox[0]),
                            float(bbox[1]),
                            float(bbox[2]),
                            float(bbox[3]),
                        )
                        bbox_polygon = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]

                        results.append(
                            OCRResult(
                                text=content_str,
                                confidence=1.0,  # parsing_res_list 通常沒有置信度
                                bbox=bbox_polygon,
                            )
                        )
            except Exception as e:
                logging.warning(f"解析單個 block 失敗: {e}")
                continue

        return results

    def parse_vl_result(self, vl_output: Any) -> List[OCRResult]:
        """
        解析視覺語言模型結果

        適用於：PaddleOCR-VL 模式

        Args:
            vl_output: PaddleOCR-VL 的輸出

        Returns:
            List[OCRResult]: OCR 結果列表
        """
        # VL 模式通常返回與 basic 模式相似的格式
        return self.parse_basic_result(vl_output)

    def parse_formula_result(self, formula_output: Any) -> List[Dict[str, Any]]:
        """
        解析公式識別結果

        適用於：PP-FormulaNet 模式

        Args:
            formula_output: FormulaRecPipeline 的輸出

        Returns:
            List[Dict]: 公式結果列表，每個包含 'latex' 和可選的 'bbox'
        """
        formulas = []

        try:
            for res in formula_output:
                if hasattr(res, "latex"):
                    formula_dict = {"latex": res.latex, "confidence": getattr(res, "score", 1.0)}

                    if hasattr(res, "bbox"):
                        formula_dict["bbox"] = res.bbox

                    formulas.append(formula_dict)
                elif isinstance(res, dict) and "latex" in res:
                    formulas.append(res)

            return formulas

        except Exception as e:
            error_msg = f"解析公式結果失敗: {e}"
            logging.error(error_msg)

            if self.strict_mode:
                raise ValueError(error_msg) from e
            else:
                print(f"警告：{error_msg}")
                return []

    def validate_results(self, results: List[OCRResult]) -> List[OCRResult]:
        """
        驗證並清理結果

        Args:
            results: OCR 結果列表

        Returns:
            List[OCRResult]: 驗證後的結果列表
        """
        valid_results = []

        for result in results:
            # 檢查必要字段
            if not result.text or not result.text.strip():
                continue

            # 檢查置信度範圍
            if not (0.0 <= result.confidence <= 1.0):
                logging.warning(f"置信度超出範圍: {result.confidence}")
                # 修正置信度
                result.confidence = max(0.0, min(1.0, result.confidence))

            # 檢查 bbox
            if not result.bbox or len(result.bbox) < 4:
                logging.warning(f"bbox 格式不正確: {result.bbox}")
                continue

            valid_results.append(result)

        return valid_results

    def filter_by_confidence(
        self, results: List[OCRResult], min_confidence: float = 0.5
    ) -> List[OCRResult]:
        """
        根據置信度過濾結果

        Args:
            results: OCR 結果列表
            min_confidence: 最小置信度閾值

        Returns:
            List[OCRResult]: 過濾後的結果
        """
        return [r for r in results if r.confidence >= min_confidence]

    def sort_by_position(
        self, results: List[OCRResult], reading_order: str = "top-to-bottom"
    ) -> List[OCRResult]:
        """
        根據位置排序結果

        Args:
            results: OCR 結果列表
            reading_order: 閱讀順序 ('top-to-bottom' 或 'left-to-right')

        Returns:
            List[OCRResult]: 排序後的結果
        """
        if reading_order == "top-to-bottom":
            # 先按 Y 座標，再按 X 座標
            return sorted(results, key=lambda r: (r.y, r.x))
        elif reading_order == "left-to-right":
            # 先按 X 座標，再按 Y 座標
            return sorted(results, key=lambda r: (r.x, r.y))
        else:
            return results
