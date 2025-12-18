# -*- coding: utf-8 -*-
"""
翻譯處理器 - 專用於 PDF 翻譯（增強版）

本模組負責：
- 翻譯流程管理
- 雙語 PDF 生成
- 翻譯結果處理
- PDF 文字渲染
"""

import logging
import os
import traceback
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

try:
    import fitz  # PyMuPDF

    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    from tqdm import tqdm

    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

if TYPE_CHECKING:
    from pdf_translator import (
        BilingualPDFGenerator,
        MonolingualPDFGenerator,
        OllamaTranslator,
        TextRenderer,
        TranslatedBlock,
    )

try:
    from paddleocr_toolkit.core.models import OCRResult
except ImportError:
    from ..core.models import OCRResult


class EnhancedTranslationProcessor:
    """
    增強版翻譯處理器

    整合完整的 PDF 翻譯流程，包括：
    - Ollama 翻譯器設定
    - 文字渲染器
    - 雙語/單語 PDF 生成
    - 批次翻譯處理

    Example:
        >>> processor = EnhancedTranslationProcessor()
        >>> result = processor.process_pdf_translation(
        ...     erased_pdf_path="document_erased.pdf",
        ...     ocr_results_per_page=ocr_results,
        ...     translate_config={...}
        ... )
    """

    def __init__(self):
        """初始化增強版翻譯處理器"""
        self.translator = None
        self.renderer = None

    def process_pdf_translation(
        self,
        erased_pdf_path: str,
        ocr_results_per_page: List[List[OCRResult]],
        translate_config: Dict[str, Any],
        result_summary: Optional[Dict[str, Any]] = None,
        dpi: int = 150,
    ) -> Dict[str, Any]:
        """
        在擦除版 PDF 基礎上進行翻譯處理

        流程：
        1. 打開 *_erased.pdf（已擦除）
        2. 翻譯文字
        3. 在擦除後的圖片上繪製翻譯文字

        Args:
            erased_pdf_path: 已擦除的 PDF 路徑（*_erased.pdf）
            ocr_results_per_page: 每頁的 OCR 結果列表
            translate_config: 翻譯配置
            result_summary: 結果摘要（會被更新）
            dpi: PDF 轉圖片時使用的 DPI

        Returns:
            Dict[str, Any]: 翻譯結果摘要
        """
        if result_summary is None:
            result_summary = {}

        print(f"\n[翻譯] 開始翻譯處理...")
        logging.info(f"開始翻譯處理: {erased_pdf_path}")

        print(f"   來源語言: {translate_config.get('source_lang', 'auto')}")
        print(f"   目標語言: {translate_config.get('target_lang', 'en')}")
        print(f"   Ollama 模型: {translate_config.get('ollama_model', 'qwen2.5:7b')}")

        try:
            # === 1. 初始化工具 ===
            translation_setup = self.setup_translation_tools(
                erased_pdf_path, translate_config
            )

            if not translation_setup:
                result_summary["translation_error"] = "翻譯工具初始化失敗"
                return result_summary

            (
                translator,
                renderer,
                pdf_doc,
                hybrid_doc,
                mono_gen,
                bilingual_gen,
                trans_path,
                bi_path,
            ) = translation_setup

            total_pages = len(pdf_doc)

            # === 2. 處理所有頁面 ===
            page_iter = range(total_pages)
            if HAS_TQDM:
                page_iter = tqdm(page_iter, desc="翻譯頁面", unit="頁", ncols=80)

            for page_num in page_iter:
                try:
                    if page_num >= len(ocr_results_per_page):
                        logging.warning(f"第 {page_num + 1} 頁沒有 OCR 結果")
                        continue

                    page_ocr_results = ocr_results_per_page[page_num]

                    # 翻譯頁面文字
                    translated_blocks = self.translate_page_texts(
                        page_ocr_results,
                        translator,
                        translate_config.get("source_lang", "auto"),
                        translate_config.get("target_lang", "en"),
                        page_num,
                    )

                    # 渲染翻譯文字到 PDF
                    if translated_blocks:
                        self._render_translations_to_pdf(
                            page_num,
                            translated_blocks,
                            pdf_doc,
                            hybrid_doc,
                            renderer,
                            mono_gen,
                            bilingual_gen,
                            dpi,
                        )

                except Exception as page_err:
                    logging.error(f"翻譯第 {page_num + 1} 頁時發生錯誤: {page_err}")
                    logging.error(traceback.format_exc())
                    continue

            # === 3. 儲存輸出 ===
            pdf_doc.close()
            if hybrid_doc:
                hybrid_doc.close()

            self._save_translation_pdfs(
                mono_gen, bilingual_gen, trans_path, bi_path, result_summary
            )

            print(f"[OK] 翻譯處理完成")
            return result_summary

        except Exception as e:
            error_msg = f"翻譯處理失敗: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            print(f"錯誤：{error_msg}")
            result_summary["translation_error"] = str(e)
            return result_summary

    def setup_translation_tools(
        self, erased_pdf_path: str, translate_config: Dict[str, Any]
    ) -> Optional[Tuple]:
        """
        設定翻譯所需的工具和生成器

        Args:
            erased_pdf_path: 擦除版 PDF 路徑
            translate_config: 翻譯配置

        Returns:
            Tuple of (translator, renderer, pdf_doc, hybrid_doc,
                      mono_generator, bilingual_generator,
                      translated_path, bilingual_path)
            或 None（如果設定失敗）
        """
        try:
            # 動態導入翻譯模組
            from pdf_translator import (
                BilingualPDFGenerator,
                MonolingualPDFGenerator,
                OllamaTranslator,
                TextRenderer,
            )

            # 初始化翻譯器和繪製器
            translator = OllamaTranslator(
                model=translate_config["ollama_model"],
                base_url=translate_config["ollama_url"],
            )
            renderer = TextRenderer(font_path=translate_config.get("font_path"))

            # 打開 PDF
            pdf_doc = fitz.open(erased_pdf_path)

            # 打開原始 hybrid PDF（用於雙語）
            hybrid_pdf_path = erased_pdf_path.replace("_erased.pdf", "_hybrid.pdf")
            hybrid_doc = None
            if not translate_config["no_dual"] and os.path.exists(hybrid_pdf_path):
                hybrid_doc = fitz.open(hybrid_pdf_path)

            # 建立輸出路徑
            base_path = erased_pdf_path.replace("_erased.pdf", "")
            target_lang = translate_config["target_lang"]
            translated_path = (
                f"{base_path}_translated_{target_lang}.pdf"
                if not translate_config["no_mono"]
                else None
            )
            bilingual_path = (
                f"{base_path}_bilingual_{target_lang}.pdf"
                if not translate_config["no_dual"]
                else None
            )

            # 建立生成器
            mono_generator = MonolingualPDFGenerator() if translated_path else None
            bilingual_generator = (
                BilingualPDFGenerator(
                    mode=translate_config["dual_mode"],
                    translate_first=translate_config.get("dual_translate_first", False),
                )
                if bilingual_path
                else None
            )

            self.translator = translator
            self.renderer = renderer

            return (
                translator,
                renderer,
                pdf_doc,
                hybrid_doc,
                mono_generator,
                bilingual_generator,
                translated_path,
                bilingual_path,
            )

        except ImportError as e:
            logging.error(f"翻譯模組導入失敗: {e}")
            return None
        except Exception as e:
            logging.error(f"翻譯工具設定失敗: {e}")
            logging.error(traceback.format_exc())
            return None

    def translate_page_texts(
        self,
        page_ocr_results: List[OCRResult],
        translator: Any,
        source_lang: str,
        target_lang: str,
        page_num: int,
    ) -> List[Any]:
        """
        翻譯頁面的所有文字

        Args:
            page_ocr_results: 頁面的 OCR 結果
            translator: 翻譯器物件
            source_lang: 來源語言
            target_lang: 目標語言
            page_num: 頁碼（0-based）

        Returns:
            List[TranslatedBlock]: 翻譯後的文字塊列表
        """
        try:
            from pdf_translator import TranslatedBlock
        except ImportError:
            logging.error("TranslatedBlock 類別導入失敗")
            return []

        # 收集需要翻譯的文字
        texts_to_translate = []
        bboxes = []
        for result in page_ocr_results:
            if result.text and result.text.strip():
                texts_to_translate.append(result.text)
                bboxes.append(result.bbox)

        if not texts_to_translate:
            return []

        logging.info(f"第 {page_num + 1} 頁: 翻譯 {len(texts_to_translate)} 個文字區塊")

        try:
            # 批次翻譯
            translated_texts = translator.translate_batch(
                texts_to_translate, source_lang, target_lang, show_progress=False
            )

            # 建立 TranslatedBlock 列表
            translated_blocks = []
            for orig, trans, bbox in zip(texts_to_translate, translated_texts, bboxes):
                translated_blocks.append(
                    TranslatedBlock(original_text=orig, translated_text=trans, bbox=bbox)
                )

            return translated_blocks

        except Exception as e:
            logging.error(f"頁面翻譯失敗: {e}")
            return []

    def _render_translations_to_pdf(
        self,
        page_num: int,
        translated_blocks: List[Any],
        pdf_doc,
        hybrid_doc,
        renderer,
        mono_gen,
        bilingual_gen,
        dpi: int,
    ) -> None:
        """渲染翻譯文字到 PDF 頁面"""
        try:
            page = pdf_doc[page_num]
            pixmap = page.get_pixmap(dpi=dpi)

            # 渲染翻譯文字
            from paddleocr_toolkit.core.pdf_utils import pixmap_to_numpy

            img_array = pixmap_to_numpy(pixmap)

            if mono_gen:
                translated_img = renderer.render_multiple_texts(
                    img_array, translated_blocks, draw_original=False
                )
                mono_gen.add_page(translated_img)

            if bilingual_gen and hybrid_doc:
                hybrid_page = hybrid_doc[page_num]
                hybrid_pixmap = hybrid_page.get_pixmap(dpi=dpi)
                hybrid_img = pixmap_to_numpy(hybrid_pixmap)

                translated_img = renderer.render_multiple_texts(
                    img_array, translated_blocks, draw_original=False
                )

                bilingual_gen.add_page_pair(hybrid_img, translated_img)

        except Exception as e:
            logging.error(f"渲染第 {page_num + 1} 頁時發生錯誤: {e}")

    def _save_translation_pdfs(
        self, mono_gen, bilingual_gen, trans_path, bi_path, result_summary
    ) -> None:
        """儲存翻譯 PDF"""
        if mono_gen and trans_path:
            try:
                mono_gen.save(trans_path)
                result_summary["translated_pdf"] = trans_path
                print(f"[OK] 純翻譯 PDF: {trans_path}")
            except Exception as e:
                logging.error(f"儲存純翻譯 PDF 失敗: {e}")

        if bilingual_gen and bi_path:
            try:
                bilingual_gen.save(bi_path)
                result_summary["bilingual_pdf"] = bi_path
                print(f"[OK] 雙語對照 PDF: {bi_path}")
            except Exception as e:
                logging.error(f"儲存雙語 PDF 失敗: {e}")


# 向後相容：保留舊的 TranslationProcessor 名稱
TranslationProcessor = EnhancedTranslationProcessor
