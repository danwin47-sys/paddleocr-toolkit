# -*- coding: utf-8 -*-
"""
OutputManager 测试
"""

import json
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from paddleocr_toolkit.outputs.output_manager import OutputManager


class TestOutputManager:
    """测试输出管理器"""

    def test_init_basic(self):
        """测试基本初始化"""
        manager = OutputManager(base_path="output/result")

        assert manager.base_path == Path("output/result")
        assert len(manager.formats) == 0

    def test_init_with_formats(self):
        """测试带格式的初始化"""
        manager = OutputManager(base_path="output/result", formats=["md", "json", "txt"])

        assert "md" in manager.formats
        assert "json" in manager.formats
        assert "txt" in manager.formats

    def test_add_format(self):
        """测试添加格式"""
        manager = OutputManager(base_path="output/result")

        manager.add_format("html")
        assert "html" in manager.formats

        manager.add_format("HTML")  # 测试大小写
        assert "html" in manager.formats

    def test_remove_format(self):
        """测试移除格式"""
        manager = OutputManager(base_path="output/result", formats=["md", "json"])

        manager.remove_format("md")
        assert "md" not in manager.formats
        assert "json" in manager.formats

    @patch("builtins.open", new_callable=mock_open)
    def test_write_markdown(self, mock_file):
        """测试写入Markdown"""
        manager = OutputManager(base_path="output/result")

        path = manager.write_markdown("# Title\nContent")

        assert str(Path(path)) == str(Path("output/result.md"))
        mock_file.assert_called()

    @patch("builtins.open", new_callable=mock_open)
    def test_write_json(self, mock_file):
        """测试写入JSON"""
        manager = OutputManager(base_path="output/result")

        data = {"key": "value", "number": 123}
        path = manager.write_json(data)

        assert str(Path(path)) == str(Path("output/result.json"))
        mock_file.assert_called()

    @patch("builtins.open", new_callable=mock_open)
    def test_write_text(self, mock_file):
        """测试写入文本"""
        manager = OutputManager(base_path="output/result")

        path = manager.write_text("Plain text content")

        assert str(Path(path)) == str(Path("output/result.txt"))
        mock_file.assert_called()

    @patch("builtins.open", new_callable=mock_open)
    def test_write_html(self, mock_file):
        """测试写入HTML"""
        manager = OutputManager(base_path="output/result")

        path = manager.write_html("Content", title="Test Page")

        assert str(Path(path)) == str(Path("output/result.html"))
        mock_file.assert_called()

    @patch("builtins.open", new_callable=mock_open)
    def test_write_all(self, mock_file):
        """测试批量写入"""
        manager = OutputManager(base_path="output/result", formats=["md", "json", "txt"])

        content_dict = {"text": "Plain text", "markdown": "# Title", "json_data": {"key": "value"}}

        paths = manager.write_all(content_dict)

        assert "markdown" in paths
        assert "json" in paths
        assert "text" in paths

    def test_get_output_path(self):
        """测试获取输出路径"""
        manager = OutputManager(base_path="output/result")

        assert str(Path(manager.get_output_path("md"))) == str(Path("output/result.md"))
        assert str(Path(manager.get_output_path("json"))) == str(Path("output/result.json"))

    def test_context_manager(self):
        """测试Context Manager"""
        with OutputManager(base_path="output/result") as manager:
            assert isinstance(manager, OutputManager)

        # 验证退出后清理完成
        assert len(manager.writers) == 0

    @patch("builtins.open", new_callable=mock_open)
    def test_write_markdown_custom_path(self, mock_file):
        """测试自定义路径写入"""
        manager = OutputManager(base_path="output/result")

        path = manager.write_markdown("Content", output_path="custom/path.md")

        assert path == "custom/path.md"

    @patch("builtins.open", new_callable=mock_open)
    def test_write_json_with_indent(self, mock_file):
        """测试JSON缩进"""
        manager = OutputManager(base_path="output/result")

        data = {"key": "value"}
        manager.write_json(data, indent=4)

        mock_file.assert_called()
