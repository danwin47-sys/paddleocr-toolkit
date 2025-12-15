# -*- coding: utf-8 -*-
"""
OCR 引擎管理器測試
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from paddleocr_toolkit.core.ocr_engine import OCREngineManager, OCRMode


class TestOCREngineManager:
    """測試 OCR 引擎管理器"""

    def test_init_basic(self):
        """測試基本初始化"""
        manager = OCREngineManager(mode="basic", device="cpu")

        assert manager.mode == OCRMode.BASIC
        assert manager.device == "cpu"
        assert not manager.is_initialized()

    def test_init_with_options(self):
        """測試帶選項的初始化"""
        manager = OCREngineManager(
            mode="hybrid",
            device="gpu",
            use_orientation_classify=True,
            use_doc_unwarping=True,
        )

        assert manager.mode == OCRMode.HYBRID
        assert manager.config["use_doc_orientation_classify"] is True
        assert manager.config["use_doc_unwarping"] is True

    def test_init_with_enum_mode(self):
        """測試使用枚舉模式初始化"""
        manager = OCREngineManager(mode=OCRMode.STRUCTURE)
        assert manager.mode == OCRMode.STRUCTURE

    def test_init_with_custom_kwargs(self):
        """測試自定義kwargs"""
        manager = OCREngineManager(custom_param="value", another_param=123)
        assert manager.config["custom_param"] == "value"
        assert manager.config["another_param"] == 123

    @patch("paddleocr_toolkit.core.ocr_engine.PaddleOCR")
    def test_init_basic_engine(self, mock_ocr):
        """測試初始化基本引擎"""
        manager = OCREngineManager(mode="basic")
        manager.init_engine()

        assert manager.is_initialized()
        assert mock_ocr.called

    @patch("paddleocr_toolkit.core.ocr_engine.PPStructureV3")
    @patch("paddleocr_toolkit.core.ocr_engine.HAS_STRUCTURE", True)
    def test_init_structure_engine(self, mock_structure):
        """測試初始化結構化引擎"""
        manager = OCREngineManager(mode="structure")
        manager.init_engine()

        assert manager.is_initialized()
        mock_structure.assert_called_once()

    @patch("paddleocr_toolkit.core.ocr_engine.HAS_STRUCTURE", False)
    def test_init_structure_without_module(self):
        """測試無結構化模組時的錯誤"""
        manager = OCREngineManager(mode="structure")

        with pytest.raises(ImportError, match="PPStructureV3"):
            manager.init_engine()

    @patch("paddleocr_toolkit.core.ocr_engine.PPStructureV3")
    @patch("paddleocr_toolkit.core.ocr_engine.HAS_STRUCTURE", True)
    def test_init_hybrid_engine(self, mock_structure):
        """測試初始化混合引擎"""
        manager = OCREngineManager(mode="hybrid")
        manager.init_engine()

        assert manager.structure_engine is not None
        assert manager.engine is manager.structure_engine

    @patch("paddleocr_toolkit.core.ocr_engine.HAS_VL", False)
    def test_init_vl_without_module(self):
        """測試無VL模組時的錯誤"""
        manager = OCREngineManager(mode="vl")

        with pytest.raises(ImportError, match="PaddleOCRVL"):
            manager.init_engine()

    @patch("paddleocr_toolkit.core.ocr_engine.HAS_FORMULA", False)
    def test_init_formula_without_module(self):
        """測試無Formula模組時的錯誤"""
        manager = OCREngineManager(mode="formula")

        with pytest.raises(ImportError, match="FormulaRecPipeline"):
            manager.init_engine()

    @patch("paddleocr_toolkit.core.ocr_engine.PaddleOCR")
    def test_double_init_warning(self, mock_ocr):
        """測試重複初始化警告"""
        manager = OCREngineManager()
        manager.init_engine()

        # 第二次初始化應該跳過
        manager.init_engine()

        # 只應該被調用一次
        assert mock_ocr.call_count == 1

    @patch("paddleocr_toolkit.core.ocr_engine.PaddleOCR")
    def test_init_failure(self, mock_ocr):
        """測試初始化失敗"""
        mock_ocr.side_effect = Exception("Init failed")

        manager = OCREngineManager()

        with pytest.raises(Exception, match="Init failed"):
            manager.init_engine()

        assert not manager.is_initialized()

    def test_predict_without_init(self):
        """測試未初始化時預測"""
        manager = OCREngineManager()

        with pytest.raises(RuntimeError, match="引擎未初始化"):
            manager.predict("test.jpg")

    @patch("paddleocr_toolkit.core.ocr_engine.PaddleOCR")
    def test_predict_after_init(self, mock_ocr):
        """測試初始化後預測"""
        mock_engine = Mock()
        mock_engine.predict.return_value = [["test", 0.95]]
        mock_ocr.return_value = mock_engine

        manager = OCREngineManager(mode="basic")
        manager.init_engine()
        result = manager.predict("test.jpg")

        assert mock_engine.predict.called

    @patch("paddleocr_toolkit.core.ocr_engine.PaddleOCR")
    def test_predict_with_kwargs(self, mock_ocr):
        """測試帶kwargs的預測"""
        mock_engine = Mock()
        mock_engine.predict.return_value = []
        mock_ocr.return_value = mock_engine

        manager = OCREngineManager()
        manager.init_engine()
        manager.predict("test.jpg", custom_param="value")

        mock_engine.predict.assert_called_with("test.jpg", custom_param="value")

    @patch("paddleocr_toolkit.core.ocr_engine.PaddleOCR")
    def test_context_manager(self, mock_ocr):
        """測試 context manager"""
        with OCREngineManager(mode="basic") as manager:
            assert manager.is_initialized()

        # 退出後應該關閉
        assert not manager.is_initialized()

    @patch("paddleocr_toolkit.core.ocr_engine.PaddleOCR")
    def test_context_manager_with_exception(self, mock_ocr):
        """測試context manager異常處理"""
        try:
            with OCREngineManager() as manager:
                raise ValueError("Test error")
        except ValueError:
            pass

        # 即使異常也應該關閉
        assert not manager.is_initialized()

    def test_get_mode(self):
        """測試獲取模式"""
        manager = OCREngineManager(mode="structure")
        assert manager.get_mode() == OCRMode.STRUCTURE

    @patch("paddleocr_toolkit.core.ocr_engine.PaddleOCR")
    def test_get_engine(self, mock_ocr):
        """測試獲取引擎"""
        manager = OCREngineManager()

        # 未初始化時應該報錯
        with pytest.raises(RuntimeError):
            manager.get_engine()

        # 初始化後應該可以獲取
        manager.init_engine()
        engine = manager.get_engine()
        assert engine is not None

    @patch("paddleocr_toolkit.core.ocr_engine.PaddleOCR")
    def test_close(self, mock_ocr):
        """測試關閉引擎"""
        manager = OCREngineManager()
        manager.init_engine()

        assert manager.is_initialized()

        manager.close()

        assert not manager.is_initialized()
        assert manager.engine is None

    def test_close_without_init(self):
        """測試未初始化時關閉"""
        manager = OCREngineManager()
        manager.close()  # 不應該報錯

        assert not manager.is_initialized()

    def test_repr(self):
        """測試字串表示"""
        manager = OCREngineManager(mode="basic", device="gpu")
        repr_str = repr(manager)

        assert "OCREngineManager" in repr_str
        assert "basic" in repr_str
        assert "gpu" in repr_str
        assert "not initialized" in repr_str

    @patch("paddleocr_toolkit.core.ocr_engine.PaddleOCR")
    def test_repr_after_init(self, mock_ocr):
        """測試初始化後的字串表示"""
        manager = OCREngineManager()
        manager.init_engine()

        repr_str = repr(manager)
        assert "initialized" in repr_str


class TestOCRMode:
    """測試 OCRMode 枚舉"""

    def test_mode_values(self):
        """測試模式值"""
        assert OCRMode.BASIC.value == "basic"
        assert OCRMode.STRUCTURE.value == "structure"
        assert OCRMode.VL.value == "vl"
        assert OCRMode.FORMULA.value == "formula"
        assert OCRMode.HYBRID.value == "hybrid"

    def test_mode_from_string(self):
        """測試從字串創建模式"""
        mode = OCRMode("basic")
        assert mode == OCRMode.BASIC

    def test_all_modes(self):
        """測試所有模式"""
        modes = list(OCRMode)
        assert len(modes) == 5
        assert OCRMode.BASIC in modes
        assert OCRMode.STRUCTURE in modes
        assert OCRMode.VL in modes
        assert OCRMode.FORMULA in modes
        assert OCRMode.HYBRID in modes
