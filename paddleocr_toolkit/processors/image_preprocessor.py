# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - 圖片預處理

提供 OCR 前的圖片最佳化功能，以提升識別精度。
"""

import logging

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import cv2

    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


def enhance_contrast(
    image: np.ndarray, clip_limit: float = 2.0, tile_size: int = 8
) -> np.ndarray:
    """
    使用 CLAHE 增強對比度

    Args:
        image: 輸入圖片（BGR 或灰階）
        clip_limit: 對比度限制（預設 2.0）
        tile_size: 區塊大小（預設 8）

    Returns:
        增強後的圖片
    """
    if not HAS_CV2:
        logging.warning("cv2 未安裝，跳過對比度增強")
        return image

    # 轉換為 LAB 色彩空間
    if len(image.shape) == 3:
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # 對 L 通道應用 CLAHE
        clahe = cv2.createCLAHE(
            clipLimit=clip_limit, tileGridSize=(tile_size, tile_size)
        )
        l = clahe.apply(l)

        # 合併通道
        lab = cv2.merge([l, a, b])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    else:
        # 灰階圖片
        clahe = cv2.createCLAHE(
            clipLimit=clip_limit, tileGridSize=(tile_size, tile_size)
        )
        return clahe.apply(image)


def denoise(image: np.ndarray, strength: int = 10) -> np.ndarray:
    """
    去除圖片噪點

    Args:
        image: 輸入圖片
        strength: 去噪強度（預設 10）

    Returns:
        去噪後的圖片
    """
    if not HAS_CV2:
        logging.warning("cv2 未安裝，跳過去噪")
        return image

    if len(image.shape) == 3:
        return cv2.fastNlMeansDenoisingColored(image, None, strength, strength, 7, 21)
    else:
        return cv2.fastNlMeansDenoising(image, None, strength, 7, 21)


def binarize(image: np.ndarray, method: str = "adaptive") -> np.ndarray:
    """
    圖片二值化（適用於掃描件）

    Args:
        image: 輸入圖片
        method: 方法 ("adaptive", "otsu", "simple")

    Returns:
        二值化後的圖片
    """
    if not HAS_CV2:
        logging.warning("cv2 未安裝，跳過二值化")
        return image

    # 轉灰階
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    if method == "adaptive":
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
    elif method == "otsu":
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

    # 轉回 BGR
    return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)


def deskew(image: np.ndarray, max_angle: float = 10.0) -> np.ndarray:
    """
    自動傾斜校正

    Args:
        image: 輸入圖片
        max_angle: 最大校正角度（預設 10 度）

    Returns:
        校正後的圖片
    """
    if not HAS_CV2:
        logging.warning("cv2 未安裝，跳過傾斜校正")
        return image

    # 轉灰階
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # 邊緣偵測
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # 霍夫變換找直線
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

    if lines is None:
        return image

    # 計算平均角度
    angles = []
    for line in lines[: min(20, len(lines))]:
        rho, theta = line[0]
        angle = (theta * 180 / np.pi) - 90
        if abs(angle) < max_angle:
            angles.append(angle)

    if not angles:
        return image

    avg_angle = np.median(angles)

    if abs(avg_angle) < 0.5:  # 幾乎不需要校正
        return image

    # 旋轉圖片
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, avg_angle, 1.0)
    rotated = cv2.warpAffine(
        image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )

    logging.info(f"傾斜校正: {avg_angle:.2f}°")
    return rotated


def sharpen(image: np.ndarray, strength: float = 1.0) -> np.ndarray:
    """
    銳化圖片

    Args:
        image: 輸入圖片
        strength: 銳化強度（預設 1.0）

    Returns:
        銳化後的圖片
    """
    if not HAS_CV2:
        return image

    kernel = np.array([[0, -1, 0], [-1, 5 + strength, -1], [0, -1, 0]])
    return cv2.filter2D(image, -1, kernel)


def preprocess_for_ocr(
    image: np.ndarray,
    enhance: bool = True,
    denoise_img: bool = False,
    deskew_img: bool = False,
    binarize_img: bool = False,
    sharpen_img: bool = False,
) -> np.ndarray:
    """
    OCR 前的圖片預處理管線

    Args:
        image: 輸入圖片（numpy 陣列）
        enhance: 是否增強對比度（預設開啟）
        denoise_img: 是否去噪（預設關閉，會變慢）
        deskew_img: 是否傾斜校正（預設關閉）
        binarize_img: 是否二值化（預設關閉，僅適用掃描件）
        sharpen_img: 是否銳化（預設關閉）

    Returns:
        預處理後的圖片
    """
    result = image.copy()

    # 1. 傾斜校正（最先做）
    if deskew_img:
        result = deskew(result)

    # 2. 對比度增強
    if enhance:
        result = enhance_contrast(result)

    # 3. 去噪
    if denoise_img:
        result = denoise(result)

    # 4. 二值化（僅適用於掃描件）
    if binarize_img:
        result = binarize(result)

    # 5. 銳化
    if sharpen_img:
        result = sharpen(result)

    return result


def auto_preprocess(image: np.ndarray, is_scanned: bool = False) -> np.ndarray:
    """
    根據圖片型別自動選擇預處理方式

    Args:
        image: 輸入圖片
        is_scanned: 是否為掃描件

    Returns:
        預處理後的圖片
    """
    if is_scanned:
        # 掃描件：增強對比 + 去噪
        return preprocess_for_ocr(
            image,
            enhance=True,
            denoise_img=True,
            deskew_img=True,
            binarize_img=False,
            sharpen_img=False,
        )
    else:
        # 一般圖片：僅增強對比
        return preprocess_for_ocr(
            image,
            enhance=True,
            denoise_img=False,
            deskew_img=False,
            binarize_img=False,
            sharpen_img=False,
        )


# ==============================================================================
# 檔案處理擴充功能 (File Handling Utility)
# ==============================================================================

from PIL import Image
from pathlib import Path
from typing import Tuple, Optional

MAX_IMAGE_SIDE = 2500

def resize_image_if_needed(file_path: str, max_side: int = MAX_IMAGE_SIDE) -> Tuple[str, bool]:
    """
    檢測並縮小大圖片以避免 OCR 記憶體問題
    
    Args:
        file_path: 圖片路徑
        max_side: 最大邊長（預設 2500px）
    
    Returns:
        Tuple[str, bool]: (處理後的圖片路徑, 是否有縮小)
    """
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            max_dim = max(width, height)
            
            if max_dim <= max_side:
                return file_path, False
            
            # 計算縮放比例
            scale = max_side / max_dim
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            logging.info(f"圖片太大 ({width}x{height})，自動縮小為 {new_width}x{new_height}")
            
            # 縮小圖片
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 儲存到新檔案
            path = Path(file_path)
            new_path = path.parent / f"{path.stem}_resized{path.suffix}"
            resized_img.save(str(new_path), quality=95)
            
            return str(new_path), True
            
    except Exception as e:
        logging.warning(f"縮小圖片時發生錯誤: {e}，使用原始圖片")
        return file_path, False

