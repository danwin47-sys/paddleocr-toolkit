# -*- coding: utf-8 -*-
"""
範例插件額外測試
測試 paddleocr_toolkit/plugins/example_plugin.py
"""

from unittest.mock import MagicMock

import pytest


class TestResultStatsPluginDetailed:
    """詳細測試範例插件"""

    def test_plugin_description(self):
        """測試插件描述"""
        from paddleocr_toolkit.plugins.example_plugin import ResultStatsPlugin

        plugin = ResultStatsPlugin()
        assert plugin.description is not None

    def test_plugin_author(self):
        """測試插件作者"""
        from paddleocr_toolkit.plugins.example_plugin import ResultStatsPlugin

        plugin = ResultStatsPlugin()
        assert plugin.author is not None

    def test_plugin_config(self):
        """測試插件配置"""
        from paddleocr_toolkit.plugins.example_plugin import ResultStatsPlugin

        plugin = ResultStatsPlugin(config={"key": "value"})
        assert plugin.config == {"key": "value"}

    def test_plugin_on_init(self):
        """測試初始化鉤子"""
        from paddleocr_toolkit.plugins.example_plugin import ResultStatsPlugin

        plugin = ResultStatsPlugin()
        result = plugin.on_init()
        assert result is True

    def test_plugin_on_shutdown(self):
        """測試關閉鉤子"""
        from paddleocr_toolkit.plugins.example_plugin import ResultStatsPlugin

        plugin = ResultStatsPlugin()
        plugin.on_shutdown()  # 不應該拋出錯誤


class TestPluginProcessing:
    """測試插件處理"""

    def test_process_empty_result(self):
        """測試處理空結果"""
        from paddleocr_toolkit.plugins.example_plugin import ResultStatsPlugin

        plugin = ResultStatsPlugin()
        result = plugin.on_after_ocr([])
        assert result is not None

    def test_process_single_item(self):
        """測試處理單個項目"""
        from paddleocr_toolkit.plugins.example_plugin import ResultStatsPlugin

        plugin = ResultStatsPlugin()
        result = plugin.on_after_ocr([{"text": "Hello"}])
        assert result is not None

    def test_process_multiple_items(self):
        """測試處理多個項目"""
        from paddleocr_toolkit.plugins.example_plugin import ResultStatsPlugin

        plugin = ResultStatsPlugin()
        items = [
            {"text": "Hello", "confidence": 0.95},
            {"text": "World", "confidence": 0.90},
        ]
        result = plugin.on_after_ocr(items)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
