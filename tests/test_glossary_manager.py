# -*- coding: utf-8 -*-
"""
Glossary Manager 單元測試
"""

import csv
import os
import sys
import tempfile

import pytest

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paddleocr_toolkit.processors.glossary_manager import (
    GlossaryEntry, GlossaryManager, create_sample_glossary)


class TestGlossaryEntry:
    """測試 GlossaryEntry"""

    def test_basic_creation(self):
        """測試基本建立"""
        entry = GlossaryEntry(source="hello", target="你好", target_lang="zh-TW")

        assert entry.source == "hello"
        assert entry.target == "你好"
        assert entry.target_lang == "zh-TW"

    def test_optional_fields(self):
        """測試可選欄位"""
        entry = GlossaryEntry(source="test", target="測試")

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

        assert "total_terms" in stats
        assert "glossaries" in stats
        assert stats["total_terms"] == 0

    def test_load_csv(self):
        """測試載入 CSV"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(f, fieldnames=["source", "target", "tgt_lng"])
            writer.writeheader()
            writer.writerow(
                {"source": "AI", "target": "Artificial Intelligence", "tgt_lng": "en"}
            )
            writer.writerow(
                {"source": "ML", "target": "Machine Learning", "tgt_lng": "en"}
            )
            temp_path = f.name

        try:
            manager = GlossaryManager(target_lang="en")
            count = manager.load_csv(temp_path)

            assert count == 2
            assert manager.get_stats()["total_terms"] == 2

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_load_nonexistent_csv(self):
        """測試載入不存在的 CSV"""
        manager = GlossaryManager()

        count = manager.load_csv("nonexistent.csv")

        assert count == 0

    def test_find_terms_in_text(self):
        """測試在文字中查找術語"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(f, fieldnames=["source", "target", "tgt_lng"])
            writer.writeheader()
            writer.writerow(
                {
                    "source": "OCR",
                    "target": "Optical Character Recognition",
                    "tgt_lng": "en",
                }
            )
            temp_path = f.name

        try:
            manager = GlossaryManager(target_lang="en")
            manager.load_csv(temp_path)

            found = manager.find_terms_in_text("This is about OCR technology")

            assert len(found) == 1
            assert found[0][0] == "OCR"

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_protect_and_restore_terms(self):
        """測試保護和還原術語"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(f, fieldnames=["source", "target", "tgt_lng"])
            writer.writeheader()
            writer.writerow(
                {"source": "PaddleOCR", "target": "PaddleOCR", "tgt_lng": "en"}
            )
            temp_path = f.name

        try:
            manager = GlossaryManager(target_lang="en")
            manager.load_csv(temp_path)

            text = "Use PaddleOCR for OCR tasks"
            protected = manager.protect_terms(text)

            # 術語應該被替換為佔位符
            assert "PaddleOCR" not in protected or "__TERM_" in protected

            # 還原
            restored = manager.restore_terms(protected)
            assert "PaddleOCR" in restored

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestCreateSampleGlossary:
    """測試建立範例術語表"""

    def test_create_sample(self):
        """測試建立範例"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sample.csv")

            create_sample_glossary(path)

            assert os.path.exists(path)

            # 檢查檔案內容
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                assert "source" in content
                assert "MEMS" in content


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
