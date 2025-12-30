# -*- coding: utf-8 -*-
"""
文件分類插件
範例插件：根據關鍵字自動分類文件類型
"""
from typing import Any, List
from paddleocr_toolkit.plugins.base import PostprocessorPlugin

class DocClassifierPlugin(PostprocessorPlugin):
    name = "Document Classifier"
    version = "1.0.0"
    author = "PaddleOCR Team"
    description = "根據關鍵字自動分類文件 (發票/合約/證件)"

    def on_init(self) -> bool:
        return True

    def on_after_ocr(self, results: List[Any]) -> List[Any]:
        """
        分析全文關鍵字進行分類
        """
        # 提取全文
        full_text = ""
        for res in results:
            text = getattr(res, "text", None) or res.get("text", "")
            full_text += text + " "
            
        doc_type = "Unknown"
        confidence = 0.0
        
        if any(k in full_text for k in ["發票", "Invoice", "稅額", "統一編號"]):
            doc_type = "Invoice"
            confidence = 0.9
        elif any(k in full_text for k in ["合約", "協議書", "Contract", "甲方", "乙方"]):
            doc_type = "Contract"
            confidence = 0.85
        elif any(k in full_text for k in ["身分證", "ID Card", "駕照", "Passport"]):
            doc_type = "ID Card"
            confidence = 0.95
            
        self.logger.info(f"文件分類結果: {doc_type} ({confidence:.2f})")
        
        # 將分類結果附加到第一個 OCR 結果的 metadata (如果有的話)
        # 這裡僅作示例 log 輸出
        
        return results
