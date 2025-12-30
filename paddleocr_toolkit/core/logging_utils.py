# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - 日誌工具
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(log_file: Optional[str] = None) -> str:
    """
    設定日誌記錄
    
    Args:
        log_file: 指定日誌檔案路徑，若未指定則自動生成
        
    Returns:
        str: 日誌檔案路徑
    """
    if log_file is None:
        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = str(
            log_dir
            / f"paddle_ocr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )

    # 移除現有的所有 handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # 創建檔案 handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="w")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )

    # 創建控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )

    # 設定 root logger
    logging.root.setLevel(logging.INFO)
    logging.root.addHandler(file_handler)
    logging.root.addHandler(console_handler)

    # 立即寫入第一條記錄
    logging.info(f"=" * 60)
    logging.info(f"日誌檔案：{log_file}")
    logging.info(f"=" * 60)

    # 強制 flush
    for handler in logging.root.handlers:
        handler.flush()

    return log_file
