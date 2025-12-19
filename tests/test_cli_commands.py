#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試CLI命令
"""

import shutil
import tempfile
from pathlib import Path

import pytest


def test_init_command():
    """測試init命令"""
    from paddleocr_toolkit.cli.commands.init import (
        create_config_file,
        create_project_structure,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # 測試建立結構
        create_project_structure(tmppath)

        assert (tmppath / "input").exists()
        assert (tmppath / "output").exists()
        assert (tmppath / "config").exists()
        assert (tmppath / "logs").exists()

        # 測試建立配置
        create_config_file(tmppath)
        assert (tmppath / "config" / "default.yaml").exists()


def test_validate_edit_distance():
    """測試編輯距離計算"""
    from paddleocr_toolkit.cli.commands.validate import edit_distance

    # 完全相同
    assert edit_distance("hello", "hello") == 0

    # 一個字元差異
    assert edit_distance("hello", "hallo") == 1

    # 插入
    assert edit_distance("hello", "helllo") == 1

    # 刪除
    assert edit_distance("hello", "helo") == 1


def test_validate_accuracy():
    """測試準確率計算"""
    from paddleocr_toolkit.cli.commands.validate import calculate_character_accuracy

    # 完全匹配
    acc = calculate_character_accuracy("hello world", "hello world")
    assert acc == 1.0

    # 部分匹配
    acc = calculate_character_accuracy("hello world", "hallo world")
    assert 0.9 < acc < 1.0

    # 完全不同
    acc = calculate_character_accuracy("abc", "xyz")
    assert acc < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
