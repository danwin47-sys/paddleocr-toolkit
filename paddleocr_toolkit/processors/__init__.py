# -*- coding: utf-8 -*-
"""PaddleOCR Toolkit - Processors 模組"""

from .batch_processor import (BatchProcessor, batch_process_images,
                              get_optimal_workers, pdf_to_images_parallel)
from .glossary_manager import (GlossaryEntry, GlossaryManager,
                               create_sample_glossary)
from .image_preprocessor import (auto_preprocess, binarize, denoise, deskew,
                                 enhance_contrast, preprocess_for_ocr, sharpen)
from .ocr_workaround import (OCRWorkaround, TextBlock, detect_scanned_document,
                             should_use_ocr_workaround)
from .pdf_quality import detect_pdf_quality
from .stats_collector import PageStats, ProcessingStats, StatsCollector
from .text_processor import MERGE_TERMS, PROTECTED_TERMS, fix_english_spacing

__all__ = [
    # 文字處理
    "fix_english_spacing",
    "MERGE_TERMS",
    "PROTECTED_TERMS",
    # PDF 品質
    "detect_pdf_quality",
    # 圖片預處理
    "enhance_contrast",
    "denoise",
    "binarize",
    "deskew",
    "sharpen",
    "preprocess_for_ocr",
    "auto_preprocess",
    # 批次處理
    "pdf_to_images_parallel",
    "batch_process_images",
    "BatchProcessor",
    "get_optimal_workers",
    # 統計收集
    "PageStats",
    "ProcessingStats",
    "StatsCollector",
    # 術語表
    "GlossaryManager",
    "GlossaryEntry",
    "create_sample_glossary",
    # OCR 補救
    "OCRWorkaround",
    "TextBlock",
    "detect_scanned_document",
    "should_use_ocr_workaround",
]
