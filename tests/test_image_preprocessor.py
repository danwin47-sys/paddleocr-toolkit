# -*- coding: utf-8 -*-
"""
Image Preprocessor 單元測試（擴充套件版）
"""

import os
import sys

import numpy as np
import pytest

# 新增專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import cv2

    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

from paddleocr_toolkit.processors.image_preprocessor import (
    auto_preprocess,
    binarize,
    denoise,
    deskew,
    enhance_contrast,
    preprocess_for_ocr,
    sharpen,
)


class TestEnhanceContrast:
    """測試對比度增強"""

    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_basic_enhance(self):
        """測試基本對比度增強"""
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

    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_with_tile_size(self):
        """測試不同 tile size"""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128

        result = enhance_contrast(image, clip_limit=2.0, tile_size=16)

        assert result.shape == image.shape


class TestBinarize:
    """測試二值化"""

    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_simple_binarize(self):
        """測試簡單二值化"""
        image = np.linspace(0, 255, 100 * 100, dtype=np.uint8).reshape(100, 100)

        result = binarize(image, method="simple")

        assert result is not None
        assert result.dtype == np.uint8

    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_adaptive_threshold(self):
        """測試自適應閾值"""
        image = np.ones((100, 100), dtype=np.uint8) * 128
        image[50:, :] = 200

        result = binarize(image, method="adaptive")

        assert result.dtype == np.uint8

    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_otsu_threshold(self):
        """測試 Otsu 閾值"""
        image = np.ones((100, 100), dtype=np.uint8) * 100
        image[50:, :] = 200

        result = binarize(image, method="otsu")

        assert result.dtype == np.uint8

    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_binarize_rgb(self):
        """測試 RGB 圖片二值化"""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128

        result = binarize(image, method="simple")

        assert result is not None


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

    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_sharpen_strength(self):
        """測試銳化強度"""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128

        result = sharpen(image, strength=2.0)

        assert result.shape == image.shape


class TestDenoise:
    """測試去噪"""

    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_basic_denoise(self):
        """測試基本去噪"""
        image = np.random.randint(100, 150, (50, 50, 3), dtype=np.uint8)

        result = denoise(image, strength=5)

        assert result.shape == image.shape

    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_grayscale_denoise(self):
        """測試灰階去噪"""
        image = np.random.randint(100, 150, (50, 50), dtype=np.uint8)

        result = denoise(image, strength=5)

        assert result.shape == image.shape


class TestDeskew:
    """測試傾斜校正"""

    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_basic_deskew(self):
        """測試基本傾斜校正"""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        # 畫一條直線
        cv2.line(image, (10, 10), (90, 90), (0, 0, 0), 2)

        result = deskew(image, max_angle=10.0)

        assert result.shape == image.shape

    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_deskew_no_lines(self):
        """測試沒有線條的圖片"""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 255

        result = deskew(image)

        # 沒有線條時應該返回原圖
        assert result.shape == image.shape

    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_deskew_grayscale_input(self):
        """測試灰階圖片輸入"""
        # 建立灰階圖片
        gray_image = np.ones((100, 100), dtype=np.uint8) * 255
        # 畫一條直線
        cv2.line(gray_image, (10, 10), (90, 90), 0, 2)

        result = deskew(gray_image)

        # 驗證結果
        assert result.shape == gray_image.shape
        # 灰階輸入應返回與輸入相同維度的圖片
        assert len(result.shape) == 2 or (
            len(result.shape) == 3 and result.shape[2] == 3
        )

    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_deskew_small_angle(self):
        """測試小角度（< 0.5 度）不旋轉"""
        # 建立幾乎水平的線條圖片
        image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        # 畫一條幾乎水平的線
        cv2.line(image, (10, 50), (90, 50), (0, 0, 0), 2)

        result = deskew(image)

        # 角度很小時應該直接返回（雖然可能經過處理）
        assert result.shape == image.shape

    def test_deskew_without_cv2(self, monkeypatch):
        """測試缺少 cv2 時的降級行為"""
        # Mock HAS_CV2 = False
        import paddleocr_toolkit.processors.image_preprocessor as module

        monkeypatch.setattr(module, "HAS_CV2", False)

        image = np.ones((100, 100, 3), dtype=np.uint8) * 128

        # 應該返回原圖
        result = deskew(image)
        assert np.array_equal(result, image)


class TestPreprocessForOCR:
    """測試 OCR 預處理管線"""

    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_default_preprocess(self):
        """測試預設預處理"""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128

        result = preprocess_for_ocr(image)

        assert result.shape == image.shape

    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_full_preprocess(self):
        """測試完整預處理"""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128

        result = preprocess_for_ocr(image, enhance=True, sharpen_img=True)

        assert result.shape == image.shape

    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_no_preprocess(self):
        """測試不做預處理"""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128

        result = preprocess_for_ocr(
            image,
            enhance=False,
            denoise_img=False,
            deskew_img=False,
            binarize_img=False,
            sharpen_img=False,
        )

        assert np.array_equal(result, image)

    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_preprocess_with_binarize(self):
        """測試啟用二值化的預處理"""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128

        result = preprocess_for_ocr(image, enhance=True, binarize_img=True)  # 測試這個分支

        assert result is not None
        assert result.shape == image.shape

    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_preprocess_all_options_enabled(self):
        """測試啟用所有預處理選項"""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128

        result = preprocess_for_ocr(
            image,
            enhance=True,
            denoise_img=True,
            deskew_img=True,
            binarize_img=True,
            sharpen_img=True,
        )

        assert result is not None
        assert result.shape == image.shape


class TestAutoPreprocess:
    """測試自動預處理"""

    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_normal_image(self):
        """測試一般圖片"""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128

        result = auto_preprocess(image, is_scanned=False)

        assert result.shape == image.shape

    @pytest.mark.skipif(not HAS_CV2, reason="OpenCV not installed")
    def test_scanned_image(self):
        """測試掃描圖片"""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128

        result = auto_preprocess(image, is_scanned=True)

        assert result.shape == image.shape


class TestMissingDependencies:
    """測試缺少依賴時的降級行為"""

    def test_functions_without_cv2(self, monkeypatch):
        """測試缺少 cv2 時的降級行為"""
        # Mock HAS_CV2 = False
        import paddleocr_toolkit.processors.image_preprocessor as module

        monkeypatch.setattr(module, "HAS_CV2", False)

        image = np.ones((100, 100, 3), dtype=np.uint8) * 128

        # 測試所有函式都返回原圖（降級行為）
        assert np.array_equal(enhance_contrast(image), image)
        assert np.array_equal(denoise(image), image)
        assert np.array_equal(binarize(image), image)
        assert np.array_equal(sharpen(image), image)


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
