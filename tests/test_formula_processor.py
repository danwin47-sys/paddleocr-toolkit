# -*- coding: utf-8 -*-
"""
測試 FormulaProcessor
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from paddleocr_toolkit.core import OCRMode
from paddleocr_toolkit.core.ocr_engine import OCREngineManager
from paddleocr_toolkit.processors.formula_processor import FormulaProcessor


class TestFormulaProcessorInitialization:
    """測試 FormulaProcessor 初始化"""

    def test_init_with_formula_engine(self):
        """測試使用 formula 引擎初始化"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.FORMULA

        processor = FormulaProcessor(mock_engine)

        assert processor.engine_manager == mock_engine

    def test_init_with_non_formula_engine_raises_error(self):
        """測試使用非 formula 引擎初始化時丟擲錯誤"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.BASIC

        with pytest.raises(ValueError, match="需要 formula 模式引擎"):
            FormulaProcessor(mock_engine)


class TestFormulaProcessorProcessImage:
    """測試圖片處理"""

    @pytest.fixture
    def processor(self):
        """建立 processor 例項"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.FORMULA
        return FormulaProcessor(mock_engine)

    def test_process_image_success(self, processor):
        """測試成功處理圖片"""
        mock_cv2 = MagicMock()
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_cv2.imread.return_value = mock_image
        
        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            # Mock OCR 輸出: [(bbox, latex_str, confidence), ...]
            mock_output = [([[0, 0], [10, 0], [10, 10], [0, 10]], "x^2 + y^2 = z^2", 0.99)]
            processor.engine_manager.predict = Mock(return_value=mock_output)
    
            result = processor.process_image("test_formula.jpg")
    
            assert "formulas" in result
            assert result["formula_count"] == 1
            assert result["formulas"][0]["latex"] == "x^2 + y^2 = z^2"

    def test_process_image_error(self, processor):
        """測試處理圖片失敗"""
        mock_cv2 = MagicMock()
        mock_cv2.imread.return_value = None
        
        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            result = processor.process_image("invalid.jpg")
            assert "error" in result


class TestFormulaProcessorProcessPDF:
    """測試 PDF 處理"""

    @pytest.fixture
    def processor(self):
        """建立 processor 例項"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.FORMULA
        return FormulaProcessor(mock_engine)

    @patch("paddleocr_toolkit.processors.formula_processor.fitz")
    def test_process_pdf_formula(self, mock_fitz, processor):
        """測試 PDF 公式識別"""
        # Mock PDF
        mock_pdf = MagicMock()
        mock_pdf.__len__.return_value = 1
        mock_page = Mock()
        mock_pixmap = Mock()
        mock_page.get_pixmap.return_value = mock_pixmap
        mock_pdf.__getitem__.return_value = mock_page
        mock_fitz.open.return_value = mock_pdf

        # Mock OCR 輸出
        mock_output = [([[0, 0], [10, 0], [10, 10], [0, 10]], "\\alpha + \\beta", 0.95)]
        processor.engine_manager.predict = Mock(return_value=mock_output)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf_path = tmp.name

        try:
            with patch(
                "paddleocr_toolkit.processors.formula_processor.pixmap_to_numpy"
            ):
                result = processor.process_pdf(pdf_path, show_progress=False)

                assert result["pages_processed"] == 1
                assert result["total_formulas"] == 1
                assert result["formulas_by_page"][0]["formulas"][0]["latex"] == "\\alpha + \\beta"
        finally:
            Path(pdf_path).unlink(missing_ok=True)


class TestFormulaProcessorUtility:
    """測試工具方法"""

    @pytest.fixture
    def processor(self):
        """建立 processor 例項"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.FORMULA
        return FormulaProcessor(mock_engine)

    def test_extract_formulas_text(self, processor):
        """測試提取公式文字"""
        formulas = [
            {"latex": "a+b=c"},
            {"latex": "E=mc^2"},
        ]
        text = processor.extract_formulas_text(formulas)
        assert text == "a+b=c\n\nE=mc^2"

    def test_save_latex(self, processor):
        """測試儲存 LaTeX 檔案"""
        formulas_by_page = [
            {"page": 1, "formulas": [{"latex": "x=1"}]}
        ]
        
        with tempfile.NamedTemporaryFile(suffix=".tex", delete=False) as tmp:
            tex_path = tmp.name
            
        try:
            processor._save_latex(formulas_by_page, tex_path)
            content = Path(tex_path).read_text(encoding="utf-8")
            assert "x=1" in content
            assert "第 1 頁" in content
        finally:
            Path(tex_path).unlink(missing_ok=True)
