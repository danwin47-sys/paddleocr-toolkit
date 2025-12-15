# -*- coding: utf-8 -*-
"""
Tests for CLI output path manager
"""

import argparse
from pathlib import Path

import pytest

from paddleocr_toolkit.cli.output_manager import OutputPathManager


class TestOutputPathManagerInit:
    """Test OutputPathManager initialization"""

    def test_basic_init(self, tmp_path):
        """Test basic initialization"""
        input_file = tmp_path / "test.pdf"
        input_file.touch()

        manager = OutputPathManager(str(input_file), mode="basic")

        assert manager.input_path == input_file
        assert manager.mode == "basic"
        assert manager.base_name == "test"
        assert manager.parent_dir == tmp_path

    def test_init_with_structure_mode(self, tmp_path):
        """Test initialization with structure mode"""
        input_file = tmp_path / "document.pdf"
        manager = OutputPathManager(str(input_file), mode="structure")
        assert manager.mode == "structure"


class TestGetSearchablePdfPath:
    """Test get_searchable_pdf_path method"""

    def test_with_custom_output(self, tmp_path):
        """Test with custom output path"""
        input_file = tmp_path / "test.pdf"
        manager = OutputPathManager(str(input_file))

        custom_path = "/custom/output.pdf"
        result = manager.get_searchable_pdf_path(custom_output=custom_path)

        assert result == custom_path

    def test_with_auto_output(self, tmp_path):
        """Test automatic path generation"""
        input_file = tmp_path / "document.pdf"
        manager = OutputPathManager(str(input_file))

        result = manager.get_searchable_pdf_path()

        assert "_searchable.pdf" in result
        assert "document" in result


class TestGetTextOutputPath:
    """Test get_text_output_path method"""

    def test_with_auto(self, tmp_path):
        """Test AUTO mode"""
        input_file = tmp_path / "test.pdf"
        manager = OutputPathManager(str(input_file))

        result = manager.get_text_output_path(custom_output="AUTO")

        assert result is not None
        assert "_ocr.txt" in result

    def test_with_none(self, tmp_path):
        """Test None input"""
        input_file = tmp_path / "test.pdf"
        manager = OutputPathManager(str(input_file))

        result = manager.get_text_output_path(custom_output=None)
        assert result is None


class TestGetMarkdownOutputPath:
    """Test get_markdown_output_path method"""

    def test_auto_with_structure_mode(self, tmp_path):
        """Test structure mode automatic path"""
        input_file = tmp_path / "document.pdf"
        manager = OutputPathManager(str(input_file), mode="structure")

        result = manager.get_markdown_output_path(custom_output="AUTO")

        assert result is not None
        assert "document_structure.md" in result


class TestGetJsonOutputPath:
    """Test get_json_output_path method"""

    def test_auto_generation(self, tmp_path):
        """Test automatic JSON path generation"""
        input_file = tmp_path / "test.pdf"
        manager = OutputPathManager(str(input_file), mode="structure")

        result = manager.get_json_output_path(custom_output="AUTO")

        assert result is not None
        assert "test_structure.json" in result


class TestGetHtmlOutputPath:
    """Test get_html_output_path method"""

    def test_auto_generation(self, tmp_path):
        """Test automatic HTML path generation"""
        input_file = tmp_path / "doc.pdf"
        manager = OutputPathManager(str(input_file), mode="hybrid")

        result = manager.get_html_output_path(custom_output="AUTO")

        assert result is not None
        assert "doc_hybrid.html" in result


class TestGetExcelOutputPath:
    """Test get_excel_output_path method"""

    def test_auto_generation(self, tmp_path):
        """Test automatic Excel path generation"""
        input_file = tmp_path / "data.pdf"
        manager = OutputPathManager(str(input_file))

        result = manager.get_excel_output_path(custom_output="AUTO")

        assert result is not None
        assert "data_tables.xlsx" in result


class TestGetLatexOutputPath:
    """Test get_latex_output_path method"""

    def test_auto_generation(self, tmp_path):
        """Test automatic LaTeX path generation"""
        input_file = tmp_path / "formula.png"
        manager = OutputPathManager(str(input_file))

        result = manager.get_latex_output_path(custom_output="AUTO")

        assert result is not None
        assert "formula_formula.tex" in result


class TestProcessModeOutputs:
    """Test process_mode_outputs method"""

    def test_basic_mode(self, tmp_path):
        """Test basic mode output processing"""
        input_file = tmp_path / "test.pdf"
        manager = OutputPathManager(str(input_file), mode="basic")

        args = argparse.Namespace(output=None, text_output="AUTO", searchable=True)

        result = manager.process_mode_outputs(args, tmp_path)

        # Basic mode doesn't set output if it's None
        assert result.text_output is not None

    def test_formula_mode(self, tmp_path):
        """Test formula mode output processing"""
        input_file = tmp_path / "math.png"
        manager = OutputPathManager(str(input_file), mode="formula")

        args = argparse.Namespace(latex_output="AUTO")

        result = manager.process_mode_outputs(args, tmp_path)

        assert result.latex_output is not None

    def test_structure_mode(self, tmp_path):
        """Test structure mode output processing"""
        input_file = tmp_path / "doc.pdf"
        manager = OutputPathManager(str(input_file), mode="structure")

        args = argparse.Namespace(
            markdown_output="AUTO",
            json_output="AUTO",
            excel_output=None,
            html_output=None,
        )

        result = manager.process_mode_outputs(args, tmp_path)

        assert result.markdown_output is not None
        assert result.json_output is not None

    def test_hybrid_mode(self, tmp_path):
        """Test hybrid mode output processing"""
        input_file = tmp_path / "test.pdf"
        manager = OutputPathManager(str(input_file), mode="hybrid")

        args = argparse.Namespace(
            output=None, markdown_output="AUTO", json_output=None, html_output="AUTO"
        )

        result = manager.process_mode_outputs(args, tmp_path)

        # Hybrid mode doesn't always set output
        assert result.markdown_output is not None
        assert result.html_output is not None


class TestPrintOutputSummary:
    """Test print_output_summary method"""

    def test_basic_mode_summary(self, tmp_path, capsys):
        """Test basic mode summary"""
        input_file = tmp_path / "test.pdf"
        manager = OutputPathManager(str(input_file), mode="basic")

        args = argparse.Namespace(
            output="/out/test.pdf", text_output="/out/test.txt", searchable=True
        )

        manager.print_output_summary(args)

        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_formula_mode_summary(self, tmp_path, capsys):
        """Test formula mode summary"""
        input_file = tmp_path / "math.png"
        manager = OutputPathManager(str(input_file), mode="formula")

        args = argparse.Namespace(latex_output="/out/formula.tex")

        manager.print_output_summary(args)

        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_structure_mode_summary(self, tmp_path, capsys):
        """Test structure mode summary"""
        input_file = tmp_path / "doc.pdf"
        manager = OutputPathManager(str(input_file), mode="structure")

        args = argparse.Namespace(
            markdown_output="/out/doc.md",
            json_output="/out/doc.json",
            excel_output="/out/tables.xlsx",
            html_output="/out/page.html",
        )

        manager.print_output_summary(args)

        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_hybrid_mode_summary(self, tmp_path, capsys):
        """Test hybrid mode summary"""
        input_file = tmp_path / "test.pdf"
        manager = OutputPathManager(str(input_file), mode="hybrid")

        args = argparse.Namespace(
            output="/out/test.pdf",
            markdown_output="/out/test.md",
            json_output=None,
            html_output="/out/test.html",
        )

        manager.print_output_summary(args)

        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_vl_mode_summary(self, tmp_path, capsys):
        """Test vl mode summary"""
        input_file = tmp_path / "doc.pdf"
        manager = OutputPathManager(str(input_file), mode="vl")

        args = argparse.Namespace(
            markdown_output="/out/doc.md",
            json_output="/out/doc.json",
            excel_output=None,
            html_output=None,
        )

        manager.print_output_summary(args)

        captured = capsys.readouterr()
        assert len(captured.out) > 0
