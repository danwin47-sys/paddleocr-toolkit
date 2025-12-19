# -*- coding: utf-8 -*-
"""
模型快取測試
測試 paddleocr_toolkit/core/model_cache.py
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestModelCache:
    """測試模型快取"""

    def test_import_model_cache(self):
        """測試匯入模型快取模組"""
        from paddleocr_toolkit.core.model_cache import ModelCache

        assert ModelCache is not None

    def test_model_cache_singleton(self):
        """測試模型快取使用單例模式"""
        from paddleocr_toolkit.core.model_cache import ModelCache

        cache1 = ModelCache()
        cache2 = ModelCache()
        assert cache1 is cache2

    def test_model_cache_get_model(self):
        """測試獲取模型"""
        from paddleocr_toolkit.core.model_cache import ModelCache

        cache = ModelCache()
        # 清除之前的快取
        cache.clear_cache()
        
        # 獲取模型（會使用佔位符）
        model = cache.get_model("basic")
        assert model is not None

    def test_model_cache_clear(self):
        """測試清除快取"""
        from paddleocr_toolkit.core.model_cache import ModelCache

        cache = ModelCache()
        cache.clear_cache()
        info = cache.get_cache_info()
        assert info["cached_models"] == 0

    def test_model_cache_get_info(self):
        """測試獲取快取資訊"""
        from paddleocr_toolkit.core.model_cache import ModelCache

        cache = ModelCache()
        info = cache.get_cache_info()
        assert "cached_models" in info


class TestResultCache:
    """測試結果快取"""

    def test_import_result_cache(self):
        """測試匯入結果快取"""
        from paddleocr_toolkit.core.model_cache import ResultCache

        assert ResultCache is not None

    def test_result_cache_init(self):
        """測試結果快取初始化"""
        from paddleocr_toolkit.core.model_cache import ResultCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ResultCache(cache_dir=Path(tmpdir))
            assert cache is not None

    def test_result_cache_default_init(self):
        """測試結果快取預設初始化"""
        from paddleocr_toolkit.core.model_cache import ResultCache

        cache = ResultCache()
        assert cache.max_size == 1000

    def test_result_cache_custom_max_size(self):
        """測試結果快取自定義大小"""
        from paddleocr_toolkit.core.model_cache import ResultCache

        cache = ResultCache(max_size=500)
        assert cache.max_size == 500

    def test_result_cache_clear(self):
        """測試清除快取"""
        from paddleocr_toolkit.core.model_cache import ResultCache

        cache = ResultCache()
        cache.clear()
        stats = cache.get_stats()
        assert stats["memory_cached"] == 0

    def test_result_cache_get_stats(self):
        """測試獲取統計資訊"""
        from paddleocr_toolkit.core.model_cache import ResultCache

        cache = ResultCache()
        stats = cache.get_stats()
        assert "hits" in stats
        assert "misses" in stats
        assert "memory_cached" in stats


class TestCachedOcrResult:
    """測試快取裝飾器"""

    def test_import_decorator(self):
        """測試匯入裝飾器"""
        from paddleocr_toolkit.core.model_cache import cached_ocr_result

        assert cached_ocr_result is not None
        assert callable(cached_ocr_result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
