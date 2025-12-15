# -*- coding: utf-8 -*-
"""
StatsCollector 單元測試（擴展版）
"""

import os
import sys
import time

import pytest

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paddleocr_toolkit.processors.stats_collector import (
    PageStats,
    ProcessingStats,
    StatsCollector,
)


class TestPageStats:
    """測試 PageStats"""

    def test_basic_creation(self):
        """測試基本建立"""
        stats = PageStats(page_num=0)

        assert stats.page_num == 0
        assert stats.char_count == 0
        assert stats.process_time == 0.0

    def test_to_dict(self):
        """測試轉換為字典"""
        stats = PageStats(
            page_num=1, char_count=200, word_count=50, line_count=10, process_time=2.0
        )

        result = stats.to_dict()

        assert isinstance(result, dict)
        assert result["page_num"] == 1
        assert result["char_count"] == 200

    def test_with_confidence(self):
        """測試帶信賴度的統計"""
        stats = PageStats(page_num=0, char_count=50, avg_confidence=0.95)

        assert stats.avg_confidence == 0.95


class TestStatsCollector:
    """測試 StatsCollector"""

    def test_initialization(self):
        """測試初始化"""
        collector = StatsCollector(input_file="test.pdf", total_pages=10)

        assert collector.stats.total_pages == 10
        assert collector.stats.input_file == "test.pdf"

    def test_page_timing(self):
        """測試頁面計時"""
        collector = StatsCollector(input_file="test.pdf", total_pages=3)

        collector.start_page(0)
        time.sleep(0.01)
        collector.finish_page(0, text="Hello World")

        assert collector.stats.processed_pages == 1

    def test_finish(self):
        """測試完成統計"""
        collector = StatsCollector(input_file="test.pdf", total_pages=2)

        collector.start_page(0)
        collector.finish_page(0, text="Page 1 text")

        collector.start_page(1)
        collector.finish_page(1, text="Page 2 text")

        result = collector.finish()

        assert result is not None
        assert isinstance(result, ProcessingStats)
        assert result.processed_pages == 2

    def test_multiple_pages(self):
        """測試多頁統計"""
        collector = StatsCollector(input_file="test.pdf", mode="hybrid", total_pages=5)

        for i in range(5):
            collector.start_page(i)
            collector.finish_page(i, text="A" * (50 + i * 10))

        result = collector.finish()

        assert result.processed_pages == 5

    def test_add_error(self):
        """測試錯誤記錄"""
        collector = StatsCollector(input_file="test.pdf")

        collector.add_error("Test error 1")
        collector.add_error("Test error 2")

        assert len(collector.stats.errors) == 2


class TestProcessingStats:
    """測試 ProcessingStats"""

    def test_chars_per_page(self):
        """測試每頁字元數計算"""
        stats = ProcessingStats(input_file="test.pdf")
        stats.processed_pages = 10
        stats.total_chars = 1000

        assert stats.chars_per_page == 100.0

    def test_to_summary(self):
        """測試生成摘要"""
        stats = ProcessingStats(input_file="test.pdf", mode="hybrid")
        stats.processed_pages = 10
        stats.total_chars = 1000

        summary = stats.to_summary()

        assert isinstance(summary, str)
        assert "test.pdf" in summary

    def test_zero_pages(self):
        """測試零頁情況"""
        stats = ProcessingStats(input_file="test.pdf")

        # 不應該拋出除以零錯誤
        assert stats.chars_per_page == 0.0
        assert stats.pages_per_second == 0.0

    def test_to_dict(self):
        """測試轉換為字典"""
        stats = ProcessingStats(input_file="test.pdf", mode="basic")

        result = stats.to_dict()

        assert isinstance(result, dict)
        assert result["input_file"] == "test.pdf"
        assert result["mode"] == "basic"

    def test_finish(self):
        """測試標記完成"""
        stats = ProcessingStats(input_file="test.pdf")

        assert stats.end_time is None

        stats.finish()

        assert stats.end_time is not None


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
