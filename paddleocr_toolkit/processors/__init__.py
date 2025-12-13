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
from .batch_processor import (
    pdf_to_images_parallel,
    batch_process_images,
    BatchProcessor,
    get_optimal_workers
)
from .stats_collector import (
    PageStats,
    ProcessingStats,
    StatsCollector
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
    # 批次處理
    'pdf_to_images_parallel',
    'batch_process_images',
    'BatchProcessor',
    'get_optimal_workers',
    # 統計收集
    'PageStats',
    'ProcessingStats',
    'StatsCollector',
]


