# -*- coding: utf-8 -*-
"""
StructureProcessor 测试
"""

from unittest.mock import MagicMock, Mock

import pytest

from paddleocr_toolkit.core.models import OCRResult
from paddleocr_toolkit.processors.structure_processor import StructureProcessor


class TestStructureProcessor:
    """测试结构化处理器"""

    def test_init(self):
        """测试初始化"""
        mock_engine = Mock()
        processor = StructureProcessor(structure_engine=mock_engine)

        assert processor.structure_engine == mock_engine
        assert processor.result_parser is None

    def test_init_with_parser(self):
        """测试带解析器的初始化"""
        mock_engine = Mock()
        mock_parser = Mock()

        processor = StructureProcessor(structure_engine=mock_engine, result_parser=mock_parser)

        assert processor.result_parser == mock_parser

    def test_process_basic(self):
        """测试基本处理"""
        mock_engine = Mock()
        mock_output = Mock()
        mock_engine.predict.return_value = mock_output

        processor = StructureProcessor(structure_engine=mock_engine)
        result = processor.process(input_path="test.pdf")

        assert result["input"] == "test.pdf"
        assert result["structure_output"] == mock_output
        mock_engine.predict.assert_called_once_with(input="test.pdf")

    def test_process_with_text_extraction(self):
        """测试文字提取"""
        mock_engine = Mock()
        mock_parser = Mock()
        mock_parser.return_value = [
            OCRResult("Hello", 0.95, [[0, 0], [100, 0], [100, 50], [0, 50]]),
            OCRResult("World", 0.92, [[0, 60], [100, 60], [100, 110], [0, 110]]),
        ]

        processor = StructureProcessor(structure_engine=mock_engine, result_parser=mock_parser)

        result = processor.process(input_path="test.pdf", extract_text=True)

        assert "ocr_results" in result
        assert "text" in result
        assert result["text"] == "Hello\nWorld"

    def test_extract_tables(self):
        """测试表格提取"""
        mock_engine = Mock()
        processor = StructureProcessor(structure_engine=mock_engine)

        # 模拟结构化输出
        mock_block = Mock()
        mock_block.type = "table"
        mock_block.content = "Table content"
        mock_block.bbox = [10, 10, 100, 100]

        mock_res = Mock()
        mock_res.parsing_res_list = [mock_block]

        tables = processor._extract_tables([mock_res])

        assert len(tables) == 1
        assert tables[0]["type"] == "table"
        assert tables[0]["content"] == "Table content"

    def test_analyze_layout(self):
        """测试版面分析"""
        mock_engine = Mock()
        processor = StructureProcessor(structure_engine=mock_engine)

        # 模拟不同类型的块
        text_block = Mock()
        text_block.type = "text"

        table_block = Mock()
        table_block.type = "table"

        image_block = Mock()
        image_block.type = "figure"

        mock_res = Mock()
        mock_res.parsing_res_list = [text_block, table_block, image_block]

        layout = processor.analyze_layout([mock_res])

        assert layout["text_blocks"] == 1
        assert layout["tables"] == 1
        assert layout["images"] == 1
        assert layout["other"] == 0

    def test_process_error_handling(self):
        """测试错误处理"""
        mock_engine = Mock()
        mock_engine.predict.side_effect = Exception("Test error")

        processor = StructureProcessor(structure_engine=mock_engine)
        result = processor.process(input_path="test.pdf")

        assert "error" in result
        assert "Test error" in result["error"]

    def test_extract_text_helper(self):
        """测试文字提取辅助方法"""
        mock_engine = Mock()
        processor = StructureProcessor(structure_engine=mock_engine)

        results = [
            OCRResult("Line1", 0.95, [[0, 0], [100, 0], [100, 50], [0, 50]]),
            OCRResult("Line2", 0.92, [[0, 60], [100, 60], [100, 110], [0, 110]]),
        ]

        text = processor._extract_text(results)
        assert text == "Line1\nLine2"

    def test_extract_tables_no_tables(self):
        """测试无表格情况"""
        mock_engine = Mock()
        processor = StructureProcessor(structure_engine=mock_engine)

        mock_res = Mock()
        mock_res.parsing_res_list = []

        tables = processor._extract_tables([mock_res])
        assert len(tables) == 0
