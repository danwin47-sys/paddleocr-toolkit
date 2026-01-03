# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - 配置管理模組

使用 Pydantic 管理所有環境變數和配置。
"""

import os
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 加載 .env 檔案
load_dotenv()


class Settings(BaseModel):
    """
    全域配置類別
    """

    # API 設置
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # OCR 設置
    OCR_DEVICE: str = os.getenv("OCR_DEVICE", "cpu")
    USE_GPU: bool = os.getenv("USE_GPU", "false").lower() == "true"
    OCR_WORKERS: int = int(os.getenv("OCR_WORKERS", "1"))

    # 路徑設置
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    CACHE_DIR: Path = BASE_DIR / ".cache"
    LOG_DIR: Path = BASE_DIR / "logs"

    # 外部 API 密鑰
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    CLAUDE_API_KEY: Optional[str] = os.getenv("CLAUDE_API_KEY")

    # 日誌設置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        arbitrary_types_allowed = True


# 創建全域配置實例
settings = Settings()

# 確保目錄存在
for directory in [
    settings.UPLOAD_DIR,
    settings.OUTPUT_DIR,
    settings.CACHE_DIR,
    settings.LOG_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)

# 初始化日誌檔案（避免健康檢查警告）
log_file = settings.LOG_DIR / "paddleocr.log"
if not log_file.exists():
    log_file.touch()
    print(f"✅ Created log file: {log_file}")
