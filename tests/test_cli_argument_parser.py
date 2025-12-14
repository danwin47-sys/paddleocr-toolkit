# -*- coding: utf-8 -*-
"""
Tests for CLI argument parser
"""

import argparse

import pytest

from paddleocr_toolkit.cli.argument_parser import create_argument_parser


class TestCreateArgumentParser:
    """Test create_argument_parser function"""

    def test_creates_parser(self):
        """Test parser creation"""
        parser = create_argument_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_has_input_argument(self):
        """Test input argument"""
        parser = create_argument_parser()
        args = parser.parse_args(["test.pdf"])
        assert args.input == "test.pdf"

    def test_default_mode(self):
        """Test default mode"""
        parser = create_argument_parser()
        args = parser.parse_args(["test.pdf"])
        assert args.mode == "basic"

    def test_mode_choices(self):
        """Test mode options"""
        parser = create_argument_parser()
        for mode in ["basic", "structure", "vl", "formula", "hybrid"]:
            args = parser.parse_args(["test.pdf", "--mode", mode])
            assert args.mode == mode

    def test_searchable_default(self):
        """Test searchable default value"""
        parser = create_argument_parser()
        args = parser.parse_args(["test.pdf"])
        assert args.searchable is True

    def test_output_option(self):
        """Test output option"""
        parser = create_argument_parser()
        args = parser.parse_args(["test.pdf", "--output", "output.pdf"])
        assert args.output == "output.pdf"

    def test_text_output_default(self):
        """Test text output default"""
        parser = create_argument_parser()
        args = parser.parse_args(["test.pdf"])
        assert args.text_output == "AUTO"

    def test_markdown_output(self):
        """Test markdown output"""
        parser = create_argument_parser()
        args = parser.parse_args(["test.pdf", "--markdown-output"])
        assert args.markdown_output == "AUTO"

    def test_json_output(self):
        """Test JSON output"""
        parser = create_argument_parser()
        args = parser.parse_args(["test.pdf", "--json-output", "data.json"])
        assert args.json_output == "data.json"

    def test_all_flag(self):
        """Test all flag"""
        parser = create_argument_parser()
        args = parser.parse_args(["test.pdf", "--all"])
        assert args.all is True

    def test_dpi_default(self):
        """Test DPI default value"""
        parser = create_argument_parser()
        args = parser.parse_args(["test.pdf"])
        assert args.dpi == 150

    def test_dpi_custom(self):
        """Test custom DPI"""
        parser = create_argument_parser()
        args = parser.parse_args(["test.pdf", "--dpi", "300"])
        assert args.dpi == 300

    def test_device_default(self):
        """Test device default"""
        parser = create_argument_parser()
        args = parser.parse_args(["test.pdf"])
        assert args.device == "cpu"

    def test_recursive_flag(self):
        """Test recursive flag"""
        parser = create_argument_parser()
        args = parser.parse_args(["test_dir", "--recursive"])
        assert args.recursive is True

    def test_verbose_flag(self):
        """Test verbose flag"""
        parser = create_argument_parser()
        args = parser.parse_args(["test.pdf", "--verbose"])
        assert args.verbose is True


class TestTranslationArguments:
    """Test translation arguments"""

    def test_translate_flag(self):
        """Test translate flag"""
        parser = create_argument_parser()
        args = parser.parse_args(["test.pdf", "--translate"])
        assert args.translate is True

    def test_source_lang_default(self):
        """Test source language default"""
        parser = create_argument_parser()
        args = parser.parse_args(["test.pdf"])
        assert args.source_lang == "auto"

    def test_target_lang_default(self):
        """Test target language default"""
        parser = create_argument_parser()
        args = parser.parse_args(["test.pdf"])
        assert args.target_lang == "en"

    def test_ollama_model_default(self):
        """Test Ollama model default"""
        parser = create_argument_parser()
        args = parser.parse_args(["test.pdf"])
        assert args.ollama_model == "qwen2.5:7b"
