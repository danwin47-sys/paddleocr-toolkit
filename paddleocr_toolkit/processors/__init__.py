# -*- coding: utf-8 -*-
"""PaddleOCR Toolkit - Processors 模組"""

from .text_processor import fix_english_spacing, MERGE_TERMS, PROTECTED_TERMS
from .pdf_quality import detect_pdf_quality
from .image_preprocessor import (
    enhance_contrast,
    denoise,
    binarize,
    deskew,
    sharpen,
    preprocess_for_ocr,
    auto_preprocess
)

__all__ = [
    # 文字處理
    'fix_english_spacing',
    'MERGE_TERMS',
    'PROTECTED_TERMS',
    # PDF 品質
    'detect_pdf_quality',
    # 圖片預處理
    'enhance_contrast',
    'denoise',
    'binarize',
    'deskew',
    'sharpen',
    'preprocess_for_ocr',
    'auto_preprocess',
]
