# -*- coding: utf-8 -*-
"""
paddle_ocr_tool.py - 相容性墊片 (Compatibility Shim)

此檔案用於維持向後相容性。
實際實作已遷移至 paddleocr_toolkit，本檔案僅作為重導向。

使用方式（推薦）：
    from paddle_ocr_facade import PaddleOCRFacade
    
使用方式（相容舊程式碼）：
    from paddle_ocr_tool import PaddleOCRTool  # 自動重導向到 Facade
"""

import sys
import warnings
from typing import Optional

# 發出遷移警告（僅在直接導入時顯示）
warnings.warn(
    "paddle_ocr_tool 已棄用，請改用 paddle_ocr_facade。" "此模組將在未來版本移除。",
    DeprecationWarning,
    stacklevel=2,
)

# 1. 從 Facade 重新匯出核心類別
try:
    from paddle_ocr_facade import PaddleOCRFacade
    from paddle_ocr_facade import PaddleOCRFacade as PaddleOCRTool

    HAS_FACADE = True
except ImportError:
    HAS_FACADE = False

# 2. 重新匯出輔助函式 (Shim implementation)
try:
    from paddleocr_toolkit.cli.main import main as _cli_main
    from paddleocr_toolkit.core.logging_utils import setup_logging
    from paddleocr_toolkit.processors.image_preprocessor import resize_image_if_needed

    HAS_TOOLKIT = True
    HAS_TRANSLATOR = True  # 假設新版總是支援翻譯

    def main():
        """CLI 主入口 shim"""
        sys.exit(_cli_main())

except ImportError:
    # 如果 Toolkit 未安裝，提供最小化 fallback
    HAS_TOOLKIT = False
    HAS_TRANSLATOR = False

    def main():
        """主程式入口 (Fallback)"""
        raise NotImplementedError("請使用 python -m paddleocr_toolkit 或安裝完整套件")

    def setup_logging(log_file: Optional[str] = None):
        """日誌設定 (Fallback)"""
        import logging

        logging.basicConfig(level=logging.INFO)

    def resize_image_if_needed(file_path: str, max_side: int = 2500):
        """圖片縮放 (Fallback)"""
        return file_path, False


__all__ = [
    "PaddleOCRTool",
    "PaddleOCRFacade",
    "HAS_TRANSLATOR",
    "main",
    "setup_logging",
    "resize_image_if_needed",
]
