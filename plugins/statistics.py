#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統計插件
示例全功能插件：收集OCR處理統計資訊
"""

import time
from typing import Any, Dict

from paddleocr_toolkit.plugins.base import OCRPlugin


class StatisticsPlugin(OCRPlugin):
    """
    統計插件

    功能：
    - 記錄處理次數
    - 計算平均處理時間
    - 追蹤成功率
    """

    name = "Statistics Collector"
    version = "1.0.0"
    author = "PaddleOCR Toolkit Team"
    description = "收集和分析OCR處理統計資訊"

    def on_init(self) -> bool:
        """初始化插件"""
        self.stats = {
            "total_processed": 0,
            "total_time": 0.0,
            "errors": 0,
            "success": 0,
        }

        self.current_start_time = None

        self.logger.info("統計插件已初始化")
        return True

    def on_before_ocr(self, image: Any) -> Any:
        """記錄開始時間"""
        self.current_start_time = time.time()
        return image

    def on_after_ocr(self, results: Any) -> Any:
        """記錄結束時間和統計"""
        if self.current_start_time:
            elapsed = time.time() - self.current_start_time

            self.stats["total_processed"] += 1
            self.stats["total_time"] += elapsed
            self.stats["success"] += 1

            avg_time = self.stats["total_time"] / self.stats["total_processed"]

            self.logger.info(f"處理完成 (耗時: {elapsed:.2f}s, 平均: {avg_time:.2f}s)")

            self.current_start_time = None

        return results

    def on_error(self, error: Exception) -> None:
        """記錄錯誤"""
        self.stats["errors"] += 1
        self.stats["total_processed"] += 1

        super().on_error(error)

    def get_statistics(self) -> Dict:
        """
        取得統計資訊

        Returns:
            統計資料字典
        """
        stats = self.stats.copy()

        if stats["total_processed"] > 0:
            stats["average_time"] = stats["total_time"] / stats["total_processed"]
            stats["success_rate"] = stats["success"] / stats["total_processed"]
        else:
            stats["average_time"] = 0
            stats["success_rate"] = 0

        return stats

    def reset_statistics(self) -> None:
        """重置統計資訊"""
        self.stats = {
            "total_processed": 0,
            "total_time": 0.0,
            "errors": 0,
            "success": 0,
        }
        self.logger.info("統計資訊已重置")

    def print_statistics(self) -> None:
        """印出統計資訊"""
        stats = self.get_statistics()

        print("\n" + "=" * 50)
        print("OCR處理統計")
        print("=" * 50)
        print(f"總處理數: {stats['total_processed']}")
        print(f"成功數: {stats['success']}")
        print(f"錯誤數: {stats['errors']}")
        print(f"成功率: {stats['success_rate']:.1%}")
        print(f"總時間: {stats['total_time']:.2f}s")
        print(f"平均時間: {stats['average_time']:.3f}s")
        print("=" * 50)
