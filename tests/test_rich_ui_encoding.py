#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試Rich UI在Windows下的編碼支援
"""

import sys

import pytest

# 必須先匯入rich_ui才能測試
from paddleocr_toolkit.cli import rich_ui


def test_icons_defined():
    """測試圖示字典已定義"""
    assert hasattr(rich_ui, "ICONS")
    assert "success" in rich_ui.ICONS
    assert "error" in rich_ui.ICONS
    assert "warning" in rich_ui.ICONS
    assert "info" in rich_ui.ICONS


def test_windows_ascii_icons():
    """測試Windows下使用ASCII圖示"""
    if sys.platform == "win32":
        assert rich_ui.ICONS["success"] == "[OK]"
        assert rich_ui.ICONS["error"] == "[X]"
        assert rich_ui.ICONS["warning"] == "[!]"
    else:
        # Unix/Mac使用Emoji
        assert rich_ui.ICONS["success"] in ["✅", "[OK]"]


def test_print_functions_no_crash(capsys):
    """測試print函式不會崩潰"""
    try:
        rich_ui.print_success("測試成功")
        rich_ui.print_error("測試錯誤")
        rich_ui.print_warning("測試警告")
        rich_ui.print_info("測試資訊")
        captured = capsys.readouterr()
        success = True
    except UnicodeEncodeError:
        success = False
    
    assert success, "print函式出現編碼錯誤"


def test_utf8_output_enabled():
    """測試UTF-8輸出已啟用"""
    if sys.platform == "win32":
        # Windows 下應該已經設定為 UTF-8
        assert sys.stdout.encoding.lower() in ["utf-8", "utf8"]


def test_banner_display(capsys):
    """測試banner顯示"""
    try:
        rich_ui.print_banner()
        captured = capsys.readouterr()
        # 應該包含某些內容
        assert len(captured.out) > 0 or rich_ui.HAS_RICH
        success = True
    except UnicodeEncodeError:
        success = False

    assert success, "banner顯示出現編碼錯誤"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
