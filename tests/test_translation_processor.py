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

    def test_process_pdf_translation_success(self):
        """測試完整翻譯流程整合"""
        processor = TranslationProcessor()

        # Mock internal methods to avoid complex setup
        processor.setup_translation_tools = Mock()
        mock_pdf_doc = MagicMock()
        mock_pdf_doc.__len__.return_value = 1
        mock_pdf_doc.__iter__.return_value = iter(
            [Mock()]
        )  # Allow iteration over pages

        mock_tools = (
            Mock(),  # translator
            Mock(),  # renderer
            mock_pdf_doc,  # pdf_doc
            Mock(),  # hybrid_doc
            Mock(),  # mono_gen
            Mock(),  # bilingual_gen
            "trans.pdf",
            "bi.pdf",
        )
        processor.setup_translation_tools.return_value = mock_tools

        processor.translate_page_texts = Mock(return_value=["block"])
        processor._render_translations_to_pdf = Mock()
        processor._save_translation_pdfs = Mock()

        # Test Input
        ocr_results = [[OCRResult(text="test", confidence=0.9, bbox=[])]]
        config = {"source_lang": "en", "target_lang": "zh", "ollama_model": "test"}

        result = processor.process_pdf_translation("test.pdf", ocr_results, config)

        assert result.get("translated_pdf") is None  # _save_translation_pdfs mocked
        processor.setup_translation_tools.assert_called_once()
        processor.translate_page_texts.assert_called_once()
        processor._render_translations_to_pdf.assert_called_once()
        processor._save_translation_pdfs.assert_called_once()

    def test_translate_page_texts_empty(self):
        """測試空頁面翻譯"""
        processor = TranslationProcessor()
        results = processor.translate_page_texts([], Mock(), "en", "zh", 0)
        assert results == []

    @patch("paddleocr_toolkit.processors.translation_processor.fitz")
    def test_render_translations_error_handling(self, mock_fitz):
        """測試渲染錯誤處理"""
        processor = TranslationProcessor()

        # 模擬渲染過程拋出例外
        processor._render_translations_to_pdf(
            0, [], Mock(), None, Mock(), Mock(), None, 150
        )
        # 這裡主要是確認不會導致程式崩潰 (Exception 自行捕獲)

    def test_setup_translation_tools_import_error(self):
        """測試匯入錯誤處理"""
        processor = TranslationProcessor()
        # 模擬 pdf_translator 匯入失敗
        with patch.dict("sys.modules", {"pdf_translator": None}):
            result = processor.setup_translation_tools("test.pdf", {})
            assert result is None

    def test_save_translation_pdfs_error(self):
        """測試儲存 PDF 失敗"""
        processor = TranslationProcessor()
        mock_mono = Mock()
        mock_mono.save.side_effect = Exception("Save Error")

        summary = {}
        processor._save_translation_pdfs(mock_mono, None, "out.pdf", None, summary)
        assert "translated_pdf" not in summary  # Should fail to set key


# Added from Ultra Coverage
from paddleocr_toolkit.processors.translation_processor import (
    EnhancedTranslationProcessor,
)
from unittest.mock import MagicMock, patch
import sys


class TestTranslationProcessorAdvanced:
    def test_setup_translation_tools_exception(self):
        processor = EnhancedTranslationProcessor()
        with patch(
            "pdf_translator.OllamaTranslator",
            side_effect=Exception("Generic Setup Error"),
        ):
            result = processor.setup_translation_tools(
                "dummy_erased.pdf", {"ollama_model": "test", "ollama_url": "test"}
            )
            assert result is None

    def test_translate_page_texts_import_error(self):
        processor = EnhancedTranslationProcessor()
        with patch.dict(sys.modules, {"pdf_translator": None}):
            with patch(
                "paddleocr_toolkit.processors.translation_processor.logging"
            ) as mock_log:
                res = processor.translate_page_texts([], MagicMock(), "zh", "en", 0)
                assert res == []

    def test_translate_page_texts_batch_exception(self):
        processor = EnhancedTranslationProcessor()
        mock_translator = MagicMock()
        mock_translator.translate_batch.side_effect = Exception("Batch Error")
        mock_ocr_res = MagicMock()
        mock_ocr_res.text = "hello"
        mock_ocr_res.bbox = [0, 0, 10, 10]
        res = processor.translate_page_texts(
            [mock_ocr_res], mock_translator, "zh", "en", 0
        )
        assert res == []

    def test_render_translations_to_pdf_exception(self):
        processor = EnhancedTranslationProcessor()
        mock_pdf = MagicMock()
        mock_pdf.__getitem__.side_effect = Exception("Render Error")
        processor._render_translations_to_pdf(
            0, [MagicMock()], mock_pdf, None, None, None, None, 150
        )

    def test_translation_processor_missed_lines(self):
        processor = EnhancedTranslationProcessor()
        # 1. if not translation_setup (lines 116-117)
        with patch.object(processor, "setup_translation_tools", return_value=None):
            res = processor.process_pdf_translation("test.pdf", [], {})
            assert "translation_error" in res

        # 2. Page overflow warning (lines 140-141)
        # 3. Overall exception (lines 184-190)
        with patch("fitz.open") as mock_fitz:
            mock_doc = MagicMock()
            mock_doc.__len__.return_value = 2
            mock_page = MagicMock()
            mock_doc.__getitem__.return_value = mock_page
            mock_fitz.return_value = mock_doc
            # setup_translation_tools returns 8-tuple
            setup_val = (
                MagicMock(),
                MagicMock(),
                mock_doc,
                MagicMock(),
                MagicMock(),
                MagicMock(),
                "t.pdf",
                "b.pdf",
            )
            with patch.object(
                processor, "setup_translation_tools", return_value=setup_val
            ):
                # 2. Page overflow warning (lines 140-141)
                res = processor.process_pdf_translation(
                    "test.pdf",
                    ocr_results_per_page=[[MagicMock()]],
                    translate_config={},
                )
                assert res is not None

                # 4. Page level exception (lines 167-170)
                with patch.object(
                    processor,
                    "translate_page_texts",
                    side_effect=[[], Exception("Page error")],
                ):
                    res = processor.process_pdf_translation(
                        "test.pdf",
                        ocr_results_per_page=[[MagicMock()], [MagicMock()]],
                        translate_config={},
                    )
                    assert res is not None

                # 5. Overall exception (lines 184-190)
                with patch.object(
                    processor,
                    "setup_translation_tools",
                    side_effect=Exception("Fatal PDF Error"),
                ):
                    res = processor.process_pdf_translation(
                        "test.pdf", ocr_results_per_page=[], translate_config={}
                    )
                    assert "Fatal PDF Error" in res["translation_error"]


class TestTranslationProcessorDeep:
    def test_save_translation_pdfs_errors(self):
        processor = EnhancedTranslationProcessor()
        mock_gen = MagicMock()
        mock_gen.save.side_effect = Exception("Save Error")
        summary = {}
        processor._save_translation_pdfs(mock_gen, None, "path", None, summary)
        assert "translated_pdf" not in summary
        processor._save_translation_pdfs(None, mock_gen, None, "path", summary)
        assert "bilingual_pdf" not in summary
