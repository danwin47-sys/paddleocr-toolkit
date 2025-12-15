# -*- coding: utf-8 -*-
"""
測試 CLI 設定檔處理器
"""

import argparse
from pathlib import Path

import pytest

from paddleocr_toolkit.cli.config_handler import (_process_all_flag,
                                                  _process_no_flags,
                                                  load_and_merge_config,
                                                  load_config_file,
                                                  process_args_overrides)


class TestLoadAndMergeConfig:
    """測試 load_and_merge_config 函數"""

    def test_basic_merge(self):
        """測試基本的參數合併"""
        # 創建測試參數
        args = argparse.Namespace(input="test.pdf", mode="basic", searchable=True)

        # 測試合併
        config = load_and_merge_config(args)

        # 驗證
        assert isinstance(config, dict)
        assert config["input"] == "test.pdf"
        assert config["mode"] == "basic"
        assert config["searchable"] is True

    def test_with_none_config_path(self):
        """測試 config_path 為 None 時的行為"""
        args = argparse.Namespace(input="test.pdf")
        config = load_and_merge_config(args, config_path=None)

        assert isinstance(config, dict)
        assert config["input"] == "test.pdf"

    def test_preserves_all_args(self):
        """測試保留所有參數"""
        args = argparse.Namespace(
            input="test.pdf", mode="structure", dpi=200, device="cpu", verbose=True
        )

        config = load_and_merge_config(args)

        assert config["input"] == "test.pdf"
        assert config["mode"] == "structure"
        assert config["dpi"] == 200
        assert config["device"] == "cpu"
        assert config["verbose"] is True


class TestLoadConfigFile:
    """測試 load_config_file 函數"""

    def test_returns_empty_dict(self):
        """測試返回空字典（功能未實作）"""
        result = load_config_file("nonexistent.yaml")
        assert isinstance(result, dict)
        assert len(result) == 0


class TestProcessArgsOverrides:
    """測試 process_args_overrides 函數"""

    def test_no_overrides(self):
        """測試無覆蓋選項時"""
        args = argparse.Namespace(
            searchable=True,
            text_output="AUTO",
            markdown_output="AUTO",
            json_output="AUTO",
            no_searchable=False,
            no_text_output=False,
            no_markdown_output=False,
            no_json_output=False,
        )

        result = process_args_overrides(args)

        assert result.searchable is True
        assert result.text_output == "AUTO"
        assert result.markdown_output == "AUTO"
        assert result.json_output == "AUTO"

    def test_with_no_searchable(self):
        """測試 --no-searchable 覆蓋"""
        args = argparse.Namespace(
            searchable=True,
            no_searchable=True,
            no_text_output=False,
            no_markdown_output=False,
            no_json_output=False,
        )

        result = process_args_overrides(args)

        assert result.searchable is False

    def test_with_all_flag_structure_mode(self):
        """測試 --all 參數在 structure 模式"""
        args = argparse.Namespace(
            mode="structure",
            all=True,
            markdown_output=None,
            json_output=None,
            html_output=None,
            no_searchable=False,
            no_text_output=False,
            no_markdown_output=False,
            no_json_output=False,
        )

        result = process_args_overrides(args)

        assert result.markdown_output == "AUTO"
        assert result.json_output == "AUTO"
        assert result.html_output == "AUTO"

    def test_with_all_flag_basic_mode(self):
        """測試 --all 參數在 basic 模式（不應啟用）"""
        args = argparse.Namespace(
            mode="basic",
            all=True,
            markdown_output=None,
            json_output=None,
            html_output=None,
            no_searchable=False,
            no_text_output=False,
            no_markdown_output=False,
            no_json_output=False,
        )

        result = process_args_overrides(args)

        # basic 模式下 --all 不應啟用這些輸出
        assert result.markdown_output is None
        assert result.json_output is None
        assert result.html_output is None


class TestProcessNoFlags:
    """測試 _process_no_flags 函數"""

    def test_all_no_flags(self):
        """測試所有 --no-* 選項"""
        args = argparse.Namespace(
            searchable=True,
            text_output="AUTO",
            markdown_output="AUTO",
            json_output="AUTO",
            no_searchable=True,
            no_text_output=True,
            no_markdown_output=True,
            no_json_output=True,
        )

        result = _process_no_flags(args)

        assert result.searchable is False
        assert result.text_output is None
        assert result.markdown_output is None
        assert result.json_output is None

    def test_partial_no_flags(self):
        """測試部分 --no-* 選項"""
        args = argparse.Namespace(
            searchable=True,
            text_output="AUTO",
            markdown_output="AUTO",
            json_output="AUTO",
            no_searchable=False,
            no_text_output=True,
            no_markdown_output=False,
            no_json_output=True,
        )

        result = _process_no_flags(args)

        assert result.searchable is True
        assert result.text_output is None
        assert result.markdown_output == "AUTO"
        assert result.json_output is None


class TestProcessAllFlag:
    """測試 _process_all_flag 函數"""

    def test_all_flag_enabled_structure(self):
        """測試 --all 在 structure 模式啟用"""
        args = argparse.Namespace(
            mode="structure",
            all=True,
            markdown_output=None,
            json_output=None,
            html_output=None,
        )

        result = _process_all_flag(args)

        assert result.markdown_output == "AUTO"
        assert result.json_output == "AUTO"
        assert result.html_output == "AUTO"

    def test_all_flag_enabled_vl(self):
        """測試 --all 在 vl 模式啟用"""
        args = argparse.Namespace(
            mode="vl",
            all=True,
            markdown_output=None,
            json_output=None,
            html_output=None,
        )

        result = _process_all_flag(args)

        assert result.markdown_output == "AUTO"
        assert result.json_output == "AUTO"
        assert result.html_output == "AUTO"

    def test_all_flag_enabled_hybrid(self):
        """測試 --all 在 hybrid 模式啟用"""
        args = argparse.Namespace(
            mode="hybrid",
            all=True,
            markdown_output=None,
            json_output=None,
            html_output=None,
        )

        result = _process_all_flag(args)

        assert result.markdown_output == "AUTO"
        assert result.json_output == "AUTO"
        assert result.html_output == "AUTO"

    def test_all_flag_disabled(self):
        """測試 --all 未啟用"""
        args = argparse.Namespace(
            mode="structure",
            all=False,
            markdown_output=None,
            json_output=None,
            html_output=None,
        )

        result = _process_all_flag(args)

        assert result.markdown_output is None
        assert result.json_output is None
        assert result.html_output is None

    def test_all_flag_preserves_existing(self):
        """測試 --all 保留現有值"""
        args = argparse.Namespace(
            mode="structure",
            all=True,
            markdown_output="custom.md",
            json_output=None,
            html_output=None,
        )

        result = _process_all_flag(args)

        assert result.markdown_output == "custom.md"  # 保留原值
        assert result.json_output == "AUTO"
        assert result.html_output == "AUTO"
