# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - 資料模型

定義 OCR 結果和模式的資料結構。
"""

from dataclasses import dataclass
from enum import Enum
from typing import List


class OCRMode(Enum):
    """OCR 模式枚舉"""

    BASIC = "basic"  # PP-OCRv5 基本文字識別
    STRUCTURE = "structure"  # PP-StructureV3 結構化文件解析
    VL = "vl"  # PaddleOCR-VL 視覺語言模型
    FORMULA = "formula"  # PP-FormulaNet 公式識別
    HYBRID = "hybrid"  # 混合模式：版面分析 + 精確 OCR


@dataclass
class OCRResult:
    """OCR 辨識結果資料結構"""

    text: str  # 辨識的文字
    confidence: float  # 信賴度 (0-1)
    bbox: List[List[float]]  # 邊界框座標 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]

    @property
    def x(self) -> float:
        """左上角 X 座標"""
        return min(p[0] for p in self.bbox)

    @property
    def y(self) -> float:
        """左上角 Y 座標"""
        return min(p[1] for p in self.bbox)

    @property
    def width(self) -> float:
        """邊界框寬度"""
        xs = [p[0] for p in self.bbox]
        return max(xs) - min(xs)

    @property
    def height(self) -> float:
        """邊界框高度"""
        ys = [p[1] for p in self.bbox]
        return max(ys) - min(ys)


# 支援的檔案格式
SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
SUPPORTED_PDF_FORMAT = ".pdf"
