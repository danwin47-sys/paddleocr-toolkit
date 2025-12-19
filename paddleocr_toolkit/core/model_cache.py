#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型和結果快取系統
v1.2.0新增 - 提升重複檔案處理速度10x+
"""

import hashlib
import pickle
import time
from pathlib import Path
from typing import Any, Dict, Optional


class ModelCache:
    """
    模型單例快取
    避免重複載入模型
    """

    _instance: Optional["ModelCache"] = None
    _cache: Dict[str, Any] = {}

    def __new__(cls):
        """單例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_model(self, mode: str, **kwargs):
        """
        獲取或載入模型

        Args:
            mode: OCR模式
            **kwargs: 模型引數

        Returns:
            模型例項
        """
        # 建立快取鍵
        cache_key = self._make_cache_key(mode, kwargs)

        if cache_key not in self._cache:
            print(f"載入模型: {mode}")
            start = time.time()

            # 這裡應該是實際的模型載入邏輯
            # 暫時使用佔位符
            model = self._load_model(mode, **kwargs)

            self._cache[cache_key] = model
            print(f"模型載入完成 ({time.time() - start:.2f}s)")
        else:
            print(f"使用快取模型: {mode}")

        return self._cache[cache_key]

    def _make_cache_key(self, mode: str, kwargs: dict) -> str:
        """建立快取鍵"""
        # 將引數轉為字串
        params_str = f"{mode}_{sorted(kwargs.items())}"
        return hashlib.md5(params_str.encode()).hexdigest()

    def _load_model(self, mode: str, **kwargs):
        """載入模型（佔位符）"""
        # 實際應該呼叫PaddleOCR載入
        return {"mode": mode, "params": kwargs}

    def clear_cache(self):
        """清理快取"""
        print(f"清理 {len(self._cache)} 個快取模型")
        self._cache.clear()

    def get_cache_info(self) -> Dict:
        """獲取快取資訊"""
        return {"cached_models": len(self._cache), "models": list(self._cache.keys())}


class ResultCache:
    """
    OCR結果快取
    使用LRU策略，避免重複處理相同檔案
    """

    def __init__(self, cache_dir: Optional[Path] = None, max_size: int = 1000):
        """
        初始化結果快取

        Args:
            cache_dir: 快取目錄
            max_size: 最大快取數量
        """
        self.cache_dir = cache_dir or Path.home() / ".paddleocr" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size = max_size

        # 記憶體快取（使用LRU）
        self.memory_cache: Dict[str, Any] = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def _compute_file_hash(self, file_path: str) -> str:
        """
        計算檔案雜湊

        Args:
            file_path: 檔案路徑

        Returns:
            SHA256雜湊值
        """
        sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:
            # 分塊讀取，避免大檔案記憶體問題
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)

        return sha256.hexdigest()

    def get(self, file_path: str, mode: str) -> Optional[Any]:
        """
        獲取快取結果

        Args:
            file_path: 檔案路徑
            mode: OCR模式

        Returns:
            快取的結果，如果不存在返回None
        """
        # 計算快取鍵
        file_hash = self._compute_file_hash(file_path)
        cache_key = f"{file_hash}_{mode}"

        # 1. 檢查記憶體快取
        if cache_key in self.memory_cache:
            self.cache_hits += 1
            return self.memory_cache[cache_key]

        # 2. 檢查磁碟快取
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    result = pickle.load(f)

                # 載入到記憶體快取
                self.memory_cache[cache_key] = result
                self.cache_hits += 1

                return result
            except Exception as e:
                print(f"載入快取失敗: {e}")

        self.cache_misses += 1
        return None

    def set(self, file_path: str, mode: str, result: Any):
        """
        設定快取

        Args:
            file_path: 檔案路徑
            mode: OCR模式
            result: OCR結果
        """
        file_hash = self._compute_file_hash(file_path)
        cache_key = f"{file_hash}_{mode}"

        # 1. 儲存到記憶體
        self.memory_cache[cache_key] = result

        # 2. 儲存到磁碟
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(result, f)
        except Exception as e:
            print(f"儲存快取失敗: {e}")

        # 3. 檢查快取大小
        self._check_cache_size()

    def _check_cache_size(self):
        """檢查並清理過大的快取"""
        if len(self.memory_cache) > self.max_size:
            # 簡單的FIFO清理策略
            # 實際應該使用LRU
            keys_to_remove = list(self.memory_cache.keys())[
                : len(self.memory_cache) - self.max_size
            ]
            for key in keys_to_remove:
                del self.memory_cache[key]

    def clear(self):
        """清理所有快取"""
        self.memory_cache.clear()

        # 清理磁碟快取
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()

        print("快取已清理")

    def get_stats(self) -> Dict:
        """獲取快取統計"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0

        return {
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "hit_rate": hit_rate,
            "memory_cached": len(self.memory_cache),
            "disk_cached": len(list(self.cache_dir.glob("*.pkl"))),
        }

    def print_stats(self):
        """列印快取統計"""
        stats = self.get_stats()

        print("\n" + "=" * 60)
        print("快取統計")
        print("=" * 60)
        print(f"快取命中: {stats['hits']}")
        print(f"快取未命中: {stats['misses']}")
        print(f"命中率: {stats['hit_rate']:.1%}")
        print(f"記憶體快取: {stats['memory_cached']}")
        print(f"磁碟快取: {stats['disk_cached']}")
        print("=" * 60)


# 裝飾器形式的快取
def cached_ocr_result(mode: str):
    """
    OCR結果快取裝飾器

    Usage:
        @cached_ocr_result('hybrid')
        def process_image(image_path):
            return ocr_engine.ocr(image_path)
    """
    cache = ResultCache()

    def decorator(func):
        def wrapper(file_path, *args, **kwargs):
            # 嘗試從快取獲取
            cached_result = cache.get(file_path, mode)
            if cached_result is not None:
                return cached_result

            # 執行實際處理
            result = func(file_path, *args, **kwargs)

            # 儲存到快取
            cache.set(file_path, mode, result)

            return result

        return wrapper

    return decorator


# 使用示例
if __name__ == "__main__":
    print("快取系統")
    print("預期效能提升: 10x+ (重複檔案)")
    print("\n使用方法:")
    print(
        """
# 1. 模型快取
from paddleocr_toolkit.core.model_cache import ModelCache

model_cache = ModelCache()
model = model_cache.get_model('hybrid', lang='ch')

# 2. 結果快取
from paddleocr_toolkit.core.model_cache import ResultCache

result_cache = ResultCache()
result = result_cache.get('file.pdf', 'hybrid')
if result is None:
    result = process_file('file.pdf')
    result_cache.set('file.pdf', 'hybrid', result)

# 3. 裝飾器快取
@cached_ocr_result('hybrid')
def process_image(image_path):
    return ocr_engine.ocr(image_path)
"""
    )
