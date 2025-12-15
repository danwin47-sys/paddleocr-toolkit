#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试CLI命令
"""

import shutil
import tempfile
from pathlib import Path

import pytest


def test_init_command():
    """测试init命令"""
    from paddleocr_toolkit.cli.commands.init import (
        create_config_file,
        create_project_structure,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # 测试创建结构
        create_project_structure(tmppath)

        assert (tmppath / "input").exists()
        assert (tmppath / "output").exists()
        assert (tmppath / "config").exists()
        assert (tmppath / "logs").exists()

        # 测试创建配置
        create_config_file(tmppath)
        assert (tmppath / "config" / "default.yaml").exists()


def test_validate_edit_distance():
    """测试编辑距离计算"""
    from paddleocr_toolkit.cli.commands.validate import edit_distance

    # 完全相同
    assert edit_distance("hello", "hello") == 0

    # 一个字符差异
    assert edit_distance("hello", "hallo") == 1

    # 插入
    assert edit_distance("hello", "helllo") == 1

    # 删除
    assert edit_distance("hello", "helo") == 1


def test_validate_accuracy():
    """测试准确率计算"""
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
