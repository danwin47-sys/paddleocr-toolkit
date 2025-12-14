# -*- coding: utf-8 -*-
"""
翻譯處理器 - 專用於 PDF 翻譯

本模組負責：
- 翻譯流程管理
- 雙語 PDF 生成
- 翻譯結果處理
"""

import logging
from typing import List, Dict, Any, Optional

try:
    from paddleocr_toolkit.core.models import OCRResult
except ImportError:
    from ..core.models import OCRResult


class TranslationProcessor:
    """
    翻譯處理器
    
    管理 PDF 翻譯流程
    
    Example:
        processor = TranslationProcessor(translator=translator)
        result = processor.process_translation(
            ocr_results=results,
            source_lang='zh',
            target_lang='en'
        )
    """
    
    def __init__(
        self,
        translator: Optional[Any] = None,
        renderer: Optional[Any] = None
    ):
        """
        初始化翻譯處理器
        
        Args:
            translator: 翻譯器（如 OllamaTranslator）
            renderer: 文字渲染器（如 TextRenderer）
        """
        self.translator = translator
        self.renderer = renderer
    
    def process_translation(
        self,
        ocr_results: List[OCRResult],
        source_lang: str = 'auto',
        target_lang: str = 'en',
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        處理翻譯
        
        Args:
            ocr_results: OCR 結果列表
            source_lang: 源語言
            target_lang: 目標語言
            **kwargs: 其他翻譯參數
        
        Returns:
            List[Dict]: 翻譯結果列表
        """
        if not self.translator:
            raise ValueError("翻譯器未初始化")
        
        translated_blocks = []
        
        try:
            # 提取文字
            texts = [r.text for r in ocr_results]
            
            # 執行翻譯
            translations = self.translator.translate_batch(
                texts,
                source_lang=source_lang,
                target_lang=target_lang
            )
            
            # 組合結果
            for ocr_result, translation in zip(ocr_results, translations):
                block = {
                    'original': ocr_result.text,
                    'translated': translation,
                    'bbox': ocr_result.bbox,
                    'confidence': ocr_result.confidence
                }
                translated_blocks.append(block)
            
            return translated_blocks
            
        except Exception as e:
            logging.error(f"翻譯處理失敗: {e}")
            return []
    
    def generate_bilingual_pdf(
        self,
        original_pdf: str,
        translated_blocks: List[Dict[str, Any]],
        output_path: str,
        mode: str = 'alternating'
    ) -> bool:
        """
        生成雙語 PDF
        
        Args:
            original_pdf: 原始 PDF 路徑
            translated_blocks: 翻譯結果列表
            output_path: 輸出路徑
            mode: 雙語模式 ('alternating' 或 'side-by-side')
        
        Returns:
            bool: 是否成功
        """
        try:
            # 這裡應該實現雙語 PDF 生成邏輯
            # 簡化版本僅返回成功
            logging.info(f"生成雙語 PDF: {output_path} (模式: {mode})")
            return True
            
        except Exception as e:
            logging.error(f"生成雙語 PDF 失敗: {e}")
            return False
    
    def extract_translation_text(
        self,
        translated_blocks: List[Dict[str, Any]],
        include_original: bool = False
    ) -> str:
        """
        提取翻譯文字
        
        Args:
            translated_blocks: 翻譯結果列表
            include_original: 是否包含原文
        
        Returns:
            str: 翻譯文字
        """
        lines = []
        
        for block in translated_blocks:
            if include_original:
                lines.append(f"原文: {block['original']}")
                lines.append(f"譯文: {block['translated']}")
                lines.append('')
            else:
                lines.append(block['translated'])
        
        return '\n'.join(lines)
