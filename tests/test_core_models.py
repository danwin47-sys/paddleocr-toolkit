# -*- coding: utf-8 -*-
"""
核心模組單元測試
"""

import pytest
import sys
import os

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paddleocr_toolkit.core.models import OCRResult, OCRMode


class TestOCRResult:
    """測試 OCRResult 資料結構"""
    
    def test_basic_creation(self):
        """測試基本建立"""
        result = OCRResult(
            text="Hello World",
            confidence=0.95,
            bbox=[[0, 0], [100, 0], [100, 20], [0, 20]]
        )
        assert result.text == "Hello World"
        assert result.confidence == 0.95
    
    def test_x_property(self):
        """測試 x 屬性"""
        result = OCRResult(
            text="Test",
            confidence=0.9,
            bbox=[[10, 20], [110, 20], [110, 40], [10, 40]]
        )
        assert result.x == 10
    
    def test_y_property(self):
        """測試 y 屬性"""
        result = OCRResult(
            text="Test",
            confidence=0.9,
            bbox=[[10, 20], [110, 20], [110, 40], [10, 40]]
        )
        assert result.y == 20
    
    def test_width_property(self):
        """測試 width 屬性"""
        result = OCRResult(
            text="Test",
            confidence=0.9,
            bbox=[[10, 20], [110, 20], [110, 40], [10, 40]]
        )
        assert result.width == 100
    
    def test_height_property(self):
        """測試 height 屬性"""
        result = OCRResult(
            text="Test",
            confidence=0.9,
            bbox=[[10, 20], [110, 20], [110, 40], [10, 40]]
        )
        assert result.height == 20


class TestOCRMode:
    """測試 OCRMode 枚舉"""
    
    def test_basic_mode(self):
        """測試 basic 模式"""
        assert OCRMode.BASIC.value == "basic"
    
    def test_structure_mode(self):
        """測試 structure 模式"""
        assert OCRMode.STRUCTURE.value == "structure"
    
    def test_hybrid_mode(self):
        """測試 hybrid 模式"""
        assert OCRMode.HYBRID.value == "hybrid"
    
    def test_all_modes(self):
        """測試所有模式存在"""
        modes = [m.value for m in OCRMode]
        assert "basic" in modes
        assert "structure" in modes
        assert "vl" in modes
        assert "formula" in modes
        assert "hybrid" in modes


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
