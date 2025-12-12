# -*- coding: utf-8 -*-
"""PaddleOCR Toolkit - Processors 模組"""

from .text_processor import fix_english_spacing, MERGE_TERMS, PROTECTED_TERMS
from .pdf_quality import detect_pdf_quality

__all__ = [
    'fix_english_spacing',
    'detect_pdf_quality',
    'MERGE_TERMS',
    'PROTECTED_TERMS',
]
