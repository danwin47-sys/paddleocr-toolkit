# -*- coding: utf-8 -*-
"""
Advanced tests for CLI ModeProcessor to maximize coverage.
"""
import pytest
import argparse
import sys
from unittest.mock import MagicMock, patch, Mock
from pathlib import Path
from paddleocr_toolkit.cli.mode_processor import ModeProcessor


class TestModeProcessorAdvanced:
    @patch("paddleocr_toolkit.cli.mode_processor.sys.exit")
    @patch("paddle_ocr_tool.HAS_TRANSLATOR", False)
    def test_translator_missing_exit(self, mock_exit, tmp_path):
        """Test exit when translator module is missing"""
        # Mock exit to raise SystemExit so execution stops
        mock_exit.side_effect = SystemExit(1)

        tool = Mock()
        args = argparse.Namespace(mode="hybrid", translate=True, no_progress=False)
        processor = ModeProcessor(tool, args, tmp_path / "f.pdf", tmp_path)

        # Should call sys.exit(1)
        with pytest.raises(SystemExit):
            processor.process()

        mock_exit.assert_called_with(1)

    def test_basic_image_searchable(self, tmp_path):
        """Test basic mode with image and searchable=True (PDF generation)"""
        tool = Mock()
        tool.process_image.return_value = [Mock()]
        tool.get_text.return_value = "Image Text"

        args = argparse.Namespace(
            mode="basic",
            output=None,
            text_output=None,
            searchable=True,  # Toggle to True
            dpi=150,
            recursive=False,
            debug_text=False,
            no_progress=False,
        )
        input_path = tmp_path / "img.png"
        input_path.touch()

        with patch("paddleocr_toolkit.core.PDFGenerator") as mock_pdf_cls:
            mock_pdf_gen = Mock()
            mock_pdf_cls.return_value = mock_pdf_gen

            processor = ModeProcessor(tool, args, input_path, tmp_path)
            processor._process_basic()

            mock_pdf_gen.add_page.assert_called()
            mock_pdf_gen.save.assert_called()

    def test_text_output_absolute_path(self, tmp_path):
        """Test text output with absolute path"""
        tool = Mock()
        tool.process_pdf.return_value = ([[Mock()]], None)
        tool.get_text.return_value = "Absolute Text"

        abs_output = tmp_path / "abs_out.txt"

        args = argparse.Namespace(
            mode="basic",
            output=None,
            text_output=str(abs_output),  # Absolute path
            searchable=False,
            dpi=150,
            recursive=False,
            debug_text=False,
            no_progress=False,
        )
        input_path = tmp_path / "doc.pdf"
        input_path.touch()

        processor = ModeProcessor(tool, args, input_path, tmp_path)
        processor._process_basic()

        assert abs_output.exists()
        assert "Absolute Text" in abs_output.read_text("utf-8")

    @patch("paddle_ocr_tool.HAS_TRANSLATOR", True)
    def test_hybrid_translation_full_logging(self, tmp_path, caplog):
        """Test all logging branches in hybrid translation"""
        tool = Mock()
        # Return dict withALL keys to trigger all log lines
        tool.process_translate.return_value = {
            "pages_processed": 1,
            "searchable_pdf": "s.pdf",
            "markdown_file": "m.md",
            "json_file": "j.json",
            "html_file": "h.html",
            "translated_pdf": "t.pdf",
            "bilingual_pdf": "b.pdf",
        }

        args = argparse.Namespace(
            mode="hybrid",
            translate=True,
            source_lang="en",
            target_lang="zh",
            ollama_model="m",
            ollama_url="u",
            no_mono=False,
            no_dual=False,
            dual_mode="m",
            dual_translate_first=True,
            font_path=None,
            output=None,
            dpi=150,
            json_output=None,
            html_output=None,
            ocr_workaround=False,
            no_progress=False,
        )

        with patch("paddleocr_toolkit.cli.mode_processor.logger") as mock_logger:
            processor = ModeProcessor(tool, args, tmp_path / "f.pdf", tmp_path)
            processor._process_hybrid_with_translation()

            # Verify specific log calls
            calls = [c[0] for c in mock_logger.info.call_args_list]
            assert any("Searchable PDF" in str(c) for c in calls)
            assert any("Markdown" in str(c) for c in calls)
            assert any("JSON" in str(c) for c in calls)
            assert any("HTML" in str(c) for c in calls)
            assert any("Translated PDF" in str(c) for c in calls)
            assert any("Bilingual PDF" in str(c) for c in calls)
