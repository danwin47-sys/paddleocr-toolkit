# -*- coding: utf-8 -*-
"""
Glossary Manager 單元測試
"""

import pytest
import sys
import os
import tempfile

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paddleocr_toolkit.processors.glossary_manager import (
    GlossaryEntry,
    GlossaryManager,
    create_sample_glossary,
)


class TestGlossaryEntry:
    """測試 GlossaryEntry"""
    
    def test_basic_creation(self):
        """測試基本建立"""
        entry = GlossaryEntry(
            source="hello",
            target="你好",
            target_lang="zh-TW"
        )
        
        assert entry.source == "hello"
        assert entry.target == "你好"
        assert entry.target_lang == "zh-TW"
    
    def test_optional_fields(self):
        """測試可選欄位"""
        entry = GlossaryEntry(
            source="test",
            target="測試"
        )
        
        assert entry.source == "test"
        assert entry.target_lang is None
    
    def test_matches_lang(self):
        """測試語言匹配"""
        entry = GlossaryEntry(source="AI", target="人工智慧", target_lang="zh-TW")
        
        assert entry.matches_lang("zh-TW") is True
        assert entry.matches_lang("zh-tw") is True
        assert entry.matches_lang("en") is False
    
    def test_matches_any_lang(self):
        """測試無語言限制"""
        entry = GlossaryEntry(source="MEMS", target="")
        
        assert entry.matches_lang("en") is True
        assert entry.matches_lang("zh-TW") is True


class TestGlossaryManager:
    """測試 GlossaryManager"""
    
    def test_initialization(self):
        """測試初始化"""
        manager = GlossaryManager()
        
        assert manager is not None
        assert manager.target_lang == "en"
    
    def test_initialization_with_lang(self):
        """測試指定語言初始化"""
        manager = GlossaryManager(target_lang="zh-TW")
        
        assert manager.target_lang == "zh-TW"
    
    def test_find_terms_empty(self):
        """測試空術語表查詢"""
        manager = GlossaryManager()
        
        result = manager.find_terms_in_text("Hello world")
        
        assert result == []
    
    def test_get_stats(self):
        """測試取得統計"""
        manager = GlossaryManager()
        
        stats = manager.get_stats()
        
        assert 'total_terms' in stats
        assert 'glossaries' in stats
        assert stats['total_terms'] == 0


class TestCreateSampleGlossary:
    """測試建立範例術語表"""
    
    def test_create_sample(self):
        """測試建立範例"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sample.csv")
            
            create_sample_glossary(path)
            
            assert os.path.exists(path)
            
            # 檢查檔案內容
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert 'source' in content
                assert 'MEMS' in content


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
