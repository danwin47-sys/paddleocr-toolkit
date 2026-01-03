# -*- coding: utf-8 -*-
"""
浮水印去除插件
範例插件：偵測並移除灰色浮水印
"""
import cv2
import numpy as np
from typing import Any
from paddleocr_toolkit.plugins.base import PreprocessorPlugin


class WatermarkRemoverPlugin(PreprocessorPlugin):
    name = "Watermark Remover"
    version = "1.0.0"
    author = "PaddleOCR Team"
    description = "去除淺色浮水印以提升 OCR 準確度"

    def on_init(self) -> bool:
        self.logger.info("Watermark Remover 插件已載入")
        return True

    def on_before_ocr(self, image: np.ndarray) -> np.ndarray:
        """
        對輸入圖片進行去浮水印處理
        """
        if image is None:
            return image

        # 轉灰階
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # 簡單的亮度門檻濾除 (針對淺色浮水印)
        # 將接近白色的淺灰色 (200-250) 轉為白色 (255)
        # 將深色文字保留
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

        # 簡單的形態學操作去除噪點
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        # 轉回 BGR
        if len(image.shape) == 3:
            result = cv2.cvtColor(cleaned, cv2.COLOR_GRAY2BGR)
        else:
            result = cleaned

        self.logger.info("已執行浮水印去除預處理")
        return result
