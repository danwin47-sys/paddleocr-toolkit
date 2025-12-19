#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Rich UI在Windows下的编码支持
"""

import sys

import pytest

# 必须先导入rich_ui才能测试
from paddleocr_toolkit.cli import rich_ui


def test_icons_defined():
    """测试图标字典已定义"""
    assert hasattr(rich_ui, "ICONS")
    assert "success" in rich_ui.ICONS
    assert "error" in rich_ui.ICONS
    assert "warning" in rich_ui.ICONS
    assert "info" in rich_ui.ICONS


def test_windows_ascii_icons():
    """测试Windows下使用ASCII图标"""
    if sys.platform == "win32":
        assert rich_ui.ICONS["success"] == "[OK]"
        assert rich_ui.ICONS["error"] == "[X]"
        assert rich_ui.ICONS["warning"] == "[!]"
    else:
        # Unix/Mac使用Emoji
        assert rich_ui.ICONS["success"] in ["✅", "[OK]"]


def test_print_functions_no_crash(capsys):

    assert success, "print函数出现编码错误"


def test_utf8_output_enabled():
    """测试UTF-8输出已启用"""
    if sys.platform == "win32":
        # Windows 下應該已經設定為 UTF-8
        assert sys.stdout.encoding.lower() in ["utf-8", "utf8"]


def test_banner_display(capsys):
    """测试banner显示"""
    try:
        rich_ui.print_banner()
        captured = capsys.readouterr()
        # 应该包含某些内容
        assert len(captured.out) > 0 or rich_ui.HAS_RICH
        success = True
    except UnicodeEncodeError:
        success = False

    assert success, "banner显示出现编码错误"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
