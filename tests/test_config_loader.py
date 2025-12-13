# -*- coding: utf-8 -*-
"""
設定檔載入器單元測試
"""

import pytest
import sys
import os
import tempfile

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paddleocr_toolkit.core.config_loader import (
    load_config,
    deep_merge,
    get_config_value,
    save_config,
    DEFAULT_CONFIG,
)


class TestDeepMerge:
    """測試 deep_merge"""
    
    def test_simple_merge(self):
        """測試簡單合併"""
        base = {'a': 1, 'b': 2}
        override = {'b': 3, 'c': 4}
        
        result = deep_merge(base, override)
        
        assert result['a'] == 1
        assert result['b'] == 3
        assert result['c'] == 4
    
    def test_nested_merge(self):
        """測試巢狀合併"""
        base = {'ocr': {'mode': 'basic', 'dpi': 150}}
        override = {'ocr': {'mode': 'hybrid'}}
        
        result = deep_merge(base, override)
        
        assert result['ocr']['mode'] == 'hybrid'
        assert result['ocr']['dpi'] == 150  # 保留未覆蓋的值


class TestGetConfigValue:
    """測試 get_config_value"""
    
    def test_simple_path(self):
        """測試簡單路徑"""
        config = {'ocr': {'mode': 'hybrid'}}
        
        assert get_config_value(config, 'ocr.mode') == 'hybrid'
    
    def test_deep_path(self):
        """測試深層路徑"""
        config = {'a': {'b': {'c': 'value'}}}
        
        assert get_config_value(config, 'a.b.c') == 'value'
    
    def test_missing_path(self):
        """測試不存在的路徑"""
        config = {'ocr': {'mode': 'hybrid'}}
        
        assert get_config_value(config, 'ocr.missing', 'default') == 'default'
    
    def test_top_level(self):
        """測試頂層值"""
        config = {'version': '1.0.0'}
        
        assert get_config_value(config, 'version') == '1.0.0'


class TestLoadConfig:
    """測試 load_config"""
    
    def test_default_config(self):
        """測試載入預設設定"""
        # 不指定路徑，使用預設
        config = load_config(config_path="nonexistent.yaml")
        
        # 應該有預設值
        assert 'ocr' in config
        assert 'output' in config
        assert 'compression' in config
        assert 'translation' in config
    
    def test_default_values(self):
        """測試預設值正確"""
        assert DEFAULT_CONFIG['ocr']['mode'] == 'hybrid'
        assert DEFAULT_CONFIG['compression']['jpeg_quality'] == 85
        assert DEFAULT_CONFIG['translation']['ollama_model'] == 'qwen2.5:7b'


class TestSaveConfig:
    """測試 save_config"""
    
    def test_save_and_load(self):
        """測試儲存和載入"""
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")
        
        config = {
            'ocr': {'mode': 'hybrid', 'dpi': 200},
            'test': True
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            # 儲存
            result = save_config(config, temp_path)
            assert result is True
            
            # 載入
            loaded = load_config(temp_path)
            assert loaded['ocr']['mode'] == 'hybrid'
            assert loaded['ocr']['dpi'] == 200
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
