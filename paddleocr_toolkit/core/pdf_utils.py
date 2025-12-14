# -*- coding: utf-8 -*-
"""
PDF 工具函數 - 共用的 PDF 處理邏輯

本模組提供重複使用的 PDF 處理功能，包括：
- Pixmap ↔ numpy 轉換
- numpy → PDF 頁面
- PDF 頁面轉圖片
"""

import io
import logging
from typing import Optional, Tuple

import numpy as np

try:
    import fitz  # PyMuPDF

    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    from PIL import Image

    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def pixmap_to_numpy(pixmap: "fitz.Pixmap", copy: bool = True) -> np.ndarray:
    """
    將 PyMuPDF Pixmap 轉換為 numpy 陣列 (RGB)

    Args:
        pixmap: PyMuPDF Pixmap 物件
        copy: 是否複製陣列（True 避免記憶體問題）

    Returns:
        numpy.ndarray: RGB 格式的圖片陣列 (H, W, 3)
    """
    img_array = np.frombuffer(pixmap.samples, dtype=np.uint8)
    img_array = img_array.reshape(pixmap.height, pixmap.width, pixmap.n)

    # RGBA → RGB
    if pixmap.n == 4:
        img_array = img_array[:, :, :3]

    if copy:
        img_array = img_array.copy()

    return img_array


def page_to_numpy(page: "fitz.Page", dpi: int = 150, copy: bool = True) -> np.ndarray:
    """
    將 PDF 頁面轉換為 numpy 陣列

    Args:
        page: PyMuPDF Page 物件
        dpi: 解析度（預設 150）
        copy: 是否複製陣列

    Returns:
        numpy.ndarray: RGB 格式的圖片陣列 (H, W, 3)
    """
    scale = dpi / 72.0
    matrix = fitz.Matrix(scale, scale)
    pixmap = page.get_pixmap(matrix=matrix)
    return pixmap_to_numpy(pixmap, copy=copy)


def numpy_to_pdf_bytes(
    image: np.ndarray, format: str = "PNG", jpeg_quality: int = 85
) -> io.BytesIO:
    """
    將 numpy 陣列轉換為圖片 bytes（用於插入 PDF）

    Args:
        image: numpy 陣列圖片
        format: 圖片格式（"PNG" 或 "JPEG"）
        jpeg_quality: JPEG 品質（0-100）

    Returns:
        io.BytesIO: 圖片 bytes 流
    """
    if not HAS_PIL:
        raise ImportError("Pillow 未安裝")

    pil_image = Image.fromarray(image)
    img_bytes = io.BytesIO()

    if format.upper() == "JPEG":
        # 確保是 RGB 模式
        if pil_image.mode == "RGBA":
            pil_image = pil_image.convert("RGB")
        pil_image.save(img_bytes, format="JPEG", quality=jpeg_quality)
    else:
        pil_image.save(img_bytes, format="PNG")

    img_bytes.seek(0)
    return img_bytes


def add_image_page(
    doc: "fitz.Document", image: np.ndarray, compress: bool = False, jpeg_quality: int = 85
) -> "fitz.Page":
    """
    將 numpy 陣列添加為 PDF 的新頁面

    Args:
        doc: PyMuPDF Document 物件
        image: numpy 陣列圖片
        compress: 是否使用 JPEG 壓縮
        jpeg_quality: JPEG 品質（0-100）

    Returns:
        fitz.Page: 新建立的頁面
    """
    if not HAS_FITZ:
        raise ImportError("PyMuPDF 未安裝")
    if not HAS_PIL:
        raise ImportError("Pillow 未安裝")

    pil_image = Image.fromarray(image)

    # 轉換為 bytes
    format_str = "JPEG" if compress else "PNG"
    img_bytes = numpy_to_pdf_bytes(image, format=format_str, jpeg_quality=jpeg_quality)

    # 建立頁面
    img_rect = fitz.Rect(0, 0, pil_image.width, pil_image.height)
    page = doc.new_page(width=img_rect.width, height=img_rect.height)
    page.insert_image(img_rect, stream=img_bytes.read())

    return page


def get_dpi_matrix(dpi: int = 150) -> "fitz.Matrix":
    """
    取得指定 DPI 的縮放矩陣

    Args:
        dpi: 目標解析度

    Returns:
        fitz.Matrix: 縮放矩陣
    """
    if not HAS_FITZ:
        raise ImportError("PyMuPDF 未安裝")

    scale = dpi / 72.0
    return fitz.Matrix(scale, scale)


def open_pdf(pdf_path: str) -> "fitz.Document":
    """
    開啟 PDF 檔案

    Args:
        pdf_path: PDF 檔案路徑

    Returns:
        fitz.Document: PDF 文件物件
    """
    if not HAS_FITZ:
        raise ImportError("PyMuPDF 未安裝")

    return fitz.open(pdf_path)


def create_pdf() -> "fitz.Document":
    """
    建立新的空白 PDF

    Returns:
        fitz.Document: 空白 PDF 文件物件
    """
    if not HAS_FITZ:
        raise ImportError("PyMuPDF 未安裝")

    return fitz.open()


def get_page_size(page: "fitz.Page") -> Tuple[float, float]:
    """
    取得頁面尺寸

    Args:
        page: PyMuPDF Page 物件

    Returns:
        Tuple[float, float]: (寬度, 高度)
    """
    rect = page.rect
    return (rect.width, rect.height)


def copy_page(src_doc: "fitz.Document", dst_doc: "fitz.Document", page_num: int) -> "fitz.Page":
    """
    複製頁面到另一個文件

    Args:
        src_doc: 來源文件
        dst_doc: 目標文件
        page_num: 頁碼（0-indexed）

    Returns:
        fitz.Page: 新建立的頁面
    """
    dst_doc.insert_pdf(src_doc, from_page=page_num, to_page=page_num)
    return dst_doc[-1]
