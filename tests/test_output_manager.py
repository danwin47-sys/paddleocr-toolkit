# -*- coding: utf-8 -*-
"""
OutputManager 測試
"""

import json
import sys
import builtins
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from paddleocr_toolkit.outputs.output_manager import OutputManager


class TestOutputManager:
    """測試輸出管理器"""

    def test_init_basic(self):
        """測試基本初始化"""
        manager = OutputManager(base_path="output/result")

        assert manager.base_path == Path("output/result")
        assert len(manager.formats) == 0

    def test_init_with_formats(self):
        """測試帶格式的初始化"""
        manager = OutputManager(
            base_path="output/result", formats=["md", "json", "txt"]
        )

        assert "md" in manager.formats
        assert "json" in manager.formats
        assert "txt" in manager.formats

    def test_add_format(self):
        """測試新增格式"""
        manager = OutputManager(base_path="output/result")

        manager.add_format("html")
        assert "html" in manager.formats

        manager.add_format("HTML")  # 測試大小寫
        assert "html" in manager.formats

    def test_remove_format(self):
        """測試移除格式"""
        manager = OutputManager(base_path="output/result", formats=["md", "json"])

        manager.remove_format("md")
        assert "md" not in manager.formats
        assert "json" in manager.formats

    @patch("builtins.open", new_callable=mock_open)
    def test_write_markdown(self, mock_file):
        """測試寫入Markdown"""
        manager = OutputManager(base_path="output/result")

        path = manager.write_markdown("# Title\nContent")

        assert str(Path(path)) == str(Path("output/result.md"))
        mock_file.assert_called()

    @patch("builtins.open", new_callable=mock_open)
    def test_write_json(self, mock_file):
        """測試寫入JSON"""
        manager = OutputManager(base_path="output/result")

        data = {"key": "value", "number": 123}
        path = manager.write_json(data)

        assert str(Path(path)) == str(Path("output/result.json"))
        mock_file.assert_called()

    @patch("builtins.open", new_callable=mock_open)
    def test_write_text(self, mock_file):
        """測試寫入文字"""
        manager = OutputManager(base_path="output/result")

        path = manager.write_text("Plain text content")

        assert str(Path(path)) == str(Path("output/result.txt"))
        mock_file.assert_called()

    @patch("builtins.open", new_callable=mock_open)
    def test_write_html(self, mock_file):
        """測試寫入HTML"""
        manager = OutputManager(base_path="output/result")

        path = manager.write_html("Content", title="Test Page")

        assert str(Path(path)) == str(Path("output/result.html"))
        mock_file.assert_called()

    @patch("builtins.open", new_callable=mock_open)
    def test_write_all(self, mock_file):
        """測試批次寫入"""
        manager = OutputManager(
            base_path="output/result", formats=["md", "json", "txt"]
        )

        content_dict = {
            "text": "Plain text",
            "markdown": "# Title",
            "json_data": {"key": "value"},
        }

        paths = manager.write_all(content_dict)

        assert "markdown" in paths
        assert "json" in paths
        assert "text" in paths

    def test_get_output_path(self):
        """測試獲取輸出路徑"""
        manager = OutputManager(base_path="output/result")

        assert str(Path(manager.get_output_path("md"))) == str(Path("output/result.md"))
        assert str(Path(manager.get_output_path("json"))) == str(
            Path("output/result.json")
        )

    def test_context_manager(self):
        """測試Context Manager"""
        with OutputManager(base_path="output/result") as manager:
            assert isinstance(manager, OutputManager)

        # 驗證退出後清理完成
        assert len(manager.writers) == 0

    @patch("builtins.open", new_callable=mock_open)
    def test_write_markdown_custom_path(self, mock_file):
        """測試自定義路徑寫入"""
        manager = OutputManager(base_path="output/result")

        path = manager.write_markdown("Content", output_path="custom/path.md")

        assert path == "custom/path.md"

    @patch("builtins.open", new_callable=mock_open)
    def test_write_json_with_indent(self, mock_file):
        """測試JSON縮排"""
        manager = OutputManager(base_path="output/result")

        data = {"key": "value"}
        manager.write_json(data, indent=4)

        mock_file.assert_called()


class TestOutputManagerAdvanced:
    """進階 OutputManager 測試 (Mocking & Edge Cases)"""

    def test_import_fallback(self):
        # Cover lines 21-22 (ImportError for BufferedJSONWriter)
        # We need to reload output_manager with mocked imports
        import importlib

        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "paddleocr_toolkit.core.buffered_writer":
                raise ImportError("No Buffer")
            return real_import(name, *args, **kwargs)

        if "paddleocr_toolkit.outputs.output_manager" in sys.modules:
            del sys.modules["paddleocr_toolkit.outputs.output_manager"]

        with patch("builtins.__import__", side_effect=mock_import):
            import paddleocr_toolkit.outputs.output_manager as om

            assert om.HAS_BUFFERED is False

        # Restore module
        if "paddleocr_toolkit.outputs.output_manager" in sys.modules:
            del sys.modules["paddleocr_toolkit.outputs.output_manager"]
        importlib.import_module("paddleocr_toolkit.outputs.output_manager")

    def test_buffered_writer_usage(self):
        # Cover lines 111-113 (use_buffered=True branch)
        # Ensure module is loaded fresh or correctly
        if "paddleocr_toolkit.outputs.output_manager" not in sys.modules:
            import paddleocr_toolkit.outputs.output_manager

        from paddleocr_toolkit.outputs.output_manager import OutputManager

        # Trigger use_buffered=True and data is list
        # We need to mock BufferedJSONWriter
        with patch(
            "paddleocr_toolkit.outputs.output_manager.BufferedJSONWriter"
        ) as MockWriter:
            mock_instance = MockWriter.return_value
            mock_instance.__enter__.return_value = mock_instance

            mgr = OutputManager("test", use_buffered=True)
            # Force switch if HAS_BUFFERED was false
            mgr.use_buffered = True

            data = [1, 2, 3]
            mgr.write_json(data)

            assert mock_instance.write.call_count == 3

    def test_write_all_exceptions(self):
        # Cover lines 216-224: html branch + exception handling in loop
        from paddleocr_toolkit.outputs.output_manager import OutputManager

        mgr = OutputManager("test", formats=["html", "json"])

        # 1. HTML branch (lines 216-221)
        with patch.object(mgr, "write_html") as mock_html:
            mgr.write_all({"html": "<h1>Hi</h1>"})
            mock_html.assert_called()

        # 2. Exception in loop (lines 223-224)
        with patch.object(mgr, "write_json", side_effect=Exception("Write Fail")):
            # Should catch exception and continue/log
            mgr.write_all({"json_data": {}})
