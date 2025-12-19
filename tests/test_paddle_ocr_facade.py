# -*- coding: utf-8 -*-
"""
測試 PaddleOCRFacade
"""

from unittest.mock import Mock, patch

import pytest

from paddle_ocr_facade import PaddleOCRFacade
from paddleocr_toolkit.core import OCRMode


class TestPaddleOCRFacadeInitialization:
    """測試 PaddleOCRFacade 初始化"""

    @patch("paddle_ocr_facade.OCREngineManager")
    def test_init_basic_mode(self, mock_engine_class):
        """測試基本模式初始化"""
        mock_engine = Mock()
        mock_engine.get_mode.return_value = OCRMode.BASIC
        mock_engine_class.return_value = mock_engine

        facade = PaddleOCRFacade(mode="basic")

        assert facade.mode == "basic"
        assert facade.debug_mode is False
        assert facade.compress_images is True
        assert facade.jpeg_quality == 85
        mock_engine.init_engine.assert_called_once()

    @patch("paddle_ocr_facade.OCREngineManager")
    @patch("paddleocr_toolkit.processors.hybrid_processor.HybridPDFProcessor")
    def test_init_hybrid_mode(self, mock_processor_class, mock_engine_class):
        """測試混合模式初始化"""
        mock_engine = Mock()
        mock_engine.get_mode.return_value = OCRMode.HYBRID
        mock_engine.init_engine = Mock()
        mock_engine_class.return_value = mock_engine

        # Mock processor
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor

        facade = PaddleOCRFacade(mode="hybrid", debug_mode=True)

        assert facade.mode == "hybrid"
        assert facade.debug_mode is True
        assert hasattr(facade, "hybrid_processor")
        # 驗證 processor 被正確初始化
        mock_processor_class.assert_called_once()

    @patch("paddle_ocr_facade.OCREngineManager")
    def test_init_with_custom_settings(self, mock_engine_class):
        """測試自訂設定初始化"""
        mock_engine = Mock()
        mock_engine.get_mode.return_value = OCRMode.BASIC
        mock_engine_class.return_value = mock_engine

        facade = PaddleOCRFacade(
            mode="basic",
            device="gpu",
            compress_images=False,
            jpeg_quality=95,
        )

        assert facade.device == "gpu"
        assert facade.compress_images is False
        assert facade.jpeg_quality == 95


class TestPaddleOCRFacadeProcessHybrid:
    """測試混合模式處理"""

    @patch("paddle_ocr_facade.OCREngineManager")
    @patch("paddleocr_toolkit.processors.hybrid_processor.HybridPDFProcessor")
    def test_process_hybrid_delegation(self, mock_processor_class, mock_engine_class):
        """測試 process_hybrid 委派給 HybridPDFProcessor"""
        mock_engine = Mock()
        mock_engine.get_mode.return_value = OCRMode.HYBRID
        mock_engine.init_engine = Mock()
        mock_engine_class.return_value = mock_engine

        mock_processor = Mock()
        mock_processor.process_pdf.return_value = {"pages_processed": 5}
        mock_processor_class.return_value = mock_processor

        facade = PaddleOCRFacade(mode="hybrid")
        result = facade.process_hybrid("input.pdf", "output.pdf")

        mock_processor.process_pdf.assert_called_once()
        assert result["pages_processed"] == 5

    @patch("paddle_ocr_facade.OCREngineManager")
    def test_process_hybrid_wrong_mode_raises_error(self, mock_engine_class):
        """測試錯誤模式時丟擲異常"""
        mock_engine = Mock()
        mock_engine.get_mode.return_value = OCRMode.BASIC
        mock_engine_class.return_value = mock_engine

        facade = PaddleOCRFacade(mode="basic")

        with pytest.raises(ValueError, match="僅適用於 hybrid 模式"):
            facade.process_hybrid("input.pdf")


class TestPaddleOCRFacadeUnifiedProcess:
    """測試統一處理介面"""

    @patch("paddle_ocr_facade.OCREngineManager")
    @patch("paddleocr_toolkit.processors.hybrid_processor.HybridPDFProcessor")
    def test_process_routes_to_hybrid(self, mock_processor_class, mock_engine_class):
        """測試 process() 正確路由到 hybrid 模式"""
        mock_engine = Mock()
        mock_engine.get_mode.return_value = OCRMode.HYBRID
        mock_engine.init_engine = Mock()
        mock_engine_class.return_value = mock_engine

        mock_processor = Mock()
        mock_processor.process_pdf.return_value = {"mode": "hybrid"}
        mock_processor_class.return_value = mock_processor

        facade = PaddleOCRFacade(mode="hybrid")
        result = facade.process("input.pdf")

        assert result["mode"] == "hybrid"

    @patch("paddle_ocr_facade.OCREngineManager")
    def test_process_unsupported_mode_raises_error(self, mock_engine_class):
        """測試不支援的模式"""
        mock_engine = Mock()
        mock_engine.get_mode.return_value = OCRMode.BASIC
        mock_engine_class.return_value = mock_engine

        facade = PaddleOCRFacade(mode="unknown")

        with pytest.raises(ValueError, match="不支援的模式"):
            facade.process("input.pdf")


class TestPaddleOCRFacadeBackwardCompatibility:
    """測試向後相容性"""

    @patch("paddle_ocr_facade.OCREngineManager")
    def test_get_engine(self, mock_engine_class):
        """測試 get_engine() 方法"""
        mock_engine = Mock()
        mock_engine.get_mode.return_value = OCRMode.BASIC
        mock_real_engine = Mock()
        mock_engine.get_engine.return_value = mock_real_engine
        mock_engine_class.return_value = mock_engine

        facade = PaddleOCRFacade()
        engine = facade.get_engine()

        assert engine == mock_real_engine

    @patch("paddle_ocr_facade.OCREngineManager")
    def test_predict(self, mock_engine_class):
        """測試 predict() 方法"""
        mock_engine = Mock()
        mock_engine.get_mode.return_value = OCRMode.BASIC
        mock_engine.predict.return_value = ["result"]
        mock_engine_class.return_value = mock_engine

        facade = PaddleOCRFacade()
        result = facade.predict("image")

        mock_engine.predict.assert_called_once_with("image")
        assert result == ["result"]

    def test_repr(self):
        """測試字串表示"""
        with patch("paddle_ocr_facade.OCREngineManager") as mock_engine_class:
            mock_engine = Mock()
            mock_engine.init_engine = Mock()
            mock_engine_class.return_value = mock_engine
            
            with patch("paddleocr_toolkit.processors.hybrid_processor.HybridPDFProcessor"):
                facade = PaddleOCRFacade(mode="hybrid", device="gpu")
                repr_str = repr(facade)

                assert "mode=hybrid" in repr_str
                assert "device=gpu" in repr_str
