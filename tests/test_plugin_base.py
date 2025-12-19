# -*- coding: utf-8 -*-
"""
外掛基礎類別測試
測試 paddleocr_toolkit/plugins/base.py
"""

from unittest.mock import MagicMock

import pytest


class TestOCRPluginBase:
    """測試 OCR 外掛基礎類別"""

    def test_import_ocr_plugin(self):
        """測試匯入 OCRPlugin"""
        from paddleocr_toolkit.plugins.base import OCRPlugin

        assert OCRPlugin is not None

    def test_import_example_plugin(self):
        """測試匯入範例外掛"""
        from paddleocr_toolkit.plugins.example_plugin import ResultStatsPlugin

        assert ResultStatsPlugin is not None


class TestResultStatsPlugin:
    """測試範例外掛"""

    def test_example_plugin_init(self):
        """測試範例外掛初始化"""
        from paddleocr_toolkit.plugins.example_plugin import ResultStatsPlugin

        plugin = ResultStatsPlugin()
        assert plugin is not None

    def test_example_plugin_name(self):
        """測試外掛名稱"""
        from paddleocr_toolkit.plugins.example_plugin import ResultStatsPlugin

        plugin = ResultStatsPlugin()
        assert plugin.name == "ResultStats"

    def test_example_plugin_version(self):
        """測試外掛版本"""
        from paddleocr_toolkit.plugins.example_plugin import ResultStatsPlugin

        plugin = ResultStatsPlugin()
        assert plugin.version == "1.0.0"

    def test_example_plugin_enabled(self):
        """測試外掛啟用狀態"""
        from paddleocr_toolkit.plugins.example_plugin import ResultStatsPlugin

        plugin = ResultStatsPlugin()
        assert plugin.enabled is True

    def test_example_plugin_initialize(self):
        """測試外掛初始化方法"""
        from paddleocr_toolkit.plugins.example_plugin import ResultStatsPlugin

        plugin = ResultStatsPlugin()
        result = plugin.initialize()
        assert result is True

    def test_example_plugin_enable(self):
        """測試啟用外掛"""
        from paddleocr_toolkit.plugins.example_plugin import ResultStatsPlugin

        plugin = ResultStatsPlugin()
        plugin.disable()
        plugin.enable()
        assert plugin.enabled is True

    def test_example_plugin_disable(self):
        """測試停用外掛"""
        from paddleocr_toolkit.plugins.example_plugin import ResultStatsPlugin

        plugin = ResultStatsPlugin()
        plugin.disable()
        assert plugin.enabled is False

    def test_example_plugin_get_info(self):
        """測試獲取外掛資訊"""
        from paddleocr_toolkit.plugins.example_plugin import ResultStatsPlugin

        plugin = ResultStatsPlugin()
        info = plugin.get_info()
        assert isinstance(info, dict)
        assert "name" in info
        assert "version" in info


class TestPluginHooks:
    """測試外掛鉤子"""

    def test_on_before_ocr(self):
        """測試 OCR 前處理鉤子"""
        from paddleocr_toolkit.plugins.example_plugin import ResultStatsPlugin

        plugin = ResultStatsPlugin()
        # 預設應該返回輸入的圖片不變
        result = plugin.on_before_ocr("test_image")
        assert result == "test_image"

    def test_on_after_ocr(self):
        """測試 OCR 後處理鉤子"""
        from paddleocr_toolkit.plugins.example_plugin import ResultStatsPlugin

        plugin = ResultStatsPlugin()
        # 傳入模擬結果
        test_result = [{"text": "Hello", "confidence": 0.95}]
        result = plugin.on_after_ocr(test_result)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
