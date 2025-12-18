# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - 解耦版模式處理器

處理不同 OCR 模式的執行和結果顯示。
使用 OCREngineManager + Processors 組合，不依賴 PaddleOCRTool。
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict

from paddleocr_toolkit.core import OCRMode
from paddleocr_toolkit.core.ocr_engine import OCREngineManager

# 支援的檔案格式
SUPPORTED_PDF_FORMAT = ".pdf"
SUPPORTED_IMAGE_FORMATS = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp")


class DecoupledModeProcessor:
    """
    解耦版模式處理器

    直接使用 OCREngineManager 和各個 Processor，
    不依賴 PaddleOCRTool 單體類別。

    封裝了 formula、structure、vl、hybrid、basic 五種模式的處理邏輯。
    """

    def __init__(
        self,
        mode: str,
        args: argparse.Namespace,
        input_path: Path,
        script_dir: Path,
        device: str = "cpu",
        **engine_kwargs,
    ):
        """
        初始化解耦版模式處理器

        Args:
            mode: OCR 模式
            args: 命令列參數
            input_path: 輸入檔案路徑
            script_dir: 腳本所在目錄
            device: 運算設備
            **engine_kwargs: 引擎初始化參數
        """
        self.mode = mode
        self.args = args
        self.input_path = input_path
        self.script_dir = script_dir
        self.show_progress = not args.no_progress

        # 初始化 OCR 引擎管理器
        self.engine_manager = OCREngineManager(
            mode=mode, device=device, **engine_kwargs
        )
        self.engine_manager.init_engine()

        # 根據模式初始化對應的 Processor
        self._init_processors()

    def _init_processors(self):
        """根據模式初始化對應的 Processor"""
        if self.mode == "hybrid":
            from paddleocr_toolkit.processors.hybrid_processor import (
                HybridPDFProcessor,
            )

            self.hybrid_processor = HybridPDFProcessor(
                self.engine_manager,
                debug_mode=getattr(self.args, "debug_text", False),
                compress_images=not getattr(self.args, "no_compress", False),
                jpeg_quality=getattr(self.args, "jpeg_quality", 85),
            )

        # 其他模式可以在這裡初始化對應的 Processor
        # if self.mode == "structure":
        #     self.structure_processor = StructureProcessor(self.engine_manager)

    def process(self) -> Dict[str, Any]:
        """
        根據模式執行處理

        Returns:
            Dict[str, Any]: 處理結果
        """
        if self.args.mode == "formula":
            return self._process_formula()
        elif self.args.mode in ["structure", "vl"]:
            return self._process_structured()
        elif self.args.mode == "hybrid":
            return self._process_hybrid()
        else:  # basic
            return self._process_basic()

    def _process_formula(self) -> Dict[str, Any]:
        """
        處理 formula 模式

        Returns:
            Dict[str, Any]: 處理結果
        """
        # TODO: 使用 FormulaProcessor
        print("Formula 模式尚未重構為 Processor")
        return {"error": "Not implemented"}

    def _process_structured(self) -> Dict[str, Any]:
        """
        處理 structure/vl 模式

        Returns:
            Dict[str, Any]: 處理結果
        """
        # TODO: 使用 StructureProcessor
        print("Structure/VL 模式尚未重構為 Processor")
        return {"error": "Not implemented"}

    def _process_hybrid(self) -> Dict[str, Any]:
        """
        處理 hybrid 模式

        Returns:
            Dict[str, Any]: 處理結果
        """
        # 檢查是否啟用翻譯功能
        if hasattr(self.args, "translate") and self.args.translate:
            return self._process_hybrid_with_translation()
        else:
            return self._process_hybrid_normal()

    def _process_hybrid_with_translation(self) -> Dict[str, Any]:
        """
        處理 hybrid 模式 + 翻譯

        Returns:
            Dict[str, Any]: 處理結果
        """
        # 檢查翻譯模組
        try:
            import pdf_translator

            HAS_TRANSLATOR = True
        except ImportError:
            HAS_TRANSLATOR = False

        if not HAS_TRANSLATOR:
            print("錯誤：翻譯模組不可用")
            print("請確認 pdf_translator.py 存在且依賴已安裝")
            sys.exit(1)

        print(f"[翻譯功能] 啟用")
        print(f"   來源語言：{self.args.source_lang}")
        print(f"   目標語言：{self.args.target_lang}")
        print(f"   Ollama 模型：{self.args.ollama_model}")
        print(f"   純翻譯 PDF：{'停用' if self.args.no_mono else '啟用'}")
        print(
            f"   雙語對照 PDF：{'停用' if self.args.no_dual else f'啟用 ({self.args.dual_mode})'}"
        )

        # 使用 HybridPDFProcessor 處理
        result = self.hybrid_processor.process_pdf(
            str(self.input_path),
            output_path=self.args.output,
            markdown_output=self.args.markdown_output,
            json_output=self.args.json_output,
            html_output=self.args.html_output,
            dpi=self.args.dpi,
            show_progress=self.show_progress,
            translate_config={
                "source_lang": self.args.source_lang,
                "target_lang": self.args.target_lang,
                "ollama_model": self.args.ollama_model,
                "ollama_url": self.args.ollama_url,
                "no_mono": self.args.no_mono,
                "no_dual": self.args.no_dual,
                "dual_mode": self.args.dual_mode,
                "dual_translate_first": self.args.dual_translate_first,
                "font_path": self.args.font_path,
            },
        )

        if result.get("error"):
            print(f"處理過程中發生錯誤: {result['error']}")
        else:
            print(f"\n[OK] 翻譯處理完成！共處理 {result['pages_processed']} 頁")
            if result.get("searchable_pdf"):
                print(f"  [可搜尋 PDF] {result['searchable_pdf']}")
            if result.get("markdown_file"):
                print(f"  [Markdown] {result['markdown_file']}")
            if result.get("translated_pdf"):
                print(f"  [翻譯PDF] {result['translated_pdf']}")
            if result.get("bilingual_pdf"):
                print(f"  [雙語PDF] {result['bilingual_pdf']}")

        return result

    def _process_hybrid_normal(self) -> Dict[str, Any]:
        """
        處理普通 hybrid 模式（無翻譯）

        Returns:
            Dict[str, Any]: 處理結果
        """
        result = self.hybrid_processor.process_pdf(
            str(self.input_path),
            output_path=self.args.output,
            markdown_output=self.args.markdown_output,
            json_output=self.args.json_output,
            html_output=self.args.html_output,
            dpi=self.args.dpi,
            show_progress=self.show_progress,
        )

        if result.get("error"):
            print(f"處理過程中發生錯誤: {result['error']}")
        else:
            print(f"\n[OK] 混合模式處理完成！共處理 {result['pages_processed']} 頁")
            if result.get("searchable_pdf"):
                print(f"  可搜尋 PDF: {result['searchable_pdf']}")
            if result.get("markdown_file"):
                print(f"  Markdown 檔案: {result['markdown_file']}")

        return result

    def _process_basic(self) -> Dict[str, Any]:
        """
        處理 basic 模式

        Returns:
            Dict[str, Any]: 處理結果
        """
        # TODO: 使用 BasicProcessor 或直接使用 OCREngineManager
        print("Basic 模式尚未完全重構")
        return {"error": "Not fully implemented"}


# 向後相容：保留舊名稱（但建議使用新名稱）
ModeProcessor = DecoupledModeProcessor
