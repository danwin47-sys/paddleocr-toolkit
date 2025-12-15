# -*- coding: utf-8 -*-
"""
範例插件 - 結果統計
"""

from typing import Any

from paddleocr_toolkit.plugins.base import OCRPlugin


class ResultStatsPlugin(OCRPlugin):
    """
    結果統計插件

    統計並記錄OCR識別到的文字框數量
    """

    name = "ResultStats"
    version = "1.0.0"
    author = "PaddleOCR Toolkit Team"
    description = "統計OCR結果中的文字框數量"

    def on_init(self) -> bool:
        """初始化"""
        self.logger.info("結果統計插件已初始化")
        return True

    def on_before_ocr(self, image: Any) -> Any:
        """前處理 - 不做任何事"""
        return image

    def on_after_ocr(self, results: Any) -> Any:
        """後處理 - 統計數量"""
        try:
            # PaddleOCR 結果結構通常是 list of lines
            # 每個 line 是 [box, (text, score)]

            count = 0
            if isinstance(results, list):
                # 處理不同模式的結果結構
                if len(results) > 0:
                    if isinstance(results[0], list):
                        # 基本模式: [[box, (text, score)], ...]
                        count = len(results[0])  # 通常結果包在第一層 list
                    else:
                        # 可能是其他結構
                        count = len(results)

            self.logger.info(f"OCR 統計: 偵測到 {count} 個文字區塊")

            # 我們也可以修改結果，例如添加統計資訊
            # 但這裡我們只做 logging，不改變結果結構以免影響後續處理

        except Exception as e:
            self.logger.warning(f"統計結果時發生錯誤: {e}")

        return results
