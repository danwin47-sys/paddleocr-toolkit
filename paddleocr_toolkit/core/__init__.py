# -*- coding: utf-8 -*-
"""PaddleOCR Toolkit - Core 模組"""

from .models import OCRResult, OCRMode, SUPPORTED_IMAGE_FORMATS, SUPPORTED_PDF_FORMAT
from .pdf_generator import PDFGenerator
from .pdf_utils import (
    pixmap_to_numpy,
    page_to_numpy,
    numpy_to_pdf_bytes,
    add_image_page,
    get_dpi_matrix,
    open_pdf,
    create_pdf,
    get_page_size,
    copy_page,
)

__all__ = [
    # 資料模型
    'OCRResult',
    'OCRMode',
    'PDFGenerator',
    'SUPPORTED_IMAGE_FORMATS',
    'SUPPORTED_PDF_FORMAT',
    # PDF 工具函數
    'pixmap_to_numpy',
    'page_to_numpy',
    'numpy_to_pdf_bytes',
    'add_image_page',
    'get_dpi_matrix',
    'open_pdf',
    'create_pdf',
    'get_page_size',
    'copy_page',
]
