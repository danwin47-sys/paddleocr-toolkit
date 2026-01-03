"""統一日誌配置模組

這個模組提供了一個統一的日誌配置系統，取代散落各處的 print() 語句。

使用範例:
    from paddleocr_toolkit.utils.logger import logger
    
    logger.info("Processing file: %s", filename)
    logger.warning("Large file detected: %d MB", size_mb)
    logger.error("Failed to process: %s", error_msg)
"""
import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "paddleocr_toolkit",
    level: str = "INFO",
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """
    設置統一的日誌格式

    Args:
        name: Logger 名稱
        level: 日誌級別 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 可選的日誌文件路徑

    Returns:
        配置好的 Logger 實例
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # 防止重複添加 handler
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # 格式化器
    formatter = logging.Formatter(
        "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (可選)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 全局 logger 實例
logger = setup_logger()


__all__ = ["logger", "setup_logger"]
