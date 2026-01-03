# -*- coding: utf-8 -*-
"""
測試 FormulaProcessor
"""

import tempfile
import os
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
            mock_output = [
                ([[0, 0], [10, 0], [10, 10], [0, 10]], "x^2 + y^2 = z^2", 0.99)
            ]
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
                assert (
                    result["formulas_by_page"][0]["formulas"][0]["latex"]
                    == "\\alpha + \\beta"
                )
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)


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
        formulas_by_page = [{"page": 1, "formulas": [{"latex": "x=1"}]}]

        with tempfile.NamedTemporaryFile(suffix=".tex", delete=False) as tmp:
            tex_path = tmp.name

        try:
            processor._save_latex(formulas_by_page, tex_path)
            content = Path(tex_path).read_text(encoding="utf-8")
            assert "x=1" in content
            assert "第 1 頁" in content
        finally:
            if os.path.exists(tex_path):
                os.remove(tex_path)


# Added from Ultra Coverage
from paddleocr_toolkit.processors.formula_processor import FormulaProcessor
from unittest.mock import MagicMock, patch
import pytest


class TestFormulaProcessorUltra:
    def test_formula_processor_init_error(self):
        mock_mgr = MagicMock()
        mock_mgr.get_mode.return_value.value = "ocr"
        with pytest.raises(ValueError, match="FormulaProcessor 需要 formula 模式"):
            FormulaProcessor(mock_mgr)

    def test_process_image_error(self):
        mock_mgr = MagicMock()
        mock_mgr.get_mode.return_value.value = "formula"
        processor = FormulaProcessor(mock_mgr)

        # 1. Image is None (line 87)
        with patch("cv2.imread", return_value=None):
            res = processor.process_image("invalid.jpg")
            assert "無法讀取" in res["error"]

        # 2. General exception (lines 102-104)
        with patch("cv2.imread", side_effect=Exception("CV2 error")):
            res = processor.process_image("invalid.jpg")
            assert "CV2 error" in res["error"]

    def test_process_pdf_page_loop_errors(self):
        mock_mgr = MagicMock()
        mock_mgr.get_mode.return_value.value = "formula"
        processor = FormulaProcessor(mock_mgr)
        with patch("fitz.open") as mock_fitz:
            mock_doc = MagicMock()
            mock_doc.__len__.return_value = 1
            mock_page = MagicMock()
            mock_doc.__getitem__.return_value = mock_page
            mock_fitz.return_value = mock_doc
            # Force page error
            mock_page.get_pixmap.side_effect = Exception("Pixmap error")
            res = processor.process_pdf("test.pdf")
            assert res["pages_processed"] == 0

    def test_parse_formula_output_exception(self):
        mock_mgr = MagicMock()
        mock_mgr.get_mode.return_value.value = "formula"
        processor = FormulaProcessor(mock_mgr)
        # Trigger exception in _parse_formula_output (line 213)
        res = processor._parse_formula_output(
            MagicMock()
        )  # Passing something that causes iteration error
        assert res == []

    def test_save_latex_exception(self):
        mock_mgr = MagicMock()
        mock_mgr.get_mode.return_value.value = "formula"
        processor = FormulaProcessor(mock_mgr)
        with patch("builtins.open", side_effect=Exception("Write Error")):
            processor._save_latex([{"page": 1, "formulas": []}], "out.tex")


class TestFormulaUltraMore:
    def test_formula_processor_exception(self):
        mock_mgr = MagicMock()
        mock_mgr.get_mode.return_value.value = "formula"
        proc = FormulaProcessor(mock_mgr)

        # Trigger line 214 exception in _parse_formula_output
        mock_bad_item = MagicMock()
        mock_bad_item.__len__.side_effect = TypeError("Bad len")
        res = proc._parse_formula_output([mock_bad_item])
        assert res == []
