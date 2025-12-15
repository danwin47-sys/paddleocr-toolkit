# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - CLI 命令列介面模組

此模組提供命令列介面相關功能：
- argument_parser: 命令列參數解析
- output_manager: 輸出路徑管理
- config_handler: 設定檔處理
- mode_processor: 模式處理器
"""

from .argument_parser import create_argument_parser
from .config_handler import (
    load_and_merge_config,
    load_config_file,
    process_args_overrides,
)
from .mode_processor import ModeProcessor
from .output_manager import OutputPathManager

__all__ = [
    "create_argument_parser",
    "OutputPathManager",
    "load_and_merge_config",
    "load_config_file",
    "process_args_overrides",
    "ModeProcessor",
]
