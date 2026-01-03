# -*- coding: utf-8 -*-
"""
測試 BasicProcessor
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from paddleocr_toolkit.core import OCRMode, OCRResult
from paddleocr_toolkit.core.ocr_engine import OCREngineManager
from paddleocr_toolkit.processors.basic_processor import BasicProcessor


class TestBasicProcessorInitialization:
    """測試 BasicProcessor 初始化"""

    def test_init_with_basic_engine(self):
        """測試使用 basic 引擎初始化"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.BASIC

        processor = BasicProcessor(mock_engine)

        assert processor.engine_manager == mock_engine
        assert processor.debug_mode is False
        assert processor.compress_images is True
        assert processor.jpeg_quality == 85

    def test_init_with_non_basic_engine_raises_error(self):
        """測試使用非 basic 引擎初始化時丟擲錯誤"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.HYBRID

        with pytest.raises(ValueError, match="需要 basic 模式引擎"):
            BasicProcessor(mock_engine)

    def test_init_with_custom_settings(self):
        """測試使用自訂設定初始化"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.BASIC

        processor = BasicProcessor(
            mock_engine, debug_mode=True, compress_images=False, jpeg_quality=95
        )

        assert processor.debug_mode is True
        assert processor.compress_images is False
        assert processor.jpeg_quality == 95


class TestBasicProcessorProcessImage:
    """測試圖片處理"""

    @pytest.fixture
    def processor(self):
        """建立 processor 例項"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.BASIC
        return BasicProcessor(mock_engine)

    @pytest.fixture
    def sample_ocr_results(self):
        """建立測試用 OCR 結果"""
        return [
            OCRResult(
                text="測試文字",
                confidence=0.95,
                bbox=[[0, 0], [100, 0], [100, 30], [0, 30]],
            )
        ]

    def test_process_image_success(self, processor, sample_ocr_results):
        """測試成功處理圖片處理"""
        mock_cv2 = MagicMock()
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_cv2.imread.return_value = mock_image

        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            # Mock OCR
            processor.engine_manager.predict = Mock(return_value=["mock_result"])
            processor.result_parser = Mock()
            processor.result_parser.parse_basic_result.return_value = sample_ocr_results

            result = processor.process_image("test.jpg")

            assert "ocr_results" in result
            assert result["text_count"] == 1
            assert result["image"] == "test.jpg"

    def test_process_image_text_format(self, processor, sample_ocr_results):
        """測試文字格式輸出"""
        mock_cv2 = MagicMock()
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_cv2.imread.return_value = mock_image

        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            processor.engine_manager.predict = Mock(return_value=["mock_result"])
            processor.result_parser = Mock()
            processor.result_parser.parse_basic_result.return_value = sample_ocr_results

            result = processor.process_image("test.jpg", output_format="text")

            assert "text" in result
            assert "測試文字" in result["text"]

    def test_process_image_not_found(self, processor):
        """測試圖片不存在"""
        mock_cv2 = MagicMock()
        mock_cv2.imread.return_value = None

        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            result = processor.process_image("not_exist.jpg")

            assert "error" in result


class TestBasicProcessorProcessBatch:
    """測試批次處理"""

    @pytest.fixture
    def processor(self):
        """建立 processor 例項"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.BASIC
        return BasicProcessor(mock_engine)

    def test_process_batch(self, processor):
        """測試批次處理"""
        with patch.object(processor, "process_image") as mock_process:
            mock_process.return_value = {"text": "test"}

            results = processor.process_batch(
                ["img1.jpg", "img2.jpg"], show_progress=False
            )

            assert len(results) == 2
            assert mock_process.call_count == 2


class TestBasicProcessorProcessPDF:
    """測試 PDF 處理"""

    @pytest.fixture
    def processor(self):
        """建立 processor 例項"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.BASIC
        return BasicProcessor(mock_engine)

    @patch("paddleocr_toolkit.processors.basic_processor.fitz")
    @patch("paddleocr_toolkit.processors.basic_processor.PDFGenerator")
    def test_process_pdf_basic(self, mock_pdf_gen_class, mock_fitz, processor):
        """測試基本 PDF 處理"""
        # Mock PDF
        mock_pdf = MagicMock()
        mock_pdf.__len__.return_value = 1
        mock_page = Mock()
        mock_pixmap = Mock()
        mock_page.get_pixmap.return_value = mock_pixmap
        mock_pdf.__getitem__.return_value = mock_page
        mock_fitz.open.return_value = mock_pdf

        # Mock PDF Generator
        mock_gen = Mock()
        mock_gen.save.return_value = True
        mock_pdf_gen_class.return_value = mock_gen

        # Mock OCR
        processor.engine_manager.predict = Mock(return_value=["result"])
        processor.result_parser = Mock()
        processor.result_parser.parse_basic_result.return_value = []

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf_path = tmp.name

        try:
            with patch(
                "paddleocr_toolkit.processors.basic_processor.pixmap_to_numpy"
            ) as mock_p2n:
                mock_p2n.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
                result = processor.process_pdf(pdf_path, show_progress=False)

                assert result["mode"] == "basic"
                assert result["pages_processed"] == 1
                assert result["searchable_pdf"] is not None
        finally:
            import os

            if os.path.exists(pdf_path):
                os.remove(pdf_path)


class TestBasicProcessorUtilityMethods:
    """測試工具方法"""

    @pytest.fixture
    def processor(self):
        """建立 processor 例項"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.BASIC
        return BasicProcessor(mock_engine)

    def test_get_text(self, processor):
        """測試文字提取"""
        results = [
            OCRResult(
                text="第一行", confidence=0.9, bbox=[[0, 0], [100, 0], [100, 30], [0, 30]]
            ),
            OCRResult(
                text="第二行",
                confidence=0.95,
                bbox=[[0, 40], [100, 40], [100, 70], [0, 70]],
            ),
        ]

        text = processor.get_text(results)

        assert text == "第一行\n第二行"

    def test_filter_by_confidence(self, processor):
        """測試置信度過濾"""
        results = [
            OCRResult(
                text="高", confidence=0.9, bbox=[[0, 0], [100, 0], [100, 30], [0, 30]]
            ),
            OCRResult(
                text="低", confidence=0.3, bbox=[[0, 40], [100, 40], [100, 70], [0, 70]]
            ),
        ]

        filtered = processor.filter_by_confidence(results, min_confidence=0.5)

        assert len(filtered) == 1
        assert filtered[0].text == "高"


# Added from Ultra Coverage
from paddleocr_toolkit.processors.basic_processor import BasicProcessor
from unittest.mock import MagicMock, patch


class TestBasicProcessorUltra:
    def test_process_image_error(self):
        mock_mgr = MagicMock()
        mock_mgr.get_mode.return_value.value = "basic"
        proc = BasicProcessor(mock_mgr)

        # 1. image is None (line 110)
        with patch("cv2.imread", return_value=None):
            res = proc.process_image("invalid.jpg")
            assert "無法讀取" in res["error"]

        # 2. General exception (line 144)
        with patch("cv2.imread", side_effect=Exception("CV2 error")):
            res = proc.process_image("invalid.jpg")
            assert "CV2 error" in res["error"]

    def test_process_pdf_errors(self):
        mock_mgr = MagicMock()
        mock_mgr.get_mode.return_value.value = "basic"
        proc = BasicProcessor(mock_mgr)

        # 1. Page loop exception (line 243)
        with patch("fitz.open") as mock_fitz:
            mock_doc = MagicMock()
            mock_doc.__len__.return_value = 1
            mock_page = MagicMock()
            mock_doc.__getitem__.return_value = mock_page
            mock_fitz.return_value = mock_doc
            mock_page.get_pixmap.side_effect = Exception("Page error")
            res = proc.process_pdf("test.pdf")
            assert res["pages_processed"] == 0

        # 2. General exception (line 257)
        with patch("fitz.open", side_effect=Exception("Fatal PDF error")):
            res = proc.process_pdf("test.pdf")
            assert "Fatal PDF error" in res["error"]
