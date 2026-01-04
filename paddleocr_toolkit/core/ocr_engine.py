# -*- coding: utf-8 -*-
"""
OCR 引擎管理器 - 管理 PaddleOCR 引擎生命週期

本模組負責：
- OCR 引擎初始化
- 引擎配置管理
- 引擎生命週期管理
- 統一的預測介面
"""

import logging
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from paddleocr_toolkit.utils.logger import logger
from paddleocr_toolkit.core.config import settings

from paddleocr_toolkit.utils.logger import logger

if TYPE_CHECKING:
    from paddleocr_toolkit.plugins.loader import PluginLoader

try:
    from paddleocr import PaddleOCR, PPStructure

    # Export as PPStructureV3 for backward compatibility and tests
    PPStructureV3 = PPStructure
    HAS_STRUCTURE = True
except ImportError:
    PaddleOCR = None  # type: ignore
    PPStructure = None  # type: ignore
    PPStructureV3 = None  # type: ignore
    HAS_STRUCTURE = False

try:
    from paddleocr import PaddleOCRVL

    HAS_VL = True
except ImportError:
    PaddleOCRVL = None  # type: ignore
    HAS_VL = False

try:
    from paddleocr import FormulaRecPipeline

    HAS_FORMULA = True
except ImportError:
    FormulaRecPipeline = None  # type: ignore
    HAS_FORMULA = False


class OCRMode(Enum):
    """OCR 模式列舉"""

    BASIC = "basic"
    STRUCTURE = "structure"
    VL = "vl"
    FORMULA = "formula"
    HYBRID = "hybrid"


class OCREngineManager:
    """
    OCR 引擎管理器

    管理不同模式的 PaddleOCR 引擎，提供統一的介面。

    Attributes:
        mode: OCR 模式
        device: 運算裝置 ('gpu' 或 'cpu')
        config: 引擎配置
        engine: OCR 引擎例項
        structure_engine: 結構化引擎（hybrid 模式用）

    Example:
        manager = OCREngineManager(
            mode="basic",
            device="gpu",
            use_orientation_classify=True
        )
        manager.init_engine()
        result = manager.predict(image)
        manager.close()
    """

    def __init__(
        self,
        mode: str = "basic",
        device: str = "gpu",
        use_orientation_classify: bool = False,
        use_doc_unwarping: bool = False,
        use_textline_orientation: bool = False,
        plugin_loader: Optional["PluginLoader"] = None,
        **kwargs,
    ):
        """
        初始化 OCR 引擎管理器

        Args:
            mode: OCR 模式 ('basic', 'structure', 'vl', 'formula', 'hybrid')
            device: 運算裝置 ('gpu' 或 'cpu')
            use_orientation_classify: 是否啟用檔案方向自動校正
            use_doc_unwarping: 是否啟用檔案彎曲校正
            use_textline_orientation: 是否啟用文字行方向偵測
            **kwargs: 其他引擎引數
        """
        self.mode = OCRMode(mode) if isinstance(mode, str) else mode
        self.device = device
        self.config = {
            "use_doc_orientation_classify": use_orientation_classify,
            "use_doc_unwarping": use_doc_unwarping,
            "use_textline_orientation": use_textline_orientation,
            "device": device,
            **kwargs,
        }

        self.engine: Optional[Any] = None
        self.structure_engine: Optional[Any] = None
        self.plugin_loader = plugin_loader
        self._is_initialized = False

    def init_engine(self) -> None:
        """
        初始化 OCR 引擎

        Raises:
            ImportError: 當所需模組不可用時
            Exception: 初始化失敗時
        """
        if self._is_initialized:
            logger.warning("Engine already initialized, skipping")
            return

        logger.info("Initializing PaddleOCR 3.x (Mode: %s)...", self.mode.value)

        try:
            if self.mode == OCRMode.STRUCTURE:
                self._init_structure_engine()

            elif self.mode == OCRMode.VL:
                self._init_vl_engine()

            elif self.mode == OCRMode.FORMULA:
                self._init_formula_engine()

            elif self.mode == OCRMode.HYBRID:
                self._init_hybrid_engine()

            else:  # BASIC
                self._init_basic_engine()

            self._is_initialized = True

        except Exception as e:
            logger.error("Initialization failed: %s", e)
            raise

    def _init_basic_engine(self) -> None:
        """初始化基本 OCR 引擎"""
        if PaddleOCR is None:
            raise ImportError("PaddleOCR 模組不可用，請執行 'pip install paddleocr'")

        self.engine = PaddleOCR(
            use_doc_orientation_classify=self.config.get(
                "use_doc_orientation_classify", True
            ),
            use_doc_unwarping=self.config.get("use_doc_unwarping", True),
            use_textline_orientation=self.config.get("use_textline_orientation", True),
        )
        logger.info("[OK] PP-OCRv5 initialized (Basic Mode)")

    def _init_structure_engine(self) -> None:
        """初始化結構化引擎"""
        if not HAS_STRUCTURE or PPStructureV3 is None:
            raise ImportError("PPStructureV3 模組不可用，請執行 'pip install paddleocr'")

        logger.info("  Loading PPStructure engine...")
        self.engine = PPStructureV3(show_log=True, layout=True, table=True, ocr=True)
        logger.info("[OK] PPStructure initialized (Structure Mode)")

    def _init_vl_engine(self) -> None:
        """初始化視覺語言模型引擎"""
        if not HAS_VL or PaddleOCRVL is None:
            raise ImportError("PaddleOCRVL 模組不可用，請執行 'pip install paddleocr'")

        self.engine = PaddleOCRVL(
            use_doc_orientation_classify=self.config.get(
                "use_doc_orientation_classify", True
            ),
            use_doc_unwarping=self.config.get("use_doc_unwarping", True),
        )
        logger.info("[OK] PaddleOCR-VL initialized (VL Mode)")

    def _init_formula_engine(self) -> None:
        """初始化公式識別引擎"""
        if not HAS_FORMULA or FormulaRecPipeline is None:
            raise ImportError("FormulaRecPipeline 模組不可用，請執行 'pip install paddleocr'")

        self.engine = FormulaRecPipeline(
            use_doc_orientation_classify=self.config.get(
                "use_doc_orientation_classify", True
            ),
            use_doc_unwarping=self.config.get("use_doc_unwarping", True),
            device=self.device,
        )
        logger.info("[OK] PP-FormulaNet initialized (Formula Mode)")

    def _init_hybrid_engine(self) -> None:
        """初始化混合模式引擎"""
        if not HAS_STRUCTURE:
            logger.warning("PPStructure unavailable, downgrading to Basic mode")
            self._init_basic_engine()
            return

        logger.info("  Loading PPStructure engine...")
        logger.info("  - Layout Analysis: Enabled")
        logger.info("  - Table Recognition: Enabled")
        logger.info("  - OCR Recognition: Enabled")

        try:
            if PPStructure is None:
                raise ImportError("PPStructure 模組不可用")

            self.structure_engine = PPStructure(
                show_log=True, layout=True, table=True, ocr=True
            )
            # 設定 engine 為 structure_engine 以便其他方法使用
            self.engine = self.structure_engine
            logger.info(
                "[OK] Hybrid Mode initialized (PPStructure Layout + Table + OCR)"
            )
        except Exception as e:
            logger.error("Hybrid mode initialization failed: %s", e)
            logger.warning("Downgrading to Basic mode")
            self._init_basic_engine()

    def predict(self, input_data, **kwargs):
        """
        執行 OCR 預測

        Args:
            input_data: 輸入資料（影象路徑或 numpy 陣列）
            **kwargs: 預測引數

        Returns:
            OCR 預測結果

        Raises:
            RuntimeError: 當引擎未初始化時
        """
        if not self._is_initialized or self.engine is None:
            raise RuntimeError("引擎未初始化，請先呼叫 init_engine()")

        # 1. 外掛前處理
        if self.plugin_loader:
            # 注意：這裡假設 input_data 是可以被外掛處理的格式（如 numpy array 或路徑）
            # 實際實作可能需要更複雜的型別檢查
            for plugin in self.plugin_loader.get_all_plugins().values():
                input_data = plugin.process_before_ocr(input_data)

        # 2. 執行預測
        if self.mode == OCRMode.BASIC and hasattr(self.engine, "ocr"):
            # Use standard ocr() method which returns list structure
            # PaddleOCR v3/PaddleX ocr() might not accept kwargs if it forwards to predict()
            results = self.engine.ocr(input_data)
        elif self.mode in [OCRMode.STRUCTURE, OCRMode.HYBRID] and hasattr(self.engine, "__call__"):
            # PPStructure 在新版本使用 __call__ 而非 predict
            results = self.engine(input_data, **kwargs)
        elif hasattr(self.engine, "predict"):
            # Fallback for older API that has predict()
            results = self.engine.predict(input_data, **kwargs)
        else:
            # 最後嘗試直接調用
            results = self.engine(input_data, **kwargs)

        # 3. 外掛後處理
        if self.plugin_loader:
            for plugin in self.plugin_loader.get_all_plugins().values():
                results = plugin.process_after_ocr(results)

        return results

    def is_initialized(self) -> bool:
        """
        檢查引擎是否已初始化

        Returns:
            bool: 是否已初始化
        """
        return self._is_initialized

    def get_mode(self) -> OCRMode:
        """
        獲取當前 OCR 模式

        Returns:
            OCRMode: 當前模式
        """
        return self.mode

    def get_engine(self):
        """
        獲取原始引擎例項

        Returns:
            OCR 引擎例項

        Raises:
            RuntimeError: 當引擎未初始化時
        """
        if not self._is_initialized or self.engine is None:
            raise RuntimeError("引擎未初始化")

        return self.engine

    def close(self) -> None:
        """關閉引擎，釋放資源"""
        if self.engine is not None:
            # PaddleOCR 引擎通常不需要顯式關閉
            # 但我們可以清理引用
            self.engine = None
            self.structure_engine = None
            self._is_initialized = False
            logging.info("OCR 引擎已關閉")

    def __enter__(self):
        """Context manager 支援"""
        self.init_engine()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 支援"""
        self.close()
        return False

    def __repr__(self) -> str:
        status = "initialized" if self._is_initialized else "not initialized"
        return f"OCREngineManager(mode={self.mode.value}, device={self.device}, status={status})"
