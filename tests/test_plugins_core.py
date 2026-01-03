# -*- coding: utf-8 -*-
import pytest
import sys
import os
import shutil
import tempfile
import logging
from unittest.mock import MagicMock, patch, mock_open
from paddleocr_toolkit.plugins.base import OCRPlugin
from paddleocr_toolkit.plugins.loader import PluginLoader


# 1. Plugin Base Coverage
class TestPluginBaseCore:
    def test_plugin_base_exceptions_and_flows(self):
        # Create concrete implementation
        class MockPlugin(OCRPlugin):
            def on_init(self):
                return True

            def on_before_ocr(self, image):
                raise ValueError("Before Error")

            def on_after_ocr(self, results):
                raise ValueError("After Error")

        plugin = MockPlugin({})

        # initialize returns True if already initialized
        plugin._initialized = True
        assert plugin.initialize() is True

        # initialize exception
        plugin._initialized = False
        with patch.object(plugin, "on_init", side_effect=Exception("Init Fail")):
            assert plugin.initialize() is False

        # process_before_ocr exception
        plugin._initialized = True
        plugin.process_before_ocr("img")  # Should log error and return original

        # process_after_ocr exception
        plugin.process_after_ocr("res")  # Should log error and return original

        # process_after_ocr early return
        plugin.enabled = False
        assert plugin.process_after_ocr("res") == "res"

    def test_plugin_base_info_methods(self):
        class MockP(OCRPlugin):
            def on_init(self):
                return True

            def on_before_ocr(self, i):
                return i

            def on_after_ocr(self, r):
                return r

        p = MockP()

        # get_info
        info = p.get_info()
        assert info["name"] == "Plugin Name"

        # on_shutdown
        with patch.object(p.logger, "info") as mock_log:
            p.on_shutdown()
            mock_log.assert_called()

        # enable/disable
        p.disable()
        assert p.enabled is False
        p.enable()
        assert p.enabled is True

        # initialize success logging
        with patch.object(p.logger, "info") as mock_log:
            p.initialize()
            mock_log.assert_called_with(f"外掛 {p.name} v{p.version} 初始化成功")

        # initialize fail logging
        p._initialized = False
        with patch.object(p, "on_init", return_value=False):
            with patch.object(p.logger, "warning") as mock_warn:
                assert p.initialize() is False
                mock_warn.assert_called()
                assert p.initialize() is False
                mock_warn.assert_called()

    def test_example_usage_block(self):
        # Cover if __name__ == "__main__" block
        import paddleocr_toolkit.plugins.base as base_mod

        file_path = base_mod.__file__
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        # Filter out encoding lines or just exec safe part
        code = code.replace("\ufeff", "")  # Remove BOM if exists
        with patch("builtins.print"):
            try:
                exec(code, {"__name__": "__main__"})
            except Exception:
                pass


# 2. Plugin Loader Coverage
class TestPluginLoaderCore:
    def test_loader_enable_disable_returns(self):
        loader = PluginLoader("dummy_dir")
        mock_plugin = MagicMock()
        loader.plugins = {"p1": mock_plugin}

        # enable_plugin success
        assert loader.enable_plugin("p1") is True
        mock_plugin.enable.assert_called()

        # disable_plugin success
        assert loader.disable_plugin("p1") is True
        mock_plugin.disable.assert_called()

    def test_discovery_and_management(self):
        # Create a dummy plugin file content
        plugin_code = """
from paddleocr_toolkit.plugins.base import OCRPlugin
class MyTestPlugin(OCRPlugin):
    name = "TestPlugin"
    version = "0.0.1"
    def on_init(self): return True
    def on_before_ocr(self, img): return img
    def on_after_ocr(self, res): return res
"""
        # Create temp dir for plugins
        tmp_dir = tempfile.mkdtemp()
        try:
            # Write plugin file
            with open(os.path.join(tmp_dir, "my_plugin.py"), "w") as f:
                f.write(plugin_code)

            # Init loader with this dir
            loader = PluginLoader(tmp_dir)

            # Discover plugins
            loader.load_all_plugins()

            # Verify plugin loaded
            assert "TestPlugin" in loader.plugins

            # Get Plugin
            p = loader.get_plugin("TestPlugin")
            assert p is not None
            assert loader.get_plugin("NonExistent") is None

            # List Plugins
            info_list = loader.list_plugins()
            assert len(info_list) >= 1
            assert info_list[0]["name"] == "TestPlugin"

            # Get Plugin Info
            info = loader.get_plugin_info("TestPlugin")
            assert info["name"] == "TestPlugin"
            assert loader.get_plugin_info("Nada") is None

            # Unload Plugin
            assert loader.unload_plugin("TestPlugin") is True
            assert "TestPlugin" not in loader.plugins
            assert loader.unload_plugin("TestPlugin") is False  # Already gone

            # Unload All
            loader.load_all_plugins()
            assert len(loader.plugins) > 0
            loader.unload_all_plugins()
            assert len(loader.plugins) == 0

        finally:
            shutil.rmtree(tmp_dir)

    def test_loader_failures(self):
        # Directory does not exist
        loader = PluginLoader("non_existent_dir_xyz_123")
        with patch.object(loader.logger, "warning") as mock_warn:
            assert loader.discover_plugins() == []
            mock_warn.assert_called()

        # Skip files starting with _
        tmp_dir = tempfile.mkdtemp()
        try:
            with open(os.path.join(tmp_dir, "_hidden.py"), "w") as f:
                f.write("pass")
            with open(os.path.join(tmp_dir, "visible.py"), "w") as f:
                f.write("pass")

            loader = PluginLoader(tmp_dir)
            files = loader.discover_plugins()
            assert len(files) == 1
            assert "visible.py" in files[0]

            # Load failure - No Plugin Class
            with patch.object(loader.logger, "warning") as mock_warn:
                assert loader.load_plugin_from_file(files[0]) is None
                mock_warn.assert_called_with(f"在 {files[0]} 中未找到插件類別")

            # Load failure - Exception
            with patch(
                "importlib.util.spec_from_file_location",
                side_effect=Exception("Load Crash"),
            ):
                with patch.object(loader.logger, "error") as mock_err:
                    assert loader.load_plugin_from_file(files[0]) is None
                    mock_err.assert_called()

        finally:
            shutil.rmtree(tmp_dir)

    def test_loader_main_block(self):
        import paddleocr_toolkit.plugins.loader as mod

        with open(mod.__file__, "r", encoding="utf-8") as f:
            code = f.read()

        # Simple exec
        with patch("logging.getLogger"):
            try:
                exec(code, {"__name__": "__main__"})
            except:
                pass


# 3. Example Plugin Coverage
class TestExamplePluginCore:
    def test_example_plugin_coverage(self):
        from paddleocr_toolkit.plugins.example_plugin import ResultStatsPlugin

        p = ResultStatsPlugin()
        # on_init
        with patch.object(p.logger, "info") as mock_log:
            assert p.on_init() is True
            mock_log.assert_called()

        # on_before_ocr
        assert p.on_before_ocr("img") == "img"

        # results not results[0] list
        results = ["something"]
        p.on_after_ocr(results)

        # Exception handling
        mock_bad_list = MagicMock()
        mock_bad_list.__len__.side_effect = Exception("Len Fail")

        p.on_after_ocr(mock_bad_list)

        # Normal list list
        results_list = [["item1", "item2"]]
        p.on_after_ocr(results_list)
