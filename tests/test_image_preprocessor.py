# -*- coding: utf-8 -*-
"""
Image Preprocessor 單元測試
"""

import pytest
import sys
import os
import numpy as np

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

from paddleocr_toolkit.processors.image_preprocessor import (
    enhance_contrast,
    binarize,
    sharpen,
)


class TestEnhanceContrast:
    """測試對比度增強"""
    
    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_basic_enhance(self):
        """測試基本對比度增強"""
        # 建立灰階圖片
        image = np.ones((100, 100), dtype=np.uint8) * 128
        
        result = enhance_contrast(image, clip_limit=1.5)
        
        assert result.shape == image.shape
        assert result.dtype == np.uint8
    
    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_rgb_enhance(self):
        """測試 RGB 圖片增強"""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        
        result = enhance_contrast(image, clip_limit=1.2)
        
        assert result.shape == image.shape


class TestBinarize:
    """測試二值化"""
    
    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_basic_binarize(self):
        """測試基本二值化"""
        # 建立漸層圖片
        image = np.linspace(0, 255, 100*100, dtype=np.uint8).reshape(100, 100)
        
        result = binarize(image, method="simple")
        
        # 應該有結果
        assert result is not None
        assert result.dtype == np.uint8
    
    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_adaptive_threshold(self):
        """測試自適應閾值"""
        image = np.ones((100, 100), dtype=np.uint8) * 128
        image[50:, :] = 200
        
        result = binarize(image, method="adaptive")
        
        assert result.dtype == np.uint8


class TestSharpen:
    """測試銳化"""
    
    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_basic_sharpen(self):
        """測試基本銳化"""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        
        result = sharpen(image)
        
        assert result.shape == image.shape
        assert result.dtype == np.uint8
    
    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_grayscale_sharpen(self):
        """測試灰階圖片銳化"""
        image = np.ones((100, 100), dtype=np.uint8) * 128
        
        result = sharpen(image)
        
        assert result.shape == image.shape


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
