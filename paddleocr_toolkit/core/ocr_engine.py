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

if TYPE_CHECKING:
    from paddleocr_toolkit.plugins.loader import PluginLoader

try:
    from paddleocr import PaddleOCR, PPStructure
    # Export as PPStructureV3 for backward compatibility and tests
    PPStructureV3 = PPStructure
    HAS_STRUCTURE = True
except ImportError:
    HAS_STRUCTURE = False
    PPStructureV3 = None  # type: ignore

try:
    from paddleocr import PaddleOCRVL

    HAS_VL = True
except ImportError:
    HAS_VL = False

try:
    from paddleocr import FormulaRecPipeline

    HAS_FORMULA = True
except ImportError:
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
            logging.warning("引擎已初始化，跳過")
            return

        print(f"正在初始化 PaddleOCR 3.x (模式: {self.mode.value})...")

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
            print(f"初始化失敗: {e}")
            raise

    def _init_basic_engine(self) -> None:
        """初始化基本 OCR 引擎"""
        self.engine = PaddleOCR(
            use_doc_orientation_classify=self.config["use_doc_orientation_classify"],
            use_doc_unwarping=self.config["use_doc_unwarping"],
            use_textline_orientation=self.config["use_textline_orientation"],
        )
        print("[OK] PP-OCRv5 初始化完成（基本文字識別模式）")

    def _init_structure_engine(self) -> None:
        """初始化結構化引擎"""
        if not HAS_STRUCTURE:
            raise ImportError("PPStructure 模組不可用，請確認 paddleocr 版本")

        print("  載入 PPStructure 引擎...")
        self.engine = PPStructure(
            show_log=True,
            layout=True,
            table=True,
            ocr=True
        )
        print("[OK] PPStructure 初始化完成（結構化文件解析模式）")

    def _init_vl_engine(self) -> None:
        """初始化視覺語言模型引擎"""
        if not HAS_VL:
            raise ImportError("PaddleOCRVL 模組不可用，請確認 paddleocr 版本")

        self.engine = PaddleOCRVL(
            use_doc_orientation_classify=self.config["use_doc_orientation_classify"],
            use_doc_unwarping=self.config["use_doc_unwarping"],
        )
        print("[OK] PaddleOCR-VL 初始化完成（視覺語言模型模式）")

    def _init_formula_engine(self) -> None:
        """初始化公式識別引擎"""
        if not HAS_FORMULA:
            raise ImportError("FormulaRecPipeline 模組不可用，請確認 paddleocr 版本")

        self.engine = FormulaRecPipeline(
            use_doc_orientation_classify=self.config["use_doc_orientation_classify"],
            use_doc_unwarping=self.config["use_doc_unwarping"],
            device=self.device,
        )
        print("[OK] PP-FormulaNet 初始化完成（公式識別模式）")

    def _init_hybrid_engine(self) -> None:
        """初始化混合模式引擎"""
        if not HAS_STRUCTURE:
            print("[WARNING] PPStructure 不可用，降級為 Basic 模式")
            self._init_basic_engine()
            return

        print("  載入 PPStructure 引擎...")
        print("  - 版面分析：啟用")
        print("  - 表格識別：啟用")
        print("  - OCR 識別：啟用")
        
        try:
            self.structure_engine = PPStructure(
                show_log=True,
                layout=True,
                table=True,
                ocr=True
            )
            # 設定 engine 為 structure_engine 以便其他方法使用
            self.engine = self.structure_engine
            print("[OK] Hybrid 模式初始化完成（PPStructure 版面分析 + 表格識別 + OCR）")
        except Exception as e:
            print(f"[ERROR] Hybrid 模式初始化失敗: {e}")
            print("[WARNING] 降級為 Basic 模式")
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
        else:
            # Fallback for Structure/Layout analysis which rely on predict()
            results = self.engine.predict(input_data, **kwargs)

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
