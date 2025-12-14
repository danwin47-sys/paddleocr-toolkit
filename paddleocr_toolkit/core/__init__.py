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
from .config_loader import (
    load_config,
    save_config,
    apply_config_to_args,
    get_config_value,
    DEFAULT_CONFIG,
)

# 性能優化工具（可選）
try:
    from .streaming_utils import (
        open_pdf_context,
        pdf_pages_generator,
        batch_pages_generator,
        StreamingPDFProcessor,
    )
    from .buffered_writer import (
        BufferedWriter,
        BufferedJSONWriter,
        write_text_efficient,
        write_json_efficient,
    )
    HAS_PERF_TOOLS = True
except ImportError:
    HAS_PERF_TOOLS = False

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
    # 設定檔
    'load_config',
    'save_config',
    'apply_config_to_args',
    'get_config_value',
    'DEFAULT_CONFIG',
]

# 添加性能優化工具（如果可用）
if HAS_PERF_TOOLS:
    __all__.extend([
        # 串流處理
        'open_pdf_context',
        'pdf_pages_generator',
        'batch_pages_generator',
        'StreamingPDFProcessor',
        # 緩衝寫入
        'BufferedWriter',
        'BufferedJSONWriter',
        'write_text_efficient',
        'write_json_efficient',
    ])
