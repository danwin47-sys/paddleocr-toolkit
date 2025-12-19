# -*- coding: utf-8 -*-
"""
OutputManager 測試
"""

import json
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
