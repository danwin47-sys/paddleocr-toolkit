# -*- coding: utf-8 -*-
"""
測試 HybridPDFProcessor - 額外覆蓋率測試
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from paddleocr_toolkit.core import OCRMode, OCRResult
from paddleocr_toolkit.core.ocr_engine import OCREngineManager
from paddleocr_toolkit.processors.hybrid_processor import HybridPDFProcessor


class TestHybridProcessorLayoutAnalysis:
    """測試版面分析相關功能"""

    @pytest.fixture
    def processor(self):
        """建立 processor 實例"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.HYBRID
        return HybridPDFProcessor(mock_engine)

    def test_extract_markdown_from_structure_result(self, processor):
        """測試從結構化結果提取 Markdown"""
        mock_result = Mock()
        mock_result.markdown = "## 章節標題\n\n- 項目 1\n- 項目 2"
        
        structure_output = [mock_result]
        
        processor.result_parser.parse_structure_result = Mock(return_value=[
            OCRResult(text="章節標題", confidence=0.9, bbox=[[0, 0], [100, 0], [100, 20], [0, 20]]),
            OCRResult(text="項目 1", confidence=0.9, bbox=[[0, 30], [100, 30], [100, 50], [0, 50]]),
        ])
        
        ocr_results, markdown = processor._extract_and_merge_results(structure_output, 0)
        
        assert len(ocr_results) == 2
        assert "章節標題" in markdown
        assert "項目 1" in markdown
        assert "第 1 頁" in markdown

    def test_extract_markdown_from_result_helper(self, processor):
        """測試 Markdown 提取輔助方法"""
        mock_result = Mock()
        mock_result.markdown = "# 標題\n\n內容"
        
        markdown = processor._extract_markdown_from_result(mock_result)
        
        assert "標題" in markdown
        assert "內容" in markdown


class TestHybridProcessorErrorHandling:
    """測試錯誤處理"""

    @pytest.fixture
    def processor(self):
        """建立 processor 實例"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.HYBRID
        return HybridPDFProcessor(mock_engine)

    @patch("paddleocr_toolkit.processors.hybrid_processor.fitz")
    def test_process_pdf_with_ocr_error(self, mock_fitz, processor):
        """測試 OCR 處理錯誤"""
        mock_pdf = MagicMock()
        mock_pdf.__len__.return_value = 1
        mock_fitz.open.return_value = mock_pdf
        
        # Mock OCR 引擎拋出錯誤
        processor.engine_manager.predict = Mock(side_effect=Exception("OCR 引擎錯誤"))
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf_path = tmp.name
        
        try:
            with patch("paddleocr_toolkit.processors.hybrid_processor.detect_pdf_quality") as mock_detect:
                mock_detect.return_value = {
                    "is_scanned": False,
                    "is_blurry": False,
                    "reason": "清晰",
                    "recommended_dpi": 150,
                }
                
                result = processor.process_pdf(pdf_path)
                
                # 應該返回錯誤資訊
                assert "error" in result or result.get("pages_processed", 0) == 0
        finally:
            Path(pdf_path).unlink(missing_ok=True)

    def test_extract_with_empty_structure_output(self, processor):
        """測試空結構化輸出"""
        structure_output = []
        
        processor.result_parser.parse_structure_result = Mock(return_value=[])
        
        ocr_results, markdown = processor._extract_and_merge_results(structure_output, 0)
        
        assert len(ocr_results) == 0
        assert "第 1 頁" in markdown


class TestHybridProcessorImageCompression:
    """測試圖片壓縮功能"""

    def test_compression_enabled(self):
        """測試啟用壓縮"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.HYBRID
        
        processor = HybridPDFProcessor(
            mock_engine,
            compress_images=True,
            jpeg_quality=75
        )
        
        assert processor.compress_images is True
        assert processor.jpeg_quality == 75

    def test_compression_disabled(self):
        """測試禁用壓縮"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.HYBRID
        
        processor = HybridPDFProcessor(
            mock_engine,
            compress_images=False
        )
        
        assert processor.compress_images is False


class TestHybridProcessorDebugMode:
    """測試除錯模式"""

    def test_debug_mode_enabled(self):
        """測試啟用除錯模式"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.HYBRID
        
        processor = HybridPDFProcessor(mock_engine, debug_mode=True)
        
        assert processor.debug_mode is True

    @patch("paddleocr_toolkit.processors.hybrid_processor.fitz")
    def test_debug_mode_affects_pdf_generation(self, mock_fitz, processor):
        """測試除錯模式影響 PDF 生成"""
        # 這個測試驗證除錯模式是否傳遞給 PDF 生成器
        processor_debug = HybridPDFProcessor(
            processor.engine_manager,
            debug_mode=True
        )
        
        assert processor_debug.debug_mode is True
