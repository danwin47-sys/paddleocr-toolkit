# -*- coding: utf-8 -*-
"""
PaddleOCR Facade - 輕量級 API 層

本模組提供簡化的公開 API，內部委派給各個專業 Processor。
這是現代化架構的主入口，替代傳統的 paddle_ocr_tool.py。

Example:
    >>> from paddle_ocr_facade import PaddleOCRFacade
    >>> 
    >>> # 基本使用
    >>> tool = PaddleOCRFacade(mode="hybrid")
    >>> result = tool.process("document.pdf")
    >>> 
    >>> # 帶翻譯
    >>> result = tool.process("document.pdf", translate=True, target_lang="en")
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from paddleocr_toolkit.core import OCRMode
from paddleocr_toolkit.core.ocr_engine import OCREngineManager


class PaddleOCRFacade:
    """
    PaddleOCR Facade - 輕量級 API 層

    提供統一的介面，內部委派給專業的 Processor 處理。

    Attributes:
        mode: OCR 模式
        engine_manager: OCR 引擎管理器
        debug_mode: 除錯模式
        compress_images: 是否壓縮圖片
        jpeg_quality: JPEG 壓縮品質

    Example:
        >>> facade = PaddleOCRFacade(mode="hybrid")
        >>> result = facade.process_hybrid("input.pdf", "output.pdf")
    """

    def __init__(
        self,
        mode: str = "basic",
        use_orientation_classify: bool = False,
        use_doc_unwarping: bool = False,
        use_textline_orientation: bool = False,
        device: str = "cpu",
        debug_mode: bool = False,
        compress_images: bool = True,
        jpeg_quality: int = 85,
        enable_semantic: bool = False,
        llm_provider: str = "ollama",
        llm_model: Optional[str] = None,
    ):
        """
        初始化 PaddleOCR Facade

        Args:
            mode: OCR 模式 ('basic', 'structure', 'vl', 'hybrid', 'formula')
            use_orientation_classify: 是否啟用檔案方向自動校正
            use_doc_unwarping: 是否啟用檔案彎曲校正
            use_textline_orientation: 是否啟用文字行方向偵測
            device: 運算裝置 ('gpu' 或 'cpu')
            debug_mode: DEBUG 模式（顯示粉紅色文字層）
            compress_images: 啟用 JPEG 壓縮以減少 PDF 檔案大小
            jpeg_quality: JPEG 壓縮品質（0-100）
            enable_semantic: 啟用語義處理（LLM 自動修正 OCR 錯誤）
            llm_provider: LLM 提供商 ('ollama', 'openai')
            llm_model: LLM 模型名稱（可選）
        """
        self.mode = mode
        self.debug_mode = debug_mode
        self.compress_images = compress_images
        self.jpeg_quality = jpeg_quality
        self.device = device
        self.enable_semantic = enable_semantic
        self.llm_provider = llm_provider
        self.llm_model = llm_model

        # 初始化 OCR 引擎管理器
        self.engine_manager = OCREngineManager(
            mode=mode,
            device=device,
            use_orientation_classify=use_orientation_classify,
            use_doc_unwarping=use_doc_unwarping,
            use_textline_orientation=use_textline_orientation,
        )
        self.engine_manager.init_engine()

        # 初始化對應的 Processor
        self._init_processors()

        # 初始化語義處理器（可選）
        self.semantic_processor = None
        if enable_semantic:
            try:
                from paddleocr_toolkit.processors.semantic_processor import (
                    SemanticProcessor,
                )

                self.semantic_processor = SemanticProcessor(
                    llm_provider=llm_provider, model=llm_model
                )
                if self.semantic_processor.is_enabled():
                    logging.info(
                        f"SemanticProcessor 已啟用：{llm_provider}/{llm_model or 'default'}"
                    )
                else:
                    logging.warning("SemanticProcessor 初始化失敗，功能已禁用")
                    self.semantic_processor = None
            except Exception as e:
                logging.error(f"SemanticProcessor 初始化錯誤: {e}")
                self.semantic_processor = None

        logging.info(
            f"PaddleOCRFacade 初始化完成：mode={mode}, device={device}, semantic={enable_semantic}"
        )

    def _init_processors(self):
        """根據模式初始化對應的 Processor"""
        if self.mode == "hybrid":
            from paddleocr_toolkit.processors.hybrid_processor import (
                HybridPDFProcessor,
            )

            self.hybrid_processor = HybridPDFProcessor(
                self.engine_manager,
                debug_mode=self.debug_mode,
                compress_images=self.compress_images,
                jpeg_quality=self.jpeg_quality,
            )
            logging.info("HybridPDFProcessor 初始化完成")

        elif self.mode == "basic":
            from paddleocr_toolkit.processors.basic_processor import BasicProcessor

            self.basic_processor = BasicProcessor(
                self.engine_manager,
                debug_mode=self.debug_mode,
                compress_images=self.compress_images,
                jpeg_quality=self.jpeg_quality,
            )
            logging.info("BasicProcessor 初始化完成")

        elif self.mode == "structure":
            from paddleocr_toolkit.processors.structure_processor import (
                StructureProcessor,
            )

            self.structure_processor = StructureProcessor(self.engine_manager)
            logging.info("StructureProcessor 初始化完成")

        elif self.mode == "formula":
            from paddleocr_toolkit.processors.formula_processor import FormulaProcessor

            self.formula_processor = FormulaProcessor(self.engine_manager)
            logging.info("FormulaProcessor 初始化完成")

    def process(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        統一處理介面（根據模式自動選擇 Processor）

        Args:
            input_path: 輸入檔案路徑
            output_path: 輸出檔案路徑（可選）
            **kwargs: 其他引數

        Returns:
            Dict[str, Any]: 處理結果

        Raises:
            ValueError: 當模式不支援時
        """
        if self.mode == "hybrid":
            return self.process_hybrid(input_path, output_path, **kwargs)
        elif self.mode == "structure":
            return self.process_structured(input_path, output_path, **kwargs)
        elif self.mode == "formula":
            return self.process_formula(input_path, output_path, **kwargs)
        elif self.mode == "basic":
            return self.process_basic(input_path, output_path, **kwargs)
        else:
            raise ValueError(f"不支援的模式: {self.mode}")

    def process_hybrid(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        markdown_output: Optional[str] = None,
        json_output: Optional[str] = None,
        html_output: Optional[str] = None,
        dpi: int = 150,
        show_progress: bool = True,
        translate_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        混合模式處理（委派給 HybridPDFProcessor）

        Args:
            input_path: 輸入檔案路徑
            output_path: 可搜尋 PDF 輸出路徑
            markdown_output: Markdown 輸出路徑
            json_output: JSON 輸出路徑
            html_output: HTML 輸出路徑
            dpi: PDF 解析度
            show_progress: 是否顯示進度
            translate_config: 翻譯配置（可選）

        Returns:
            Dict[str, Any]: 處理結果
        """
        if self.mode != "hybrid":
            raise ValueError(f"process_hybrid 僅適用於 hybrid 模式，當前: {self.mode}")

        return self.hybrid_processor.process_pdf(
            input_path,
            output_path=output_path,
            markdown_output=markdown_output,
            json_output=json_output,
            html_output=html_output,
            dpi=dpi,
            show_progress=show_progress,
            translate_config=translate_config,
        )

    def process_structured(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        結構化識別模式（委派給 StructureProcessor）

        Args:
            input_path: 輸入檔案路徑
            output_path: 輸出路徑
            **kwargs: 其他引數

        Returns:
            Dict[str, Any]: 處理結果
        """
        if self.mode != "structure":
            raise ValueError(f"process_structured 僅適用於 structure 模式，當前: {self.mode}")

        return self.structure_processor.process(
            input_path, output_path=output_path, **kwargs
        )

    def process_formula(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        公式識別模式（委派給 FormulaProcessor）

        Args:
            input_path: 輸入檔案路徑
            output_path: 輸出路徑
            **kwargs: 其他引數

        Returns:
            Dict[str, Any]: 處理結果
        """
        if self.mode != "formula":
            raise ValueError(f"process_formula 僅適用於 formula 模式，當前: {self.mode}")

        return self.formula_processor.process(
            input_path, output_path=output_path, **kwargs
        )

    def process_basic(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        基本 OCR 模式（委派給 BasicProcessor）

        Args:
            input_path: 輸入檔案路徑
            output_path: 輸出路徑
            **kwargs: 其他引數

        Returns:
            Dict[str, Any]: 處理結果
        """
        if self.mode != "basic":
            raise ValueError(f"process_basic 僅適用於 basic 模式，當前: {self.mode}")

        # 判斷是 PDF 還是圖片
        from pathlib import Path

        file_ext = Path(input_path).suffix.lower()

        if file_ext == ".pdf":
            return self.basic_processor.process_pdf(
                input_path, output_path=output_path, **kwargs
            )
        else:
            # 單張圖片
            return self.basic_processor.process_image(input_path, **kwargs)

    def predict(self, image):
        """
        直接預測（委派給引擎管理器）

        Args:
            image: 輸入圖片

        Returns:
            預測結果
        """
        return self.engine_manager.predict(image)

    def correct_text(self, text: str, language: str = "zh") -> str:
        """
        使用語義處理器修正文字（僅在啟用時可用）

        Args:
            text: 要修正的文字
            language: 語言（"zh" 或 "en"）

        Returns:
            str: 修正後的文字
        """
        if self.semantic_processor and self.semantic_processor.is_enabled():
            return self.semantic_processor.correct_ocr_errors(text, language=language)
        else:
            logging.warning("語義處理未啟用，返回原始文字")
            return text

    def extract_structured_data(
        self, text: str, schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        從文字中提取結構化資料

        Args:
            text: 源文字
            schema: JSON Schema

        Returns:
            Dict: 提取的結構化資料
        """
        if self.semantic_processor and self.semantic_processor.is_enabled():
            return self.semantic_processor.extract_structured_data(text, schema)
        else:
            logging.warning("語義處理未啟用")
            return {}

    def get_engine(self):
        """
        獲取底層 OCR 引擎（用於向後相容）

        Returns:
            OCR 引擎例項
        """
        return self.engine_manager.get_engine()

    def __repr__(self) -> str:
        """字串表示"""
        return f"PaddleOCRFacade(mode={self.mode}, device={self.device})"


# 向後相容：提供舊名稱的別名
PaddleOCRTool = PaddleOCRFacade
