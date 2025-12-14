# -*- coding: utf-8 -*-
"""
Tests for CLI mode processor
"""

import pytest
import argparse
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from paddleocr_toolkit.cli.mode_processor import ModeProcessor


class TestModeProcessorInit:
    """Test ModeProcessor initialization"""
    
    def test_basic_init(self, tmp_path):
        """Test basic initialization"""
        tool = Mock()
        args = argparse.Namespace(
            mode="basic",
            no_progress=False
        )
        input_path = tmp_path / "test.pdf"
        script_dir = tmp_path
        
        processor = ModeProcessor(tool, args, input_path, script_dir)
        
        assert processor.tool == tool
        assert processor.args == args
        assert processor.input_path == input_path
        assert processor.script_dir == script_dir
        assert processor.show_progress is True
    
    def test_init_with_no_progress(self, tmp_path):
        """Test initialization with no_progress flag"""
        tool = Mock()
        args = argparse.Namespace(
            mode="structure",
            no_progress=True
        )
        input_path = tmp_path / "doc.pdf"
        script_dir = tmp_path
        
        processor = ModeProcessor(tool, args, input_path, script_dir)
        
        assert processor.show_progress is False


class TestProcessMethod:
    """Test process method routing"""
    
    def test_process_formula_mode(self, tmp_path):
        """Test routing to formula mode"""
        tool = Mock()
        tool.process_formula.return_value = {"formulas": []}
        
        args = argparse.Namespace(
            mode="formula",
            latex_output=None,
            no_progress=False
        )
        input_path = tmp_path / "math.png"
        
        processor = ModeProcessor(tool, args, input_path, tmp_path)
        result = processor.process()
        
        tool.process_formula.assert_called_once()
        assert isinstance(result, dict)
    
    def test_process_structure_mode(self, tmp_path):
        """Test routing to structure mode"""
        tool = Mock()
        tool.process_structured.return_value = {
            "pages_processed": 1,
            "markdown_files": []
        }
        
        args = argparse.Namespace(
            mode="structure",
            markdown_output=None,
            json_output=None,
            excel_output=None,
            html_output=None,
            no_progress=False
        )
        input_path = tmp_path / "doc.pdf"
        
        processor = ModeProcessor(tool, args, input_path, tmp_path)
        result = processor.process()
        
        tool.process_structured.assert_called_once()
        assert isinstance(result, dict)
    
    def test_process_vl_mode(self, tmp_path):
        """Test routing to vl mode"""
        tool = Mock()
        tool.process_structured.return_value = {
            "pages_processed": 1,
            "json_files": []
        }
        
        args = argparse.Namespace(
            mode="vl",
            markdown_output=None,
            json_output="AUTO",
            excel_output=None,
            html_output=None,
            no_progress=False
        )
        input_path = tmp_path / "doc.pdf"
        
        processor = ModeProcessor(tool, args, input_path, tmp_path)
        result = processor.process()
        
        tool.process_structured.assert_called_once()
    
    def test_process_hybrid_mode_without_translation(self, tmp_path):
        """Test routing to hybrid mode without translation"""
        tool = Mock()
        tool.process_hybrid.return_value = {
            "pages_processed": 1,
            "searchable_pdf": "/output/test.pdf"
        }
        
        args = argparse.Namespace(
            mode="hybrid",
            output=None,
            markdown_output=None,
            json_output=None,
            html_output=None,
            dpi=150,
            no_progress=False
        )
        input_path = tmp_path / "test.pdf"
        
        processor = ModeProcessor(tool, args, input_path, tmp_path)
        result = processor.process()
        
        tool.process_hybrid.assert_called_once()
    
    def test_process_basic_mode_with_pdf(self, tmp_path):
        """Test basic mode with PDF file"""
        tool = Mock()
        tool.process_pdf.return_value = ([[]], "/output/test.pdf")
        tool.get_text.return_value = "Sample text"
        
        args = argparse.Namespace(
            mode="basic",
            output=None,
            text_output=None,
            searchable=True,
            dpi=150,
            recursive=False,
            debug_text=False,
            no_progress=False
        )
        input_path = tmp_path / "test.pdf"
        input_path.touch()
        
        processor = ModeProcessor(tool, args, input_path, tmp_path)
        result = processor.process()
        
        tool.process_pdf.assert_called_once()
        assert result["status"] == "success"


class TestProcessFormula:
    """Test _process_formula method"""
    
    def test_formula_success(self, tmp_path, capsys):
        """Test successful formula processing"""
        tool = Mock()
        tool.process_formula.return_value = {
            "formulas": ["x^2 + y^2 = z^2"],
            "latex_file": "/output/formula.tex"
        }
        
        args = argparse.Namespace(
            mode="formula",
            latex_output="AUTO",
            no_progress=False
        )
        input_path = tmp_path / "math.png"
        
        processor = ModeProcessor(tool, args, input_path, tmp_path)
        result = processor._process_formula()
        
        assert len(result["formulas"]) == 1
        assert result["latex_file"] == "/output/formula.tex"
        
        captured = capsys.readouterr()
        assert "OK" in captured.out
    
    def test_formula_with_error(self, tmp_path, capsys):
        """Test formula processing with error"""
        tool = Mock()
        tool.process_formula.return_value = {
            "error": "Processing failed"
        }
        
        args = argparse.Namespace(
            mode="formula",
            latex_output=None,
            no_progress=False
        )
        input_path = tmp_path / "math.png"
        
        processor = ModeProcessor(tool, args, input_path, tmp_path)
        result = processor._process_formula()
        
        assert "error" in result
        
        captured = capsys.readouterr()
        # Check for error message in output
        assert captured.out  # Just verify output exists


class TestProcessStructured:
    """Test _process_structured method"""
    
    def test_structured_success(self, tmp_path, capsys):
        """Test successful structured processing"""
        tool = Mock()
        tool.process_structured.return_value = {
            "pages_processed": 3,
            "markdown_files": ["/output/doc.md"],
            "json_files": ["/output/doc.json"],
            "excel_files": ["/output/tables.xlsx"],
            "html_files": ["/output/page1.html"]
        }
        
        args = argparse.Namespace(
            mode="structure",
            markdown_output="AUTO",
            json_output="AUTO",
            excel_output="AUTO",
            html_output="AUTO",
            no_progress=False
        )
        input_path = tmp_path / "doc.pdf"
        
        processor = ModeProcessor(tool, args, input_path, tmp_path)
        result = processor._process_structured()
        
        assert result["pages_processed"] == 3
        assert len(result["markdown_files"]) == 1
        
        captured = capsys.readouterr()
        assert "OK" in captured.out or "完成" in captured.out


class TestProcessHybrid:
    """Test _process_hybrid method"""
    
    def test_hybrid_without_translation(self, tmp_path):
        """Test hybrid mode without translation"""
        tool = Mock()
        tool.process_hybrid.return_value = {
            "pages_processed": 2,
            "searchable_pdf": "/output/test.pdf"
        }
        
        args = argparse.Namespace(
            mode="hybrid",
            output=None,
            markdown_output=None,
            json_output=None,
            html_output=None,
            dpi=150,
            no_progress=False
        )
        # Don't set translate attribute to test default behavior
        input_path = tmp_path / "test.pdf"
        
        processor = ModeProcessor(tool, args, input_path, tmp_path)
        result = processor._process_hybrid()
        
        tool.process_hybrid.assert_called_once()
        assert result["pages_processed"] == 2
    
    @patch('paddle_ocr_tool.HAS_TRANSLATOR', True)
    def test_hybrid_with_translation(self, tmp_path, capsys):
        """Test hybrid mode with translation enabled"""
        tool = Mock()
        tool.process_translate.return_value = {
            "pages_processed": 2,
            "searchable_pdf": "/output/test.pdf",
            "translated_pdf": "/output/test_translated.pdf",
            "bilingual_pdf": "/output/test_bilingual.pdf"
        }
        
        args = argparse.Namespace(
            mode="hybrid",
            translate=True,
            source_lang="en",
            target_lang="zh",
            ollama_model="qwen2.5:7b",
            ollama_url="http://localhost:11434",
            no_mono=False,
            no_dual=False,
            dual_mode="alternating",
            dual_translate_first=False,
            font_path=None,
            output=None,
            dpi=150,
            json_output=None,
            html_output=None,
            ocr_workaround=False,
            no_progress=False
        )
        input_path = tmp_path / "test.pdf"
        
        processor = ModeProcessor(tool, args, input_path, tmp_path)
        result = processor._process_hybrid_with_translation()
        
        tool.process_translate.assert_called_once()
        assert result["pages_processed"] == 2
        
        captured = capsys.readouterr()
        assert "翻譯" in captured.out or "translate" in captured.out.lower()


class TestProcessBasic:
    """Test _process_basic method"""
    
    def test_basic_with_pdf(self, tmp_path):
        """Test basic mode with PDF file"""
        tool = Mock()
        tool.process_pdf.return_value = (
            [[Mock()], [Mock()]],  # 2 pages of results
            "/output/test.pdf"
        )
        tool.get_text.return_value = "Sample text"
        
        args = argparse.Namespace(
            mode="basic",
            output=None,
            text_output=None,
            searchable=True,
            dpi=150,
            recursive=False,
            debug_text=False,
            no_progress=False
        )
        input_path = tmp_path / "test.pdf"
        input_path.touch()
        
        processor = ModeProcessor(tool, args, input_path, tmp_path)
        result = processor._process_basic()
        
        tool.process_pdf.assert_called_once()
        assert result["status"] == "success"
        assert "text" in result
    
    def test_basic_with_image(self, tmp_path):
        """Test basic mode with image file"""
        tool = Mock()
        tool.process_image.return_value = [Mock()]
        tool.get_text.return_value = "Image text"
        
        args = argparse.Namespace(
            mode="basic",
            output=None,
            text_output=None,
            searchable=False,
            dpi=150,
            recursive=False,
            debug_text=False,
            no_progress=False
        )
        input_path = tmp_path / "image.png"
        input_path.touch()
        
        processor = ModeProcessor(tool, args, input_path, tmp_path)
        result = processor._process_basic()
        
        tool.process_image.assert_called_once()
        assert result["status"] == "success"
    
    def test_basic_with_directory(self, tmp_path):
        """Test basic mode with directory input"""
        tool = Mock()
        tool.process_directory.return_value = {
            "file1.pdf": [[Mock()]],
            "file2.pdf": [[Mock()]]
        }
        tool.get_text.return_value = "File text"
        
        args = argparse.Namespace(
            mode="basic",
            output=None,
            text_output=None,
            searchable=True,
            recursive=True,
            debug_text=False,
            no_progress=False
        )
        input_dir = tmp_path / "docs"
        input_dir.mkdir()
        
        processor = ModeProcessor(tool, args, input_dir, tmp_path)
        result = processor._process_basic()
        
        tool.process_directory.assert_called_once()
        assert result["status"] == "success"
    
    def test_basic_with_text_output(self, tmp_path):
        """Test basic mode with text output to file"""
        tool = Mock()
        tool.process_pdf.return_value = ([[Mock()]], None)
        tool.get_text.return_value = "Output text"
        
        args = argparse.Namespace(
            mode="basic",
            output=None,
            text_output="output.txt",
            searchable=True,
            dpi=150,
            recursive=False,
            debug_text=False,
            no_progress=False
        )
        input_path = tmp_path / "test.pdf"
        input_path.touch()
        
        processor = ModeProcessor(tool, args, input_path, tmp_path)
        result = processor._process_basic()
        
        # Check that text file was created
        output_file = tmp_path / "output.txt"
        assert output_file.exists()
        assert result["status"] == "success"


class TestErrorHandling:
    """Test error handling"""
    
    def test_unsupported_file_format(self, tmp_path):
        """Test handling of unsupported file format"""
        tool = Mock()
        args = argparse.Namespace(
            mode="basic",
            no_progress=False
        )
        input_path = tmp_path / "test.xyz"
        input_path.touch()
        
        processor = ModeProcessor(tool, args, input_path, tmp_path)
        
        with pytest.raises(SystemExit):
            processor._process_basic()
