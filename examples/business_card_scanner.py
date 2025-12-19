#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎫 名片掃描器 - PaddleOCR Toolkit 示例專案
自動從名片圖片中提取聯絡資訊

使用方法:
    python business_card_scanner.py card.jpg
    python business_card_scanner.py cards/  # 批次處理
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from paddle_ocr_tool import PaddleOCRTool


class BusinessCardScanner:
    """名片掃描器"""

    def __init__(self):
        """初始化OCR引擎"""
        print("初始化 OCR 引擎...")
        self.ocr_tool = PaddleOCRTool(mode="basic", device="gpu")
        print("OCR 引擎就緒！\n")

    def scan_card(self, image_path: str) -> Dict:
        """
        掃描名片並提取資訊

        Args:
            image_path: 名片圖片路徑

        Returns:
            包含聯絡資訊的字典
        """
        print(f"掃描名片: {image_path}")

        # OCR識別
        results = self.ocr_tool.process_image(image_path)

        # 合併所有文字
        all_text = "\n".join([r.text for r in results])

        # 提取資訊
        card_info = {
            "file": str(image_path),
            "name": self._extract_name(results),
            "title": self._extract_title(results),
            "company": self._extract_company(results),
            "phone": self._extract_phone(all_text),
            "email": self._extract_email(all_text),
            "address": self._extract_address(all_text),
            "website": self._extract_website(all_text),
            "raw_text": all_text,
        }

        return card_info

    def _extract_name(self, results: List) -> Optional[str]:
        """提取姓名（通常在頂部且字型最大）"""
        if results:
            # 假設第一行或第二行是姓名
            for result in results[:3]:
                text = result.text.strip()
                # 簡單判斷：2-4個字或2-20個英文字母
                if 2 <= len(text) <= 4 or (text.isalpha() and 2 <= len(text) <= 20):
                    return text
        return None

    def _extract_title(self, results: List) -> Optional[str]:
        """提取職位"""
        title_keywords = ["經理", "總監", "主管", "Manager", "Director", "CEO", "CTO"]

        for result in results:
            text = result.text.strip()
            if any(keyword in text for keyword in title_keywords):
                return text
        return None

    def _extract_company(self, results: List) -> Optional[str]:
        """提取公司名稱"""
        company_keywords = ["公司", "有限", "Co.", "Ltd", "Inc", "Corp"]

        for result in results:
            text = result.text.strip()
            if any(keyword in text for keyword in company_keywords):
                return text
        return None

    def _extract_phone(self, text: str) -> List[str]:
        """提取電話號碼"""
        # 尋找手機號碼
        patterns = [
            r"09\d{8}",  # 臺灣手機
            r"\d{2,4}[-\s]?\d{6,8}",  # 臺灣市話 (區碼2-4位, 號碼6-8位)
            r"\+\d{1,3}[-\s]?\d{1,14}",  # 國際號碼
            r"\(\d{3}\)\s?\d{3}[-\s]?\d{4}",  # (123) 456-7890
        ]

        phones = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            phones.extend(matches)

        return list(set(phones))  # 去重

    def _extract_email(self, text: str) -> Optional[str]:
        """提取電子郵件"""
        pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        match = re.search(pattern, text)
        return match.group(0) if match else None

    def _extract_address(self, text: str) -> Optional[str]:
        """提取地址"""
        # 尋找包含地址關鍵字的行
        lines = text.split('\n')
        address_keywords = ["路", "街", "號", "市", "區", "縣", "段", "巷", "弄", "Street", "Road", "Ave", "City"]

        for line in lines:
            if any(keyword in line for keyword in address_keywords):
                return line.strip()
        return None

    def _extract_website(self, text: str) -> Optional[str]:
        """提取網站"""
        pattern = r"(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}"
        match = re.search(pattern, text)
        return match.group(0) if match else None

    def print_card_info(self, info: Dict):
        """美化顯示名片資訊"""
        print("\n" + "=" * 50)
        print("名片掃描結果")
        print("=" * 50)

        if info.get("name"):
            print(f"姓名: {info['name']}")

        if info.get("title"):
            print(f"職位: {info['title']}")

        if info.get("company"):
            print(f"公司: {info['company']}")

        if info.get("phone"):
            print(f"電話: {', '.join(info['phone'])}")

        if info.get("email"):
            print(f"信箱: {info['email']}")

        if info.get("website"):
            print(f"網站: {info['website']}")

        if info.get("address"):
            print(f"地址: {info['address']}")

        print("=" * 50 + "\n")

    def export_to_vcard(self, info: Dict, output_path: str):
        """匯出為vCard格式"""
        vcard = "BEGIN:VCARD\nVERSION:3.0\n"

        if info.get("name"):
            vcard += f"FN:{info['name']}\n"

        if info.get("title"):
            vcard += f"TITLE:{info['title']}\n"

        if info.get("company"):
            vcard += f"ORG:{info['company']}\n"

        if info.get("phone") and len(info["phone"]) > 0:
            vcard += f"TEL:{info['phone'][0]}\n"

        if info.get("email"):
            vcard += f"EMAIL:{info['email']}\n"

        if info.get("website"):
            vcard += f"URL:{info['website']}\n"

        if info.get("address"):
            vcard += f"ADR:{info['address']}\n"

        vcard += "END:VCARD"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(vcard)

        print(f"vCard已儲存至: {output_path}")


def main():
    """主程式"""
    if len(sys.argv) < 2:
        print("使用方法: python business_card_scanner.py <圖片路徑或資料夾>")
        print("範例: python business_card_scanner.py card.jpg")
        print("      python business_card_scanner.py cards/")
        return

    input_path = Path(sys.argv[1])

    # 初始化掃描器
    scanner = BusinessCardScanner()

    # 處理輸入
    if input_path.is_file():
        # 單一檔案
        info = scanner.scan_card(str(input_path))
        scanner.print_card_info(info)

        # 儲存結果
        json_file = input_path.stem + "_contact.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        print(f"JSON已儲存至: {json_file}")

        # 匯出vCard
        vcard_file = input_path.stem + ".vcf"
        scanner.export_to_vcard(info, vcard_file)

    elif input_path.is_dir():
        # 批次處理
        image_files = (
            list(input_path.glob("*.jpg"))
            + list(input_path.glob("*.png"))
            + list(input_path.glob("*.jpeg"))
        )

        if not image_files:
            print("未找到圖片檔案")
            return

        print(f"找到 {len(image_files)} 個圖片檔案\n")

        all_contacts = []
        for i, img_file in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}]")
            info = scanner.scan_card(str(img_file))
            scanner.print_card_info(info)
            all_contacts.append(info)

            # 匯出vCard
            vcard_file = img_file.stem + ".vcf"
            scanner.export_to_vcard(info, vcard_file)

        # 儲存批次結果
        with open("contacts_batch.json", "w", encoding="utf-8") as f:
            json.dump(all_contacts, f, ensure_ascii=False, indent=2)
        print(f"\n批次結果已儲存至: contacts_batch.json")

    else:
        print(f"路徑不存在: {input_path}")


if __name__ == "__main__":
    main()
