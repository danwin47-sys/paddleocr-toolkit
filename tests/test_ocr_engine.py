# -*- coding: utf-8 -*-
"""
OCR 引擎管理器測試
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from paddleocr_toolkit.core.ocr_engine import (
    OCREngineManager,
    OCRMode
)


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
            use_doc_unwarping=True
        )
        
        assert manager.mode == OCRMode.HYBRID
        assert manager.config['use_doc_orientation_classify'] is True
        assert manager.config['use_doc_unwarping'] is True
    
    @patch('paddleocr_toolkit.core.ocr_engine.PaddleOCR')
    def test_init_basic_engine(self, mock_ocr):
        """測試初始化基本引擎"""
        manager = OCREngineManager(mode="basic")
        manager.init_engine()
        
        assert manager.is_initialized()
        assert mock_ocr.called
    
    def test_predict_without_init(self):
        """測試未初始化時預測"""
        manager = OCREngineManager()
        
        with pytest.raises(RuntimeError, match="引擎未初始化"):
            manager.predict("test.jpg")
    
    @patch('paddleocr_toolkit.core.ocr_engine.PaddleOCR')
    def test_predict_after_init(self, mock_ocr):
        """測試初始化後預測"""
        mock_engine = Mock()
        mock_engine.predict.return_value = [["test", 0.95]]
        mock_ocr.return_value = mock_engine
        
        manager = OCREngineManager(mode="basic")
        manager.init_engine()
        result = manager.predict("test.jpg")
        
        assert mock_engine.predict.called
    
    @patch('paddleocr_toolkit.core.ocr_engine.PaddleOCR')
    def test_context_manager(self, mock_ocr):
        """測試 context manager"""
        with OCREngineManager(mode="basic") as manager:
            assert manager.is_initialized()
        
        # 退出後應該關閉
        assert not manager.is_initialized()
    
    def test_get_mode(self):
        """測試獲取模式"""
        manager = OCREngineManager(mode="structure")
        assert manager.get_mode() == OCRMode.STRUCTURE
    
    @patch('paddleocr_toolkit.core.ocr_engine.PaddleOCR')
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
    
    @patch('paddleocr_toolkit.core.ocr_engine.PaddleOCR')
    def test_close(self, mock_ocr):
        """測試關閉引擎"""
        manager = OCREngineManager()
        manager.init_engine()
        
        assert manager.is_initialized()
        
        manager.close()
        
        assert not manager.is_initialized()
        assert manager.engine is None
    
    def test_repr(self):
        """測試字串表示"""
        manager = OCREngineManager(mode="basic", device="gpu")
        repr_str = repr(manager)
        
        assert "OCREngineManager" in repr_str
        assert "basic" in repr_str
        assert "gpu" in repr_str
        assert "not initialized" in repr_str


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
