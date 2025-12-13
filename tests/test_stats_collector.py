# -*- coding: utf-8 -*-
"""
統計收集器單元測試
"""

import pytest
import sys
import os
import time

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paddleocr_toolkit.processors.stats_collector import (
    PageStats,
    ProcessingStats,
    StatsCollector
)


class TestPageStats:
    """測試 PageStats 資料結構"""
    
    def test_basic_creation(self):
        """測試基本建立"""
        stats = PageStats(page_num=1, char_count=100, word_count=20)
        assert stats.page_num == 1
        assert stats.char_count == 100
        assert stats.word_count == 20
    
    def test_to_dict(self):
        """測試轉換為字典"""
        stats = PageStats(page_num=0, char_count=50, line_count=5)
        d = stats.to_dict()
        assert d['page_num'] == 0
        assert d['char_count'] == 50
        assert d['line_count'] == 5


class TestStatsCollector:
    """測試 StatsCollector"""
    
    def test_initialization(self):
        """測試初始化"""
        collector = StatsCollector(
            input_file="test.pdf",
            mode="hybrid",
            total_pages=10
        )
        assert collector.stats.input_file == "test.pdf"
        assert collector.stats.mode == "hybrid"
        assert collector.stats.total_pages == 10
    
    def test_page_timing(self):
        """測試頁面計時"""
        collector = StatsCollector(input_file="test.pdf", mode="basic", total_pages=1)
        
        collector.start_page(0)
        time.sleep(0.1)  # 模擬處理時間
        collector.finish_page(0, text="Hello World")
        
        stats = collector.get_stats()
        assert stats.processed_pages == 1
        assert stats.page_stats[0].process_time >= 0.1
    
    def test_finish(self):
        """測試完成處理"""
        collector = StatsCollector(input_file="test.pdf", mode="basic", total_pages=1)
        collector.finish_page(0, text="Test")
        
        final_stats = collector.finish()
        assert final_stats.end_time is not None
        assert final_stats.processed_pages == 1


class TestProcessingStats:
    """測試 ProcessingStats"""
    
    def test_chars_per_page(self):
        """測試每頁平均字數"""
        stats = ProcessingStats(input_file="test.pdf")
        stats.total_chars = 1000
        stats.processed_pages = 10
        assert stats.chars_per_page == 100
    
    def test_to_summary(self):
        """測試生成摘要"""
        stats = ProcessingStats(input_file="test.pdf", mode="hybrid")
        stats.processed_pages = 5
        stats.total_chars = 500
        
        summary = stats.to_summary()
        assert "test.pdf" in summary
        assert "hybrid" in summary


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
