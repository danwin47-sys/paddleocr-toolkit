# -*- coding: utf-8 -*-
"""
TranslationProcessor 測試 (更新版)
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from paddleocr_toolkit.core.models import OCRResult
from paddleocr_toolkit.processors.translation_processor import (
    EnhancedTranslationProcessor as TranslationProcessor,
)


class TestTranslationProcessor:
    """測試翻譯處理器"""

    def test_init(self):
        """測試初始化"""
        processor = TranslationProcessor()
        assert processor.translator is None
        assert processor.renderer is None

    @patch("paddleocr_toolkit.processors.translation_processor.fitz")
    @patch("pdf_translator.OllamaTranslator", create=True)
    @patch("pdf_translator.TextRenderer", create=True)
    @patch("pdf_translator.MonolingualPDFGenerator", create=True)
    @patch("pdf_translator.BilingualPDFGenerator", create=True)
    def test_setup_translation_tools(
        self, mock_bi_gen, mock_mono_gen, mock_renderer, mock_translator, mock_fitz
    ):
        """測試工具設定"""
        processor = TranslationProcessor()

        mock_pdf = Mock()
        mock_fitz.open.return_value = mock_pdf

        config = {
            "ollama_model": "qwen",
            "ollama_url": "url",
            "no_mono": False,
            "no_dual": False,
            "dual_mode": "alternating",
            "target_lang": "en",
        }

        with patch("os.path.exists", return_value=True):
            setup = processor.setup_translation_tools("test_erased.pdf", config)

            assert setup is not None
            assert len(setup) == 8
            assert processor.translator is not None
            assert processor.renderer is not None

    def test_translate_page_texts(self):
        """測試頁面文字翻譯"""
        processor = TranslationProcessor()

        mock_translator = Mock()
        mock_translator.translate_batch.return_value = ["你好", "世界"]

        results = [
            OCRResult(text="Hello", confidence=0.9, bbox=[[0, 0]]),
            OCRResult(text="World", confidence=0.9, bbox=[[0, 50]]),
        ]

        with patch("pdf_translator.TranslatedBlock", create=True) as mock_block_class:
            mock_block_class.side_effect = lambda **kwargs: kwargs

            blocks = processor.translate_page_texts(
                results, mock_translator, "en", "zh", 0
            )

            assert len(blocks) == 2
            assert blocks[0]["translated_text"] == "你好"
            assert blocks[1]["translated_text"] == "世界"

    @patch("paddleocr_toolkit.processors.translation_processor.fitz")
    def test_render_translations_to_pdf(self, mock_fitz):
        """測試翻譯渲染到 PDF"""
        processor = TranslationProcessor()

        mock_pdf = [Mock()]
        mock_pdf[0].get_pixmap.return_value = Mock()

        mock_renderer = Mock()
        mock_mono_gen = Mock()

        with patch(
            "paddleocr_toolkit.core.pdf_utils.pixmap_to_numpy", return_value=None
        ):
            processor._render_translations_to_pdf(
                0,
                [{"text": "t"}],
                mock_pdf,
                None,
                mock_renderer,
                mock_mono_gen,
                None,
                150,
            )

            mock_renderer.render_multiple_texts.assert_called_once()
            mock_mono_gen.add_page.assert_called_once()

    def test_save_translation_pdfs(self):
        """測試儲存 PDF"""
        processor = TranslationProcessor()

        mock_mono = Mock()
        summary = {}

        processor._save_translation_pdfs(mock_mono, None, "mono.pdf", None, summary)

        mock_mono.save.assert_called_once_with("mono.pdf")
        assert summary["translated_pdf"] == "mono.pdf"
