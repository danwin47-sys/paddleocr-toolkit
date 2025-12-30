# -*- coding: utf-8 -*-
"""
PII 遮蔽插件
範例插件：自動偵測並遮蔽敏感個人資訊（如身分證號、手機號）
"""
import re
from typing import Any, List, Dict
from paddleocr_toolkit.plugins.base import PostprocessorPlugin

class PIIMaskingPlugin(PostprocessorPlugin):
    name = "PII Masking"
    version = "1.0.0"
    author = "PaddleOCR Team"
    description = "自動遮蔽敏感個資 (手機號、Email、身分證)"

    # 手機號碼正則
    PHONE_PATTERN = re.compile(r"09\d{2}[-\s]?\d{3}[-\s]?\d{3}")
    # Email 正則
    EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
    # 簡易身分證正則
    ID_PATTERN = re.compile(r"[A-Z][12]\d{8}")

    def on_init(self) -> bool:
        self.logger.info("PII Masking 插件已載入")
        return True

    def on_after_ocr(self, results: List[Any]) -> List[Any]:
        """
        遍歷 OCR 結果，遮蔽敏感文字
        注意：這裡假設 results 是 OCRResult 物件列表或字典列表
        """
        masked_count = 0
        
        for res in results:
            # 兼容 OCRResult 物件與字典
            text = getattr(res, "text", None) or res.get("text", "")
            original_text = text
            
            # 手機號遮蔽中間 6 碼
            text = self.PHONE_PATTERN.sub(lambda m: m.group()[:4] + "***" + m.group()[-3:], text)
            
            # Email 遮蔽使用者帳號
            text = self.EMAIL_PATTERN.sub(lambda m: m.group()[0] + "***" + m.group()[m.group().find("@"):], text)
            
            # 身分證遮蔽後 6 碼
            text = self.ID_PATTERN.sub(lambda m: m.group()[:4] + "******", text)
            
            if text != original_text:
                masked_count += 1
                if hasattr(res, "text"):
                    res.text = text
                else:
                    res["text"] = text
                    
        if masked_count > 0:
            self.logger.info(f"已遮蔽 {masked_count} 處敏感資訊")
            
        return results
