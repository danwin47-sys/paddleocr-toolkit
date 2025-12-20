# -*- coding: utf-8 -*-
"""
paddle_ocr_tool.py - 相容性墊片 (Compatibility Shim)

此檔案用於維持向後相容性。
實際實作已遷移至 paddle_ocr_facade.py，本檔案僅作為重導向。

使用方式（推薦）：
    from paddle_ocr_facade import PaddleOCRFacade
    
使用方式（相容舊程式碼）：
    from paddle_ocr_tool import PaddleOCRTool  # 自動重導向到 Facade
"""

import warnings

# 發出遷移警告（僅在直接導入時顯示）
warnings.warn(
    "paddle_ocr_tool 已棄用，請改用 paddle_ocr_facade。"
    "此模組將在未來版本移除。",
    DeprecationWarning,
    stacklevel=2
)

# 從 Facade 重新匯出所有公開介面
from paddle_ocr_facade import PaddleOCRFacade as PaddleOCRTool
from paddle_ocr_facade import PaddleOCRFacade

# 從 legacy 模組匯出可能需要的其他符號
try:
    from legacy.paddle_ocr_tool import (
        HAS_TRANSLATOR,
        main,
        setup_logging,
        resize_image_if_needed,
    )
except ImportError:
    # 如果 legacy 模組不可用，提供預設值
    HAS_TRANSLATOR = False
    
    def main():
        """主程式入口（已遷移至 Facade）"""
        raise NotImplementedError(
            "請使用 python -m paddleocr_toolkit 或直接使用 PaddleOCRFacade"
        )
    
    def setup_logging(*args, **kwargs):
        """日誌設定（已遷移）"""
        import logging
        logging.basicConfig(level=logging.INFO)
    
    def resize_image_if_needed(file_path, max_side=2500):
        """圖片縮放（請使用 image_preprocessor）"""
        return file_path, False

__all__ = [
    "PaddleOCRTool",
    "PaddleOCRFacade", 
    "HAS_TRANSLATOR",
    "main",
    "setup_logging",
    "resize_image_if_needed",
]
