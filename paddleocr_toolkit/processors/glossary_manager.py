# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - 智慧術語表管理器

支援多語言術語表，可在翻譯時自動鎖定專業術語。
"""

import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class GlossaryEntry:
    """術語表條目"""

    source: str  # 原文術語
    target: str  # 翻譯
    target_lang: Optional[str] = None  # 目標語言（可選）

    def matches_lang(self, lang: str) -> bool:
        """檢查是否匹配目標語言"""
        if not self.target_lang:
            return True  # 未指定語言 = 適用所有語言

        # 正規化語言程式碼
        normalized_entry = self.target_lang.lower().replace("-", "_")
        normalized_lang = lang.lower().replace("-", "_")
        return normalized_entry == normalized_lang


class GlossaryManager:
    """
    智慧術語表管理器

    功能：
    - 支援多個術語表檔案
    - 支援多語言術語
    - 翻譯時自動偵測並保護術語
    - 生成 LLM 提示詞
    """

    def __init__(self, target_lang: str = "en"):
        """
        初始化術語表管理器

        Args:
            target_lang: 目標語言程式碼（如 "en", "zh-TW", "ja"）
        """
        self.target_lang = target_lang
        self.glossaries: Dict[str, List[GlossaryEntry]] = {}  # name -> entries
        self.all_terms: Dict[str, str] = {}  # source -> target
        self._placeholder_map: Dict[str, str] = {}  # placeholder -> original

    def load_csv(self, csv_path: str, name: Optional[str] = None) -> int:
        """
        載入 CSV 術語表

        CSV 格式: source,target,tgt_lng (tgt_lng 為可選欄位)

        Args:
            csv_path: CSV 檔案路徑
            name: 術語表名稱（預設為檔名）

        Returns:
            載入的術語數量
        """
        path = Path(csv_path)
        if not path.exists():
            logging.warning(f"術語表不存在: {csv_path}")
            return 0

        if name is None:
            name = path.stem  # 使用檔名作為名稱

        entries = []
        count = 0

        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    source = row.get("source", "").strip()
                    target = row.get("target", "").strip()
                    tgt_lng = row.get("tgt_lng", "").strip() or None

                    if not source:
                        continue

                    entry = GlossaryEntry(
                        source=source, target=target, target_lang=tgt_lng
                    )

                    # 只載入匹配目標語言的術語
                    if entry.matches_lang(self.target_lang):
                        entries.append(entry)
                        self.all_terms[source] = target
                        count += 1

            self.glossaries[name] = entries
            logging.info(f"載入術語表 '{name}': {count} 條術語")

        except Exception as e:
            logging.error(f"載入術語表失敗: {e}")

        return count

    def load_multiple(self, csv_paths: List[str]) -> int:
        """載入多個術語表"""
        total = 0
        for path in csv_paths:
            total += self.load_csv(path)
        return total

    def protect_terms(self, text: str) -> str:
        """
        保護術語：用佔位符替換，避免被分詞或翻譯

        Args:
            text: 原始文字

        Returns:
            替換後的文字
        """
        self._placeholder_map.clear()
        result = text

        # 按長度排序（先處理長的，避免部分匹配問題）
        sorted_terms = sorted(self.all_terms.keys(), key=len, reverse=True)

        for i, source in enumerate(sorted_terms):
            if source in result:
                placeholder = f"__TERM_{i}__"
                self._placeholder_map[placeholder] = source
                result = result.replace(source, placeholder)

        return result

    def restore_terms(self, text: str, use_translation: bool = True) -> str:
        """
        還原術語：將佔位符換回術語（原文或翻譯）

        Args:
            text: 含佔位符的文字
            use_translation: True=使用翻譯，False=使用原文

        Returns:
            還原後的文字
        """
        result = text

        for placeholder, source in self._placeholder_map.items():
            if placeholder in result:
                if use_translation:
                    replacement = self.all_terms.get(source, source)
                else:
                    replacement = source
                result = result.replace(placeholder, replacement)

        return result

    def find_terms_in_text(self, text: str) -> List[Tuple[str, str]]:
        """
        在文字中找出所有術語

        Returns:
            List[(source, target)]
        """
        found = []
        for source, target in self.all_terms.items():
            if source in text:
                found.append((source, target))
        return found

    def generate_llm_prompt(self, text: str) -> Optional[str]:
        """
        為 LLM 生成術語提示

        如果文字中包含術語，生成提示 LLM 遵守的指令

        Returns:
            提示詞或 None（如果沒有找到術語）
        """
        found_terms = self.find_terms_in_text(text)

        if not found_terms:
            return None

        lines = ["請遵守以下術語翻譯規則："]
        for source, target in found_terms:
            if target:
                lines.append(f"- {source} → {target}")
            else:
                lines.append(f"- {source}（保持原文不翻譯）")

        return "\n".join(lines)

    def get_stats(self) -> Dict:
        """取得統計資訊"""
        return {
            "total_terms": len(self.all_terms),
            "glossaries": list(self.glossaries.keys()),
            "glossary_counts": {
                name: len(entries) for name, entries in self.glossaries.items()
            },
        }


def create_sample_glossary(output_path: str = "glossary_sample.csv"):
    """建立範例術語表檔案"""
    sample_data = [
        {"source": "MEMS", "target": "微機電系統", "tgt_lng": "zh-TW"},
        {"source": "MEMS", "target": "MEMS", "tgt_lng": "en"},
        {"source": "PolyMUMPs", "target": "", "tgt_lng": ""},  # 不翻譯
        {"source": "SOIMUMPs", "target": "", "tgt_lng": ""},
        {"source": "MEMScAP", "target": "", "tgt_lng": ""},
        {"source": "micromachining", "target": "微加工", "tgt_lng": "zh-TW"},
        {"source": "wafer", "target": "晶圓", "tgt_lng": "zh-TW"},
        {"source": "lithography", "target": "微影", "tgt_lng": "zh-TW"},
    ]

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["source", "target", "tgt_lng"])
        writer.writeheader()
        writer.writerows(sample_data)

    print(f"範例術語表已建立: {output_path}")
