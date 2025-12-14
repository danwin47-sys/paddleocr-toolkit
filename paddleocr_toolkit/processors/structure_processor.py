# -*- coding: utf-8 -*-
"""
結構化處理器 - 專用於結構化文件分析

本模組負責：
- PP-StructureV3 處理
- 版面分析
- 表格提取
- Markdown/JSON/HTML 輸出
"""

import logging
from typing import Any, Callable, Dict, List, Optional

try:
    from paddleocr_toolkit.core.models import OCRResult
except ImportError:
    from ..core.models import OCRResult


class StructureProcessor:
    """
    結構化文件處理器

    使用 PP-StructureV3 進行版面分析和內容提取

    Example:
        processor = StructureProcessor(structure_engine=engine)
        results = processor.process(input_path='document.pdf')
    """

    def __init__(self, structure_engine: Any, result_parser: Optional[Callable] = None):
        """
        初始化結構化處理器

        Args:
            structure_engine: PP-StructureV3 引擎
            result_parser: 結果解析器（可選）
        """
        self.structure_engine = structure_engine
        self.result_parser = result_parser

    def process(
        self, input_path: str, extract_tables: bool = True, extract_text: bool = True
    ) -> Dict[str, Any]:
        """
        處理結構化文件

        Args:
            input_path: 輸入檔案路徑
            extract_tables: 是否提取表格
            extract_text: 是否提取文字

        Returns:
            Dict: 處理結果
        """
        try:
            # 執行結構化分析
            structure_output = self.structure_engine.predict(input=input_path)

            results = {
                "input": input_path,
                "structure_output": structure_output,
            }

            # 提取文字
            if extract_text and self.result_parser:
                ocr_results = self.result_parser(structure_output)
                results["ocr_results"] = ocr_results
                results["text"] = self._extract_text(ocr_results)

            # 提取表格
            if extract_tables:
                tables = self._extract_tables(structure_output)
                results["tables"] = tables

            return results

        except Exception as e:
            logging.error(f"結構化處理失敗: {e}")
            return {"error": str(e)}

    def _extract_text(self, ocr_results: List[OCRResult]) -> str:
        """提取文字"""
        return "\n".join(r.text for r in ocr_results if r.text.strip())

    def _extract_tables(self, structure_output: Any) -> List[Dict]:
        """
        提取表格

        Args:
            structure_output: PP-StructureV3 輸出

        Returns:
            List[Dict]: 表格列表
        """
        tables = []

        try:
            for res in structure_output:
                if hasattr(res, "parsing_res_list"):
                    for item in res.parsing_res_list:
                        if hasattr(item, "type") and item.type == "table":
                            table_data = {
                                "type": "table",
                                "content": getattr(item, "content", ""),
                                "bbox": getattr(item, "bbox", None),
                            }
                            tables.append(table_data)
        except Exception as e:
            logging.warning(f"提取表格失敗: {e}")

        return tables

    def analyze_layout(self, structure_output: Any) -> Dict[str, Any]:
        """
        分析版面結構

        Args:
            structure_output: PP-StructureV3 輸出

        Returns:
            Dict: 版面分析結果
        """
        layout = {"text_blocks": 0, "tables": 0, "images": 0, "other": 0}

        try:
            for res in structure_output:
                if hasattr(res, "parsing_res_list"):
                    for item in res.parsing_res_list:
                        item_type = getattr(item, "type", "other")
                        if item_type == "text":
                            layout["text_blocks"] += 1
                        elif item_type == "table":
                            layout["tables"] += 1
                        elif item_type == "figure":
                            layout["images"] += 1
                        else:
                            layout["other"] += 1
        except Exception as e:
            logging.warning(f"版面分析失敗: {e}")

        return layout
