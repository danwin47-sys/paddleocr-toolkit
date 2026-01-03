# -*- coding: utf-8 -*-
"""
Advanced tests for Config Loader to maximize coverage.
"""
import pytest
import argparse
from unittest.mock import MagicMock, patch, mock_open
from paddleocr_toolkit.core.config_loader import (
    load_config,
    save_config,
    apply_config_to_args,
    get_config_value,
    DEFAULT_CONFIG,
)


class TestConfigLoaderAdvanced:
    @patch("paddleocr_toolkit.core.config_loader.HAS_YAML", False)
    def test_no_yaml_load(self):
        """Test load_config when yaml is not installed"""
        config = load_config("config.yaml")
        assert config == DEFAULT_CONFIG

    @patch("paddleocr_toolkit.core.config_loader.HAS_YAML", False)
    def test_no_yaml_save(self):
        """Test save_config when yaml is not installed"""
        success = save_config({}, "config.yaml")
        assert success is False

    def test_load_config_exception(self):
        """Test exception handling during file load"""
        with patch("builtins.open", side_effect=Exception("Read Error")):
            # Should fallback to default config without crashing
            config = load_config("bad.yaml")
            assert config == DEFAULT_CONFIG

    def test_save_config_exception(self):
        """Test exception handling during file save"""
        with patch("builtins.open", side_effect=Exception("Write Error")):
            success = save_config({}, "bad.yaml")
            assert success is False

    def test_apply_config_translation_branches(self):
        """Test apply_config_to_args translation specific branches"""
        config = {
            "translation": {
                "enabled": True,
                "source_lang": "fr",
                "target_lang": "de",
                "ollama_model": "llama3",
                "ollama_url": "http://remote:11434",
            }
        }

        args = argparse.Namespace()
        # Initialize all attributes accessed by apply_config_to_args
        args.mode = None
        args.device = None
        args.dpi = None
        args.no_progress = False
        args.no_compress = False
        args.jpeg_quality = None

        args.translate = False
        args.source_lang = None
        args.target_lang = None
        args.ollama_model = None
        args.ollama_url = None

        apply_config_to_args(config, args)

        assert args.translate is True
        assert args.source_lang == "fr"
        assert args.target_lang == "de"
        assert args.ollama_model == "llama3"
        assert args.ollama_url == "http://remote:11434"

    def test_apply_config_no_override(self):
        """Test that config does NOT override existing args"""
        config = {"ocr": {"mode": "hybrid"}}
        args = argparse.Namespace()
        args._explicit_mode = True  # Mark as explicit
        args._explicit_device = False
        args._explicit_dpi = False
        args._explicit_compress = False
        args._explicit_quality = False

        args.mode = "basic"
        args.device = None
        args.dpi = None
        args.no_progress = False
        args.no_compress = False
        args.jpeg_quality = None

        apply_config_to_args(config, args)

        assert args.mode == "basic"  # Should remain basic

    def test_get_config_value_nested_missing(self):
        """Test get_config_value with missing nested key"""
        val = get_config_value({"a": 1}, "a.b", default="def")
        assert val == "def"

        val2 = get_config_value({"a": {"b": 2}}, "a.c", default="def")
        assert val2 == "def"
