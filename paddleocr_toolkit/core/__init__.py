# -*- coding: utf-8 -*-
"""PaddleOCR Toolkit - Core 模組"""

from .config_loader import (DEFAULT_CONFIG, apply_config_to_args,
                            get_config_value, load_config, save_config)
from .models import (SUPPORTED_IMAGE_FORMATS, SUPPORTED_PDF_FORMAT, OCRMode,
                     OCRResult)
from .pdf_generator import PDFGenerator
from .pdf_utils import (add_image_page, copy_page, create_pdf, get_dpi_matrix,
                        get_page_size, numpy_to_pdf_bytes, open_pdf,
                        page_to_numpy, pixmap_to_numpy)

# 性能優化工具（可選）
try:
    from .buffered_writer import (BufferedJSONWriter, BufferedWriter,
                                  write_json_efficient, write_text_efficient)
    from .streaming_utils import (StreamingPDFProcessor, batch_pages_generator,
                                  open_pdf_context, pdf_pages_generator)

    HAS_PERF_TOOLS = True
except ImportError:
    HAS_PERF_TOOLS = False

__all__ = [
    # 資料模型
    "OCRResult",
    "OCRMode",
    "PDFGenerator",
    "SUPPORTED_IMAGE_FORMATS",
    "SUPPORTED_PDF_FORMAT",
    # PDF 工具函數
    "pixmap_to_numpy",
    "page_to_numpy",
    "numpy_to_pdf_bytes",
    "add_image_page",
    "get_dpi_matrix",
    "open_pdf",
    "create_pdf",
    "get_page_size",
    "copy_page",
    # 設定檔
    "load_config",
    "save_config",
    "apply_config_to_args",
    "get_config_value",
    "DEFAULT_CONFIG",
]

# 添加性能優化工具（如果可用）
if HAS_PERF_TOOLS:
    __all__.extend(
        [
            # 串流處理
            "open_pdf_context",
            "pdf_pages_generator",
            "batch_pages_generator",
            "StreamingPDFProcessor",
            # 緩衝寫入
            "BufferedWriter",
            "BufferedJSONWriter",
            "write_text_efficient",
            "write_json_efficient",
        ]
    )
