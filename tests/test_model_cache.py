# -*- coding: utf-8 -*-
"""
模型快取測試
測試 paddleocr_toolkit/core/model_cache.py
"""

import tempfile
import os
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

# Added from Ultra Coverage
from paddleocr_toolkit.core.model_cache import ModelCache, ResultCache
from unittest.mock import MagicMock, patch
from pathlib import Path
import runpy


class TestModelCacheUltra:
    def test_model_cache_basic(self):
        cache = ModelCache()
        # Hit line 58: Using cached model
        cache.get_model("basic")
        cache.get_model("basic")

    def test_result_cache_disk_load_error(self):
        with patch("pathlib.Path.mkdir"):
            cache = ResultCache(cache_dir=Path("./tmp_cache"))
            # Simulate disk cache exist but load fail (line 162)
            with patch("pathlib.Path.exists", return_value=True), patch(
                "builtins.open", side_effect=Exception("Disk error")
            ), patch.object(cache, "_compute_file_hash", return_value="hash"):
                res = cache.get("file.pdf", "basic")
                assert res is None

    def test_result_cache_save_error(self):
        with patch("pathlib.Path.mkdir"):
            cache = ResultCache(cache_dir=Path("./tmp_cache"))
            with patch(
                "builtins.open", side_effect=Exception("Save error")
            ), patch.object(cache, "_compute_file_hash", return_value="hash"):
                cache.set("file.pdf", "basic", {"res": 1})

    def test_main_block_simulation(self):
        runpy.run_module("paddleocr_toolkit.core.model_cache", run_name="__main__")


class TestResultCacheExtensions:
    """測試 ResultCache 進階功能"""

    def test_cache_size_limit(self):
        """測試快取大小限制"""
        from paddleocr_toolkit.core.model_cache import ResultCache

        # 設定小容量以便測試
        cache = ResultCache(max_size=3)
        cache.clear()

        # 填充快取 (Mock _compute_file_hash 以避免真實文件讀取)
        with patch.object(cache, "_compute_file_hash") as mock_hash:
            # 插入 4 個項目，應該觸發清理
            for i in range(4):
                mock_hash.return_value = f"hash_{i}"
                cache.set(f"file_{i}", "mode", f"res_{i}")

            # 驗證記憶體快取大小不超過 3
            assert len(cache.memory_cache) == 3
            # 舊的應該被移除 (FIFO: 0 最早)
            assert "hash_0_mode" not in cache.memory_cache
            assert "hash_3_mode" in cache.memory_cache

    def test_compute_file_hash_real_file(self):
        """測試真實文件哈希計算"""
        from paddleocr_toolkit.core.model_cache import ResultCache

        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(b"content")
            file_path = f.name

        try:
            cache = ResultCache()
            hash1 = cache._compute_file_hash(file_path)

            # 修改文件
            with open(file_path, "wb") as f:
                f.write(b"new content")
            hash2 = cache._compute_file_hash(file_path)

            assert hash1 != hash2
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_set_get_roundtrip_disk(self):
        """測試磁碟快取完整的寫入與讀取"""
        from paddleocr_toolkit.core.model_cache import ResultCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ResultCache(cache_dir=Path(tmpdir))

            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(b"test")
                file_path = f.name

            try:
                # 寫入
                result_data = {"text": "hello"}
                cache.set(file_path, "hybrid", result_data)

                # 驗證記憶體
                assert cache.cache_hits == 0  # 還沒 get 過

                # 清除記憶體快取，強迫從磁碟讀取
                cache.memory_cache.clear()

                # 讀取
                loaded = cache.get(file_path, "hybrid")
                assert loaded == result_data
                assert cache.cache_hits == 1  # 從磁碟命中

            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)


class TestDecoratorFunctionality:
    """測試裝飾器功能"""

    def test_cached_ocr_result_decorator(self):
        """測試裝飾器實際快取行為"""
        from paddleocr_toolkit.core.model_cache import cached_ocr_result, ResultCache

        # Mock ResultCache 以便我們可以攔截
        mock_cache_inst = MagicMock()
        mock_cache_inst.get.return_value = None

        with patch(
            "paddleocr_toolkit.core.model_cache.ResultCache",
            return_value=mock_cache_inst,
        ):
            mock_process = MagicMock(return_value="processed_result")

            @cached_ocr_result("hybrid")
            def process_func(path):
                return mock_process(path)

            # 第一次調用 (Cache Miss)
            res1 = process_func("test.pdf")
            assert res1 == "processed_result"
            mock_cache_inst.get.assert_called_with("test.pdf", "hybrid")
            mock_cache_inst.set.assert_called_with(
                "test.pdf", "hybrid", "processed_result"
            )
            mock_process.assert_called_once()

            # 模擬第二次調用 (Cache Hit)
            mock_cache_inst.get.return_value = "cached_result"
            mock_process.reset_mock()

            res2 = process_func("test.pdf")
            assert res2 == "cached_result"
            mock_process.assert_not_called()  # 應該沒有調用實際函數
