# -*- coding: utf-8 -*-
"""
設定檔載入器單元測試
"""

import argparse
import os
import sys
import tempfile

import pytest

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paddleocr_toolkit.core.config_loader import (
    DEFAULT_CONFIG,
    apply_config_to_args,
    deep_merge,
    get_config_value,
    load_config,
    save_config,
)


class TestDeepMerge:
    """測試 deep_merge"""

    def test_simple_merge(self):
        """測試簡單合併"""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}

        result = deep_merge(base, override)

        assert result["a"] == 1
        assert result["b"] == 3
        assert result["c"] == 4

    def test_nested_merge(self):
        """測試巢狀合併"""
        base = {"ocr": {"mode": "basic", "dpi": 150}}
        override = {"ocr": {"mode": "hybrid"}}

        result = deep_merge(base, override)

        assert result["ocr"]["mode"] == "hybrid"
        assert result["ocr"]["dpi"] == 150  # 保留未覆蓋的值

    def test_empty_override(self):
        """測試空覆蓋"""
        base = {"a": 1}
        override = {}

        result = deep_merge(base, override)

        assert result == {"a": 1}

    def test_new_nested_key(self):
        """測試新增巢狀鍵"""
        base = {"a": {"b": 1}}
        override = {"a": {"c": 2}}

        result = deep_merge(base, override)

        assert result["a"]["b"] == 1
        assert result["a"]["c"] == 2


class TestGetConfigValue:
    """測試 get_config_value"""

    def test_simple_path(self):
        """測試簡單路徑"""
        config = {"ocr": {"mode": "hybrid"}}

        assert get_config_value(config, "ocr.mode") == "hybrid"

    def test_deep_path(self):
        """測試深層路徑"""
        config = {"a": {"b": {"c": "value"}}}

        assert get_config_value(config, "a.b.c") == "value"

    def test_missing_path(self):
        """測試不存在的路徑"""
        config = {"ocr": {"mode": "hybrid"}}

        assert get_config_value(config, "ocr.missing", "default") == "default"

    def test_top_level(self):
        """測試頂層值"""
        config = {"version": "1.0.0"}

        assert get_config_value(config, "version") == "1.0.0"

    def test_none_default(self):
        """測試 None 預設值"""
        config = {}

        assert get_config_value(config, "missing") is None


class TestLoadConfig:
    """測試 load_config"""

    def test_default_config(self):
        """測試載入預設設定"""
        config = load_config(config_path="nonexistent.yaml")

        assert "ocr" in config
        assert "output" in config
        assert "compression" in config
        assert "translation" in config

    def test_default_values(self):
        """測試預設值正確"""
        assert DEFAULT_CONFIG["ocr"]["mode"] == "hybrid"
        assert DEFAULT_CONFIG["compression"]["jpeg_quality"] == 85
        assert DEFAULT_CONFIG["translation"]["ollama_model"] == "qwen2.5:7b"

    def test_load_from_existing_file(self):
        """測試從現有檔案載入"""
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write("ocr:\n  mode: basic\n  dpi: 300\n")
            temp_path = f.name

        try:
            config = load_config(temp_path)

            assert config["ocr"]["mode"] == "basic"
            assert config["ocr"]["dpi"] == 300

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestSaveConfig:
    """測試 save_config"""

    def test_save_and_load(self):
        """測試儲存和載入"""
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")

        config = {"ocr": {"mode": "hybrid", "dpi": 200}, "test": True}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name

        try:
            result = save_config(config, temp_path)
            assert result is True

            loaded = load_config(temp_path)
            assert loaded["ocr"]["mode"] == "hybrid"
            assert loaded["ocr"]["dpi"] == 200

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_save_creates_directory(self):
        """測試儲存時建立目錄"""
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "subdir", "config.yaml")

            result = save_config({"test": True}, path)

            assert result is True
            assert os.path.exists(path)


class TestApplyConfigToArgs:
    """測試 apply_config_to_args"""

    def test_apply_ocr_settings(self):
        """測試套用 OCR 設定"""
        config = {"ocr": {"mode": "structure", "device": "gpu", "dpi": 300}}

        args = argparse.Namespace(
            mode=None,
            device=None,
            dpi=None,
            no_progress=False,
            no_compress=False,
            jpeg_quality=None,
        )

        apply_config_to_args(config, args)

        assert args.mode == "structure"
        assert args.device == "gpu"
        assert args.dpi == 300

    def test_cli_overrides_config(self):
        """測試 CLI 參數優先於設定"""
        config = {"ocr": {"mode": "structure"}}

        args = argparse.Namespace(
            mode="hybrid",  # CLI 指定了值
            device=None,
            dpi=None,
            no_progress=False,
            no_compress=False,
            jpeg_quality=None,
        )

        apply_config_to_args(config, args)

        # CLI 參數應該保留
        assert args.mode == "hybrid"


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
