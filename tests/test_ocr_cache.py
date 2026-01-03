# -*- coding: utf-8 -*-
"""
OCR Cache Tests
"""
import os
import json
import pytest
from pathlib import Path
from paddleocr_toolkit.core.ocr_cache import OCRCache


class TestOCRCache:
    @pytest.fixture
    def cache_obj(self, tmp_path):
        """Fixture to create an OCRCache instance with a temporary directory"""
        cache_dir = tmp_path / "ocr_cache"
        return OCRCache(cache_dir=str(cache_dir))

    def test_init(self, cache_obj):
        """Test cache directory creation"""
        assert cache_obj.cache_dir.exists()
        assert cache_obj.cache_dir.is_dir()

    def test_get_file_hash(self, cache_obj, tmp_path):
        """Test file MD5 hash calculation"""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"hello world")

        file_hash = cache_obj._get_file_hash(str(test_file))
        assert len(file_hash) == 32  # MD5 hexdigest length

        # Consistent hash
        assert file_hash == cache_obj._get_file_hash(str(test_file))

    def test_set_and_get_hit(self, cache_obj, tmp_path):
        """Test cache set and successful get (hit)"""
        test_file = tmp_path / "image.png"
        test_file.write_bytes(b"fake_image_data")

        result_data = {"text": "found me", "score": 0.99}
        mode = "advanced"

        cache_obj.set(str(test_file), mode, result_data)

        # Verify get
        cached_res = cache_obj.get(str(test_file), mode)
        assert cached_res == result_data

    def test_get_miss(self, cache_obj, tmp_path):
        """Test cache miss (file doesn't exist or different mode)"""
        test_file = tmp_path / "missing.png"
        test_file.write_bytes(b"data")

        assert cache_obj.get(str(test_file), "basic") is None

        # Same file, different mode miss
        cache_obj.set(str(test_file), "basic", {"res": "ok"})
        assert cache_obj.get(str(test_file), "enhanced") is None

    def test_error_handling(self, cache_obj):
        """Test that methods don't crash on invalid input"""
        # Invalid file path for hashing
        assert cache_obj.get("/non/existent/path", "mode") is None

        # Should not raise exception
        cache_obj.set("/non/existent/path", "mode", {})
