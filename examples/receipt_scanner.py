#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📱 發票掃描器 - PaddleOCR Toolkit 示例項目
自動從發票圖片中提取關鍵資訊：金額、日期、商家名稱

使用方法:
    python receipt_scanner.py receipt.jpg
    python receipt_scanner.py receipts/  # 批次處理
"""

import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import json

# 導入PaddleOCR Toolkit
sys.path.insert(0, str(Path(__file__).parent.parent))

from paddle_ocr_tool import PaddleOCRTool


class ReceiptScanner:
    """發票掃描器"""
    
    def __init__(self):
        """初始化OCR引擎"""
        print("🔧 初始化 OCR 引擎...")
        self.ocr_tool = PaddleOCRTool(mode="basic", device="gpu")
        print("✅ OCR 引擎就緒！\n")
    
    def scan_receipt(self, image_path: str) -> Dict:
        """
        掃描發票並提取資訊
        
        Args:
            image_path: 發票圖片路徑
            
        Returns:
            包含發票資訊的字典
        """
        print(f"📷 掃描發票: {image_path}")
        
        # OCR識別
        results = self.ocr_tool.process_image(image_path)
        
        # 合併所有文字
        all_text = "\n".join([r.text for r in results])
        
        # 提取資訊
        receipt_info = {
            "file": str(image_path),
            "scan_time": datetime.now().isoformat(),
            "total_amount": self._extract_amount(all_text, results),
            "date": self._extract_date(all_text),
            "merchant": self._extract_merchant(results),
            "items": self._extract_items(results),
            "raw_text": all_text
        }
        
        return receipt_info
    
    def _extract_amount(self, text: str, results: List) -> Optional[float]:
        """提取總金額"""
        # 尋找金額模式
        patterns = [
            r'總[計金額]*[:：\s]*[\$NT]*\s*([\d,]+\.?\d*)',
            r'合[計金額]*[:：\s]*[\$NT]*\s*([\d,]+\.?\d*)',
            r'Total[:：\s]*[\$NT]*\s*([\d,]+\.?\d*)',
            r'[\$NT]\s*([\d,]+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        
        # 備用：查找最大的數字
        numbers = re.findall(r'([\d,]+\.?\d*)', text)
        if numbers:
            amounts = []
            for num in numbers:
                try:
                    amounts.append(float(num.replace(',', '')))
                except ValueError:
                    continue
            if amounts:
                return max(amounts)
        
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """提取日期"""
        # 日期模式 YYYY/MM/DD, YYYY-MM-DD, MM/DD/YYYY
        patterns = [
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_merchant(self, results: List) -> Optional[str]:
        """提取商家名稱（通常在發票頂部）"""
        if results:
            # 假設商家名稱在前3行
            top_lines = results[:3]
            for result in top_lines:
                # 跳過純數字
                if not result.text.replace(' ', '').isdigit():
                    return result.text
        return None
    
    def _extract_items(self, results: List) -> List[str]:
        """提取商品項目"""
        items = []
        for result in results:
            text = result.text.strip()
            # 跳過太短、純數字、金額符號的行
            if len(text) > 3 and not text.replace(' ', '').isdigit():
                if not any(symbol in text for symbol in ['$', 'NT', '總計', '合計', 'Total']):
                    items.append(text)
        return items[:10]  # 最多10項
    
    def print_receipt_info(self, info: Dict):
        """美化顯示發票資訊"""
        print("\n" + "="*50)
        print("📋 發票掃描結果")
        print("="*50)
        
        if info.get('merchant'):
            print(f"🏪 商家: {info['merchant']}")
        
        if info.get('date'):
            print(f"📅 日期: {info['date']}")
        
        if info.get('total_amount'):
            print(f"💰 總金額: NT$ {info['total_amount']:,.2f}")
        else:
            print(f"💰 總金額: 未找到")
        
        if info.get('items'):
            print(f"\n📦 商品項目 ({len(info['items'])} 項):")
            for i, item in enumerate(info['items'][:5], 1):
                print(f"   {i}. {item}")
        
        print("="*50 + "\n")
    
    def save_results(self, results: List[Dict], output_path: str):
        """儲存結果為JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"💾 結果已儲存至: {output_path}")


def main():
    """主程式"""
    if len(sys.argv) < 2:
        print("使用方法: python receipt_scanner.py <圖片路徑或資料夾>")
        print("範例: python receipt_scanner.py receipt.jpg")
        print("      python receipt_scanner.py receipts/")
        return
    
    input_path = Path(sys.argv[1])
    
    # 初始化掃描器
    scanner = ReceiptScanner()
    
    # 處理輸入
    if input_path.is_file():
        # 單個檔案
        info = scanner.scan_receipt(str(input_path))
        scanner.print_receipt_info(info)
        
        # 儲存結果
        output_file = input_path.stem + "_result.json"
        scanner.save_results([info], output_file)
        
    elif input_path.is_dir():
        # 批次處理
        image_files = list(input_path.glob("*.jpg")) + \
                     list(input_path.glob("*.png")) + \
                     list(input_path.glob("*.jpeg"))
        
        if not image_files:
            print("❌ 未找到圖片檔案")
            return
        
        print(f"📂 找到 {len(image_files)} 個圖片檔案\n")
        
        all_results = []
        for i, img_file in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}]")
            info = scanner.scan_receipt(str(img_file))
            scanner.print_receipt_info(info)
            all_results.append(info)
        
        # 儲存批次結果
        output_file = "receipts_batch_result.json"
        scanner.save_results(all_results, output_file)
        
        # 統計摘要
        print("\n" + "="*50)
        print("📊 批次處理摘要")
        print("="*50)
        total_amount = sum([r.get('total_amount', 0) or 0 for r in all_results])
        valid_amounts = sum([1 for r in all_results if r.get('total_amount')])
        
        print(f"總發票數: {len(all_results)}")
        print(f"成功提取金額: {valid_amounts}/{len(all_results)}")
        print(f"總金額: NT$ {total_amount:,.2f}")
        print("="*50)
    
    else:
        print(f"❌ 路徑不存在: {input_path}")


if __name__ == "__main__":
    main()
