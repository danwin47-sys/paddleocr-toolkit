# -*- coding: utf-8 -*-
"""
Tests for CLI output path manager
"""

import pytest
import argparse
from pathlib import Path
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


class TestGetExcelOutputPath:
    """Test get_excel_output_path method"""
    
    def test_auto_generation(self, tmp_path):
        """Test automatic Excel path generation"""
        input_file = tmp_path / "data.pdf"
        manager = OutputPathManager(str(input_file))
        
        result = manager.get_excel_output_path(custom_output="AUTO")
        
        assert result is not None
        assert "data_tables.xlsx" in result
