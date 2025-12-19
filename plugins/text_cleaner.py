#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文字後處理外掛
示例後處理外掛：清理和格式化OCR結果
"""

import re

from paddleocr_toolkit.plugins.base import PostprocessorPlugin


class TextCleanerPlugin(PostprocessorPlugin):
    """
    文字清理外掛

    功能：
    - 移除特殊字元
    - 修正常見錯誤
    - 格式統一化
    """

    name = "Text Cleaner"
    version = "1.0.0"
    author = "PaddleOCR Toolkit Team"
    description = "清理和格式化OCR識別結果"

    def on_init(self) -> bool:
        """初始化外掛"""
        self.remove_special_chars = self.config.get("remove_special_chars", True)
        self.fix_common_errors = self.config.get("fix_common_errors", True)
        self.normalize_spaces = self.config.get("normalize_spaces", True)

        # 常見錯誤對照表
        self.error_corrections = {
            "0": "O",  # 數字0誤認為字母O
            "1": "l",  # 數字1誤認為字母l
            # 更多修正規則...
        }

        self.logger.info("文字清理外掛已初始化")
        return True

    def on_after_ocr(self, results):
        """
        OCR後處理：清理文字

        Args:
            results: OCR識別結果

        Returns:
            清理後的結果
        """
        if isinstance(results, str):
            return self._clean_text(results)
        elif isinstance(results, list):
            return [
                self._clean_text(text) if isinstance(text, str) else text
                for text in results
            ]
        elif isinstance(results, dict):
            # 處理字典格式的結果
            if "text" in results:
                results["text"] = self._clean_text(results["text"])
            return results

        return results

    def _clean_text(self, text: str) -> str:
        """
        清理單個文字字串

        Args:
            text: 原始文字

        Returns:
            清理後的文字
        """
        if not text:
            return text

        cleaned = text

        # 移除特殊字元
        if self.remove_special_chars:
            cleaned = re.sub(r"[^\w\s\u4e00-\u9fff]", "", cleaned)

        # 統一空格
        if self.normalize_spaces:
            cleaned = re.sub(r"\s+", " ", cleaned)
            cleaned = cleaned.strip()

        # 修正常見錯誤
        if self.fix_common_errors:
            for wrong, correct in self.error_corrections.items():
                cleaned = cleaned.replace(wrong, correct)

        self.logger.debug(f"文字清理: {len(text)} -> {len(cleaned)} 字元")

        return cleaned
