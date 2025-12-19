# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - 語義處理器

使用 LLM 提升 OCR 結果的語義準確性：
- 自動修正錯別字
- 最佳化語句流暢度
- 提取結構化資料
- 檔案分類與摘要
"""

import logging
from typing import Any, Dict, List, Optional

from paddleocr_toolkit.llm import create_llm_client, LLMClient
from paddleocr_toolkit.llm.llm_client import HAS_REQUESTS


class SemanticProcessor:
    """
    語義處理器 - LLM 驅動的 OCR 後處理
    
    利用大型語言模型自動修正 OCR 識別中的常見錯誤，
    提升文字的語義準確性和可讀性。
    
    Attributes:
        llm_client: LLM 客戶端
        
    Example:
        >>> from paddleocr_toolkit.processors import SemanticProcessor
        >>> 
        >>> processor = SemanticProcessor(
        ...     llm_provider="ollama",
        ...     model="qwen2.5:14b"
        ... )
        >>> 
        >>> ocr_text = "這個文建可能有銷別字"
        >>> corrected = processor.correct_ocr_errors(ocr_text)
        >>> print(corrected)  # "這個檔案可能有錯別字"
    """
    
    def __init__(
        self,
        llm_provider: str = "ollama",
        model: Optional[str] = None,
        **llm_kwargs
    ):
        """
        初始化語義處理器
        
        Args:
            llm_provider: LLM 提供商 ("ollama", "openai")
            model: 模型名稱（可選，使用預設值）
            **llm_kwargs: LLM 客戶端的額外引數
        """
        # 設定預設模型
        if model is None:
            model = "qwen2.5:7b" if llm_provider == "ollama" else "gpt-3.5-turbo"
        
        try:
            self.llm_client = create_llm_client(
                provider=llm_provider,
                model=model,
                **llm_kwargs
            )
            
            # 檢查服務可用性
            if self.llm_client.is_available():
                print(f"語義處理器已就緒 (模型: {self.llm_client.model})")
            else:
                print(f"警告: LLM 服務 ({self.llm_client.provider}) 目前無法使用，功能將受限。")       
        except Exception as e:
            logging.error(f"初始化 LLM 客戶端失敗: {e}")
            self.llm_client = None
    
    def is_enabled(self) -> bool:
        """檢查語義處理是否啟用"""
        return self.llm_client is not None
    
    def correct_ocr_errors(
        self,
        text: str,
        context: str = "",
        language: str = "zh"
    ) -> str:
        """
        使用 LLM 修正 OCR 錯誤
        
        Args:
            text: OCR 識別的原始文字
            context: 額外的上下文資訊（可選）
            language: 文字語言（"zh", "en" 等）
        
        Returns:
            str: 修正後的文字
        """
        if not self.is_enabled():
            logging.warning("語義處理未啟用，返回原始文字")
            return text
        
        # 構建提示詞
        if language == "zh":
            prompt = self._build_chinese_correction_prompt(text, context)
        else:
            prompt = self._build_english_correction_prompt(text, context)
        
        try:
            corrected_text = self.llm_client.generate(
                prompt,
                temperature=0.3,  # 較低溫度保持準確性
                max_tokens=len(text) * 2  # 預留足夠空間
            )
            
            if corrected_text:
                return corrected_text
            else:
                logging.warning("LLM 返回空結果，返回原始文字")
                return text
        
        except Exception as e:
            logging.error(f"語義修正失敗: {e}")
            return text
    
    def _build_chinese_correction_prompt(self, text: str, context: str) -> str:
        """建立中文修正提示詞"""
        prompt = f"""你是一個專業的繁體中文 OCR 文字校對助手。
以下文字是從圖片識別出來的，可能包含錯別字、標點符號錯誤或語句不通順的地方。

**重要規則**：
1. **必須使用繁體中文輸出**，不可轉換為簡體中文
2. 只修正明顯的 OCR 錯誤（如：文建→檔案、銷別字→錯別字、工見→工具）
3. 保持原文的格式、結構和換行
4. 不要新增任何額外的說明或解釋
5. 如果不確定是否為錯誤，保持原樣
6. 保留所有專有名詞（如：PaddleOCR、Processor 等）

原始文字：
{text}
"""
        
        if context:
            prompt += f"\n上下文資訊：\n{context}\n"
        
        prompt += "\n修正後的文字（必須使用繁體中文）："
        return prompt
    
    def _build_english_correction_prompt(self, text: str, context: str) -> str:
        """建立英文修正提示詞"""
        prompt = f"""You are a professional OCR text proofreader.
The following text was extracted from an image and may contain errors.

Please correct these errors following these rules:
1. Only fix obvious mistakes, don't change the original meaning
2. Preserve the original format and structure
3. Don't add any extra content or explanations
4. If uncertain, keep it as is

Original text:
{text}
"""
        
        if context:
            prompt += f"\nContext:\n{context}\n"
        
        prompt += "\nCorrected text:"
        return prompt
    
    def extract_structured_data(
        self,
        text: str,
        schema: Dict[str, Any],
        language: str = "zh"
    ) -> Dict[str, Any]:
        """
        根據 Schema 提取結構化資料
        
        Args:
            text: 源文字
            schema: JSON Schema 定義
            language: 語言
        
        Returns:
            Dict: 提取的結構化資料
        """
        if not self.is_enabled():
            logging.warning("語義處理未啟用")
            return {}
        
        prompt = f"""請從以下文字中提取資料，並按照指定的 JSON 格式輸出。

JSON Schema:
{schema}

文字內容：
{text}

請僅返回 JSON 格式的結果，不要包含其他說明：
"""
        
        try:
            response = self.llm_client.generate(prompt, temperature=0.1)
            
            # 嘗試解析 JSON
            import json
            # 移除可能的 markdown 標記
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1])
            
            return json.loads(response)
        
        except Exception as e:
            logging.error(f"結構化資料提取失敗: {e}")
            return {}
    
    def summarize_document(self, text: str, max_length: int = 200) -> str:
        """
        生成檔案摘要
        
        Args:
            text: 檔案內容
            max_length: 摘要最大長度
        
        Returns:
            str: 摘要文字
        """
        if not self.is_enabled():
            return text[:max_length] + "..."
        
        prompt = f"""請為以下文字生成一個簡潔的摘要，長度不超過 {max_length} 字。

文字：
{text}

摘要：
"""
        
        try:
            summary = self.llm_client.generate(prompt, temperature=0.5)
            return summary[:max_length]
        except Exception as e:
            logging.error(f"生成摘要失敗: {e}")
            return text[:max_length] + "..."
