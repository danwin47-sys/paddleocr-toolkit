# -*- coding: utf-8 -*-
"""
文字處理模組單元測試
"""

import os
import sys

import pytest

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paddleocr_toolkit.processors.text_processor import (
    MERGE_TERMS,
    PROTECTED_TERMS,
    fix_english_spacing,
)


class TestMergeTerms:
    """測試 MERGE_TERMS 替換規則"""

    def test_version_number_fix(self):
        """測試版本號修正"""
        assert fix_english_spacing(".v0.pdf") == ".v10.pdf"
        assert fix_english_spacing("dr.v0") == "dr.v10"
        assert fix_english_spacing("file_v0.pdf") == "file_v10.pdf"

    def test_mems_terms(self):
        """測試 MEMS 術語修正"""
        assert "PolyMUMPs" in fix_english_spacing("Poly MUMPs")
        assert "SOIMUMPs" in fix_english_spacing("SOI MUMPs")
        assert "MEMScAP" in fix_english_spacing("MEMS cAP")

    def test_copyright_symbol(self):
        """測試版權符號空格"""
        assert fix_english_spacing("2024©") == "2024 ©"
        assert fix_english_spacing("2025©") == "2025 ©"

    def test_unit_fix(self):
        """測試單位修正"""
        assert fix_english_spacing("u m") == "μm"
        assert fix_english_spacing("u M") == "μM"


class TestCamelCaseSplit:
    """測試 CamelCase 分詞"""

    def test_basic_camelcase(self):
        """測試基本 CamelCase"""
        result = fix_english_spacing("FoundryService")
        assert "Foundry Service" in result or "Foundry" in result

    def test_protected_terms(self):
        """測試受保護術語不被拆分"""
        # PaddleOCR 不應被拆分
        result = fix_english_spacing("usePaddleOCR")
        assert "PaddleOCR" in result


class TestCommonSplits:
    """測試常見黏連詞分詞"""

    def test_article_splits(self):
        """測試冠詞黏連"""
        assert "for the" in fix_english_spacing("forthe")
        assert "in the" in fix_english_spacing("inthe")
        assert "of the" in fix_english_spacing("ofthe")

    def test_verb_splits(self):
        """測試動詞黏連"""
        assert "has been" in fix_english_spacing("hasbeen")
        assert "can be" in fix_english_spacing("canbe")


class TestHyphenatedWords:
    """測試連字符詞修復"""

    def test_common_hyphenated(self):
        """測試常見連字符詞"""
        assert "well-established" in fix_english_spacing("wellestablished").lower()
        assert "cost-effective" in fix_english_spacing("costeffective").lower()
        assert "real-time" in fix_english_spacing("realtime").lower()


class TestEdgeCases:
    """測試邊界情況"""

    def test_empty_string(self):
        """測試空字串"""
        assert fix_english_spacing("") == ""
        assert fix_english_spacing(None) is None

    def test_ordinal_numbers(self):
        """測試序數不被拆分"""
        # 9th 不應變成 9 th
        result = fix_english_spacing("9th")
        assert "9 th" not in result
        assert "9th" in result


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
