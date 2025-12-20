# -*- coding: utf-8 -*-
"""
OCR 快取管理模組
基於檔案雜湊 (MD5) 儲存與檢索 OCR 結果
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Optional


class OCRCache:
    """
    OCR 結果快取類別
    """
    
    def __init__(self, cache_dir: str = ".cache/ocr_results"):
        """
        初始化快取
        
        Args:
            cache_dir: 快取檔案儲存目錄
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_file_hash(self, file_path: str) -> str:
        """
        計算檔案的 MD5 雜湊值
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get(self, file_path: str, mode: str) -> Optional[Any]:
        """
        從快取中取得結果
        
        Args:
            file_path: 檔案路徑
            mode: OCR 模式（模式不同結果可能不同，因此也納入 key）
            
        Returns:
            Optional[Any]: 快取的結果或 None
        """
        try:
            file_hash = self._get_file_hash(file_path)
            cache_file = self.cache_dir / f"{file_hash}_{mode}.json"
            
            if cache_file.exists():
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return None
        except Exception:
            return None
            
    def set(self, file_path: str, mode: str, result: Any):
        """
        將結果寫入快取
        
        Args:
            file_path: 檔案路徑
            mode: OCR 模式
            result: 要儲存的結果
        """
        try:
            file_hash = self._get_file_hash(file_path)
            cache_file = self.cache_dir / f"{file_hash}_{mode}.json"
            
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

# 全域單例
ocr_cache = OCRCache()
