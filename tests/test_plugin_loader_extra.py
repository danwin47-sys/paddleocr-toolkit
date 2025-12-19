# -*- coding: utf-8 -*-
"""
外掛載入器額外測試
測試 paddleocr_toolkit/plugins/loader.py
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestPluginLoaderInit:
    """測試外掛載入器初始化"""

    def test_import_plugin_loader(self):
        """測試匯入外掛載入器"""
        from paddleocr_toolkit.plugins.loader import PluginLoader

        assert PluginLoader is not None

    def test_plugin_loader_init(self):
        """測試外掛載入器初始化"""
        from paddleocr_toolkit.plugins.loader import PluginLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PluginLoader(tmpdir)
            assert loader is not None
            assert loader.plugin_dir == Path(tmpdir)

    def test_plugin_loader_empty_plugins(self):
        """測試空外掛字典"""
        from paddleocr_toolkit.plugins.loader import PluginLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PluginLoader(tmpdir)
            assert loader.plugins == {}


class TestPluginLoaderDiscovery:
    """測試外掛發現"""

    def test_discover_plugins_empty_dir(self):
        """測試空目錄發現外掛"""
        from paddleocr_toolkit.plugins.loader import PluginLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PluginLoader(tmpdir)
            plugins = loader.discover_plugins()
            assert isinstance(plugins, list)

    def test_discover_plugins_nonexistent_dir(self):
        """測試不存在的目錄"""
        from paddleocr_toolkit.plugins.loader import PluginLoader

        loader = PluginLoader("/nonexistent/path")
        plugins = loader.discover_plugins()
        assert plugins == []


class TestPluginLoaderManagement:
    """測試外掛管理"""

    def test_get_plugin_nonexistent(self):
        """測試獲取不存在的外掛"""
        from paddleocr_toolkit.plugins.loader import PluginLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PluginLoader(tmpdir)
            plugin = loader.get_plugin("nonexistent")
            assert plugin is None

    def test_get_all_plugins_empty(self):
        """測試獲取所有外掛（空）"""
        from paddleocr_toolkit.plugins.loader import PluginLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PluginLoader(tmpdir)
            plugins = loader.get_all_plugins()
            assert isinstance(plugins, dict)

    def test_enable_plugin_nonexistent(self):
        """測試啟用不存在的外掛"""
        from paddleocr_toolkit.plugins.loader import PluginLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PluginLoader(tmpdir)
            result = loader.enable_plugin("nonexistent")
            assert result is False

    def test_disable_plugin_nonexistent(self):
        """測試停用不存在的外掛"""
        from paddleocr_toolkit.plugins.loader import PluginLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PluginLoader(tmpdir)
            result = loader.disable_plugin("nonexistent")
            assert result is False

    def test_unload_plugin_nonexistent(self):
        """測試解除安裝不存在的外掛"""
        from paddleocr_toolkit.plugins.loader import PluginLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PluginLoader(tmpdir)
            result = loader.unload_plugin("nonexistent")
            assert result is False

    def test_list_plugins_empty(self):
        """測試列出外掛（空）"""
        from paddleocr_toolkit.plugins.loader import PluginLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PluginLoader(tmpdir)
            plugins = loader.list_plugins()
            assert plugins == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
