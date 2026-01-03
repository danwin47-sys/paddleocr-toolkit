# -*- coding: utf-8 -*-
"""
Advanced tests for GlossaryManager to cover edge cases.
"""
import tempfile
import os
import csv
from unittest.mock import patch
import pytest

from paddleocr_toolkit.processors.glossary_manager import GlossaryManager


class TestGlossaryManagerAdvanced:
    """測試 GlossaryManager 的進階情況"""

    def test_load_csv_malformed_content(self):
        """測試載入非 CSV 格式或編碼錯誤的文件"""
        manager = GlossaryManager()

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("This is not a CSV file\nJust some random text")
            path = f.name

        try:
            # 這應該會被 try-except 捕獲並記錄錯誤，返回 0
            # DictReader 可能不會報錯，但如果 keys 不對應該也沒事
            # 我們模擬一個會讓 csv.DictReader 失敗的情況，或者在 loop 中出錯
            # 不過 DictReader 對壞格式很寬容。
            # 讓我們模擬 open 失敗
            with patch("builtins.open", side_effect=Exception("File access error")):
                count = manager.load_csv(path)
                assert count == 0

        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_load_csv_empty_source(self):
        """測試略過 source 為空的行"""
        manager = GlossaryManager()

        with tempfile.NamedTemporaryFile(mode="w", delete=False, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["source", "target"])
            writer.writeheader()
            writer.writerow({"source": "Valid", "target": "V"})
            writer.writerow({"source": "   ", "target": "Invalid"})  # 空白 source
            writer.writerow({"source": "", "target": "Empty"})
            path = f.name

        try:
            count = manager.load_csv(path)
            assert count == 1
            assert "Valid" in manager.all_terms
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_protect_terms_overlapping(self):
        """測試重疊術語的保護順序 (長詞優先)"""
        manager = GlossaryManager()
        # 手動注入術語
        manager.all_terms = {"Super Micro": "超微", "Micro": "微型"}

        text = "This is a Super Micro computer."
        protected = manager.protect_terms(text)

        # 應該先保護 'Super Micro'，所以 'Micro' 不會被二次保護
        # 佔位符應該只有一個 (對應 Super Micro)
        assert len(manager._placeholder_map) == 1

        # 驗證還原
        restored = manager.restore_terms(protected)
        assert restored == "This is a 超微 computer."  # use_translation=True by default

    def test_generate_llm_prompt_mixed_targets(self):
        """測試生成包含翻譯和不翻譯術語的提示詞"""
        manager = GlossaryManager()
        manager.all_terms = {"Term1": "Translation1", "Term2": ""}  # 不翻譯

        text = "Contains Term1 and Term2"
        prompt = manager.generate_llm_prompt(text)

        assert "Term1 → Translation1" in prompt
        assert "Term2（保持原文不翻譯）" in prompt

    def test_load_multiple(self):
        """測試載入多個檔案"""
        manager = GlossaryManager()

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, newline=""
        ) as f1, tempfile.NamedTemporaryFile(mode="w", delete=False, newline="") as f2:
            # File 1
            w1 = csv.DictWriter(f1, fieldnames=["source", "target"])
            w1.writeheader()
            w1.writerow({"source": "A", "target": "1"})

            # File 2
            w2 = csv.DictWriter(f2, fieldnames=["source", "target"])
            w2.writeheader()
            w2.writerow({"source": "B", "target": "2"})

            paths = [f1.name, f2.name]

        try:
            # 必須 close 才能讓 load_csv 讀取
            f1.close()
            f2.close()

            total = manager.load_multiple(paths)
            assert total == 2
            assert "A" in manager.all_terms
            assert "B" in manager.all_terms

        finally:
            for p in paths:
                if os.path.exists(p):
                    os.remove(p)

    def test_restore_terms_original(self):
        """測試還原為原文"""
        manager = GlossaryManager()
        manager.all_terms = {"Test": "測試"}

        text = "This is a Test."
        protected = manager.protect_terms(text)
        restored = manager.restore_terms(protected, use_translation=False)

        assert restored == "This is a Test."
