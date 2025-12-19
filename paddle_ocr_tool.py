#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PaddleOCR 工具 - 多功能文件辨識與處理器

本工具使用 PaddleOCR 3.x 進行文字識別，支援多種 OCR 模式：
- basic: PP-OCRv5 基本文字識別
- structure: PP-StructureV3 結構化文件解析（保留排版）
- vl: PaddleOCR-VL 視覺語言模型（支援 109 種語言）

使用方法:
    # 基本 OCR（輸出文字）
    python paddle_ocr_tool.py input.pdf --text-output result.txt
    
    # 生成可搜尋 PDF
    python paddle_ocr_tool.py input.pdf --searchable
    
    # PP-StructureV3 模式（輸出 Markdown）
    python paddle_ocr_tool.py input.pdf --mode structure --markdown-output result.md
    
    # PaddleOCR-VL 模式（輸出 JSON）
    python paddle_ocr_tool.py input.pdf --mode vl --json-output result.json
    
    # 啟用文件方向校正
    python paddle_ocr_tool.py input.pdf --orientation-classify --text-output result.txt
    
    # 批次處理目錄
    python paddle_ocr_tool.py ./images/ --searchable
"""

import argparse
import gc
import logging
import os
import shutil
import sys
import tempfile
import traceback
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 停用模型來源檢查以加快啟動速度（已有本機模型時不需要連線檢查）
os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"

# ===== 設定 Poppler 路徑 =====
# 設定 Poppler 的二進位檔案路徑，確保 pdftoppm, pdfimages 等工具可被調用
poppler_bin = Path(__file__).parent / "Release-25.07.0-0" / "poppler-25.07.0" / "Library" / "bin"
if poppler_bin.exists():
    os.environ["PATH"] = str(poppler_bin) + os.pathsep + os.environ["PATH"]
    logging.debug(f"已將 Poppler 路徑加入 PATH: {poppler_bin}")

# ===== 從 paddleocr_toolkit 套件匯入模組 =====
try:
    from paddleocr_toolkit.core import (
        OCRMode,
        OCRResult,
        PDFGenerator,
        get_dpi_matrix,
        page_to_numpy,
        pixmap_to_numpy,
    )
    from paddleocr_toolkit.processors import (
        OCRWorkaround,
        PageStats,
        ProcessingStats,
        StatsCollector,
        TextBlock,
        detect_pdf_quality,
        detect_scanned_document,
        fix_english_spacing,
    )

    # Stage 3 新模組（選擇性匯入，確保向後相容）
    try:
        from paddleocr_toolkit.core import OCREngineManager, OCRResultParser
        from paddleocr_toolkit.outputs import OutputManager
        from paddleocr_toolkit.processors import PDFProcessor

        HAS_STAGE3_MODULES = True
    except ImportError:
        HAS_STAGE3_MODULES = False
        logging.warning("Stage 3 模組未安裝，使用傳統實作")

    HAS_TOOLKIT = True
except ImportError:
    HAS_TOOLKIT = False
    print("錯誤：無法匯入 paddleocr_toolkit，請確認套件完整性")
    sys.exit(1)


# 設定日誌
def setup_logging(log_file: Optional[str] = None):
    """設定日誌記錄"""
    if log_file is None:
        log_file = (
            Path(__file__).parent
            / f"paddle_ocr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )

    # 移除現有的所有 handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # 創建檔案 handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="w")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )

    # 創建控制台 handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )

    # 設定 root logger
    logging.root.setLevel(logging.INFO)
    logging.root.addHandler(file_handler)
    logging.root.addHandler(console_handler)

    # 立即寫入第一條記錄
    logging.info(f"=" * 60)
    logging.info(f"日誌檔案：{log_file}")
    logging.info(f"=" * 60)

    # 強制 flush
    for handler in logging.root.handlers:
        handler.flush()

    return log_file


# 檢查依賴項
try:
    from paddleocr import PaddleOCR

    # 嘗試導入進階模組（可選）
    try:
        from paddleocr import PPStructureV3

        HAS_STRUCTURE = True
    except ImportError:
        HAS_STRUCTURE = False
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
except ImportError:
    print("錯誤：請安裝 paddleocr: pip install paddleocr")
    sys.exit(1)

try:
    import fitz  # PyMuPDF
except ImportError:
    print("錯誤：請安裝 pymupdf: pip install pymupdf")
    sys.exit(1)

try:
    import numpy as np
    from PIL import Image
except ImportError:
    print("錯誤：請安裝 Pillow 和 numpy: pip install Pillow numpy")
    sys.exit(1)

# 可選依賴：進度條
try:
    from tqdm import tqdm

    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# 可選依賴：Excel 輸出
try:
    import openpyxl

    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

# 可選依賴：英文分詞（修復 OCR 空格問題）
try:
    import wordninja

    HAS_WORDNINJA = True
except ImportError:
    HAS_WORDNINJA = False

# 可選依賴：翻譯模組
try:
    from pdf_translator import (
        BilingualPDFGenerator,
        MonolingualPDFGenerator,
        OllamaTranslator,
        TextInpainter,
        TextRenderer,
        TranslatedBlock,
    )

    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False
    logging.warning("翻譯模組 (pdf_translator) 未安裝，翻譯功能不可用")


# OCR 模式枚舉


# 支援的檔案格式
SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
SUPPORTED_PDF_FORMAT = ".pdf"

# 圖片大小限制 (避免 OCR 記憶體不足)
MAX_IMAGE_SIDE = 2500  # 像素


def resize_image_if_needed(file_path: str, max_side: int = MAX_IMAGE_SIDE) -> Tuple[str, bool]:
    """
    檢測並縮小大圖片以避免 OCR 記憶體問題
    
    Args:
        file_path: 圖片路徑
        max_side: 最大邊長（預設 2500px）
    
    Returns:
        Tuple[str, bool]: (處理後的圖片路徑, 是否有縮小)
    """
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            max_dim = max(width, height)
            
            if max_dim <= max_side:
                return file_path, False
            
            # 計算縮放比例
            scale = max_side / max_dim
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            print(f"圖片太大 ({width}x{height})，自動縮小為 {new_width}x{new_height}")
            logging.info(f"圖片太大 ({width}x{height})，自動縮小為 {new_width}x{new_height}")
            
            # 縮小圖片
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 儲存到新檔案
            path = Path(file_path)
            new_path = path.parent / f"{path.stem}_resized{path.suffix}"
            resized_img.save(str(new_path), quality=95)
            
            return str(new_path), True
            
    except Exception as e:
        logging.warning(f"縮小圖片時發生錯誤: {e}，使用原始圖片")
        return file_path, False


class PaddleOCRTool:
    """
    PaddleOCR 工具主類別

    提供 OCR 文字辨識和可搜尋 PDF 生成功能。
    支援多種 OCR 模式：
    - basic: PP-OCRv5 基本文字識別
    - structure: PP-StructureV3 結構化文件解析
    - vl: PaddleOCR-VL 視覺語言模型

    相容 PaddleOCR 3.x 新版 API。
    """

    def __init__(
        self,
        mode: str = "basic",
        use_orientation_classify: bool = False,
        use_doc_unwarping: bool = False,
        use_textline_orientation: bool = False,
        device: str = "gpu",
        debug_mode: bool = False,
        compress_images: bool = False,
        jpeg_quality: int = 85,
    ):
        """
        初始化 PaddleOCR 工具

        Args:
            mode: OCR 模式 ('basic', 'structure', 'vl')
            use_orientation_classify: 是否啟用文件方向自動校正
            use_doc_unwarping: 是否啟用文件彎曲校正
            use_textline_orientation: 是否啟用文字行方向偵測
            device: 運算設備 ('gpu' 或 'cpu')
            debug_mode: DEBUG 模式，將隱形文字改為粉紅色可見文字
            compress_images: 啟用 JPEG 壓縮以減少 PDF 檔案大小
            jpeg_quality: JPEG 壓縮品質（0-100）
        """
        self.debug_mode = debug_mode
        self.mode = mode
        self.use_orientation_classify = use_orientation_classify
        self.use_doc_unwarping = use_doc_unwarping
        self.device = device
        self.compress_images = compress_images
        self.jpeg_quality = jpeg_quality

        # === Stage 3 模組化初始化（新） ===
        if HAS_STAGE3_MODULES:
            try:
                # 初始化 OCR 引擎管理器
                self.engine_manager = OCREngineManager(
                    mode=mode,
                    device=device,
                    use_orientation_classify=use_orientation_classify,
                    use_doc_unwarping=use_doc_unwarping,
                    use_textline_orientation=use_textline_orientation,
                )
                self.engine_manager.init_engine()

                # 初始化結果解析器
                self.result_parser = OCRResultParser()

                # 初始化 PDF 處理器
                self.pdf_processor = PDFProcessor(
                    ocr_func=self.engine_manager.predict,
                    result_parser=self.result_parser.parse_basic_result,
                    debug_mode=debug_mode,
                )

                # 為了向後兼容，設置 self.ocr
                self.ocr = self.engine_manager.get_engine()

                # 標記使用新架構
                self._using_stage3 = True
                logging.info("[Stage 3] 使用模組化架構初始化")

            except Exception as e:
                logging.warning(f"[Stage 3] 模組化初始化失敗: {e}，回退到傳統實作")
                self._using_stage3 = False
                self._legacy_init(
                    mode,
                    use_orientation_classify,
                    use_doc_unwarping,
                    use_textline_orientation,
                    device,
                )
        else:
            # 使用傳統初始化
            self._using_stage3 = False
            self._legacy_init(
                mode,
                use_orientation_classify,
                use_doc_unwarping,
                use_textline_orientation,
                device,
            )

    def _legacy_init(
        self,
        mode: str,
        use_orientation_classify: bool,
        use_doc_unwarping: bool,
        use_textline_orientation: bool,
        device: str,
    ):
        """傳統初始化方法（向後相容）"""
        # 初始化對應的 OCR 引擎
        print(f"正在初始化 PaddleOCR 3.x (模式: {mode})...")
        if self.debug_mode:
            print("[DEBUG] 已啟用 DEBUG 模式：可搜尋 PDF 的隱形文字將顯示為粉紅色")

        try:
            if mode == "structure":
                if not HAS_STRUCTURE:
                    raise ImportError("PPStructureV3 模組不可用，請確認 paddleocr 版本")
                self.ocr = PPStructureV3(
                    use_doc_orientation_classify=use_orientation_classify,
                    use_doc_unwarping=use_doc_unwarping,
                    use_textline_orientation=use_textline_orientation,
                    device=device,
                )
                print("[OK] PP-StructureV3 初始化完成（結構化文件解析模式）")

            elif mode == "vl":
                if not HAS_VL:
                    raise ImportError("PaddleOCRVL 模組不可用，請確認 paddleocr 版本")
                self.ocr = PaddleOCRVL(
                    use_doc_orientation_classify=use_orientation_classify,
                    use_doc_unwarping=use_doc_unwarping,
                )
                print("[OK] PaddleOCR-VL 初始化完成（視覺語言模型模式）")

            elif mode == "formula":
                if not HAS_FORMULA:
                    raise ImportError("FormulaRecPipeline 模組不可用，請確認 paddleocr 版本")
                self.ocr = FormulaRecPipeline(
                    use_doc_orientation_classify=use_orientation_classify,
                    use_doc_unwarping=use_doc_unwarping,
                    device=device,
                )
                print("[OK] PP-FormulaNet 初始化完成（公式識別模式）")

            elif mode == "hybrid":
                # 混合模式：只使用 PP-StructureV3（內含 OCR）
                if not HAS_STRUCTURE:
                    raise ImportError("PPStructureV3 模組不可用，請確認 paddleocr 版本")

                print("  載入 PP-StructureV3 引擎...")
                self.structure_engine = PPStructureV3(
                    use_doc_orientation_classify=use_orientation_classify,
                    use_doc_unwarping=use_doc_unwarping,
                    use_textline_orientation=use_textline_orientation,
                    device=device,
                )

                # 設定 self.ocr 為 structure_engine 以便其他方法使用
                self.ocr = self.structure_engine
                print("[OK] Hybrid 模式初始化完成（PP-StructureV3 版面分析 + OCR）")

            else:  # basic 模式
                self.ocr = PaddleOCR(
                    use_doc_orientation_classify=use_orientation_classify,
                    use_doc_unwarping=use_doc_unwarping,
                    use_textline_orientation=use_textline_orientation,
                )
                print("[OK] PP-OCRv5 初始化完成（基本文字識別模式）")

        except Exception as e:
            print(f"初始化失敗: {e}")
            raise

    def _parse_predict_result(self, predict_result) -> List[OCRResult]:
        """
        解析 PaddleOCR 3.x predict() 方法的回傳結果

        Args:
            predict_result: predict() 方法回傳的結果物件

        Returns:
            List[OCRResult]: OCR 辨識結果列表
        """
        # 優先使用 Stage 3 結果解析器
        if self._using_stage3 and hasattr(self, "result_parser"):
            return self.result_parser.parse_basic_result(predict_result)

        # 傳統實作（向後相容）
        results = []

        try:
            # PaddleOCR 3.x 回傳結果是一個列表，每個元素代表一個輸入
            for res in predict_result:
                # 取得 OCR 結果
                # 新版 API 的結果結構：res['rec_texts'], res['rec_scores'], res['dt_polys']
                if hasattr(res, "rec_texts"):
                    texts = res.rec_texts if hasattr(res, "rec_texts") else []
                    scores = res.rec_scores if hasattr(res, "rec_scores") else []
                    polys = res.dt_polys if hasattr(res, "dt_polys") else []

                    for i, (text, score, poly) in enumerate(zip(texts, scores, polys)):
                        # 將 polygon 轉換為 bbox 格式
                        bbox = poly.tolist() if hasattr(poly, "tolist") else list(poly)
                        results.append(
                            OCRResult(
                                text=str(text), confidence=float(score), bbox=bbox
                            )
                        )
                elif hasattr(res, "__getitem__"):
                    # 嘗試透過字典方式存取
                    texts = res.get("rec_texts", []) if isinstance(res, dict) else []
                    scores = res.get("rec_scores", []) if isinstance(res, dict) else []
                    polys = res.get("dt_polys", []) if isinstance(res, dict) else []

                    for text, score, poly in zip(texts, scores, polys):
                        bbox = poly.tolist() if hasattr(poly, "tolist") else list(poly)
                        results.append(
                            OCRResult(
                                text=str(text), confidence=float(score), bbox=bbox
                            )
                        )
        except Exception as e:
            print(f"解析結果時發生錯誤: {e}")

        return results

    def process_image(self, image_path: str) -> List[OCRResult]:
        """
        處理單張圖片進行 OCR

        Args:
            image_path: 圖片檔案路徑

        Returns:
            List[OCRResult]: OCR 辨識結果列表
        """
        results = []
        resized_path = None  # 追蹤是否有產生縮小的圖片

        try:
            # 0. 自動縮小大圖片
            processed_path, was_resized = resize_image_if_needed(image_path)
            if was_resized:
                resized_path = processed_path  # 記住以便稍後清理

            # === Stage 3: 使用引擎管理器和解析器 ===
            if self._using_stage3 and hasattr(self, "engine_manager"):
                predict_result = self.engine_manager.predict(input=processed_path)
                results = self.result_parser.parse_basic_result(predict_result)
            else:
                # === 傳統實作 ===
                # PaddleOCR 3.x 使用 predict() 方法
                predict_result = self.ocr.predict(input=processed_path)
                results = self._parse_predict_result(predict_result)

            if not results:
                print(f"警告：未在圖片中偵測到文字: {image_path}")

            return results

        except Exception as e:
            print(f"錯誤：處理圖片失敗 ({image_path}): {e}")
            return results

    def process_image_array(self, image_array: np.ndarray) -> List[OCRResult]:
        """
        處理 numpy 陣列圖片進行 OCR

        Args:
            image_array: numpy 陣列格式的圖片

        Returns:
            List[OCRResult]: OCR 辨識結果列表
        """
        results = []
        tmp_path = None

        try:
            # 將 numpy 陣列轉為臨時圖片檔案，因為 PaddleOCR 3.x predict() 接受路徑
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                tmp_path = tmp_file.name
                Image.fromarray(image_array).save(tmp_path)

            try:
                predict_result = self.ocr.predict(input=tmp_path)
                results = self._parse_predict_result(predict_result)
            finally:
                # 清理臨時檔案
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except:
                        pass

            # 強制清理記憶體
            del image_array
            gc.collect()

            return results

        except Exception as e:
            logging.error(f"處理圖片陣列失敗: {e}")
            logging.error(traceback.format_exc())
            print(f"錯誤：處理圖片陣列失敗: {e}")
            # 確保臨時檔案被清理
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except:
                    pass
            return results

    # ========== Structured 處理輔助方法 ==========

    def _setup_structured_output_paths(
        self,
        markdown_output: Optional[str],
        json_output: Optional[str],
        script_dir: Path,
    ) -> Tuple[Optional[Path], Optional[Path]]:
        """設定 structured 模式的輸出路徑"""
        md_path, json_path = None, None

        if markdown_output:
            md_path = Path(markdown_output)
            if not md_path.is_absolute():
                md_path = script_dir / md_path
            md_path.parent.mkdir(parents=True, exist_ok=True)

        if json_output:
            json_path = Path(json_output)
            if not json_path.is_absolute():
                json_path = script_dir / json_path
            json_path.parent.mkdir(parents=True, exist_ok=True)

        return md_path, json_path

    def _process_with_tempdir(
        self, res, save_method_name: str, glob_pattern: str, process_func
    ) -> None:
        """使用臨時目錄處理輸出的通用方法"""
        temp_dir = tempfile.mkdtemp()
        try:
            save_method = getattr(res, save_method_name, None)
            if save_method:
                save_method(save_path=temp_dir)
                for file in Path(temp_dir).glob(glob_pattern):
                    process_func(file)
        except Exception as e:
            logging.warning(f"{save_method_name} 失敗: {e}")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _save_structured_page_outputs(
        self,
        res,
        page_count: int,
        markdown_output: Optional[str],
        json_output: Optional[str],
        excel_output: Optional[str],
        html_output: Optional[str],
        md_path: Optional[Path],
        json_path: Optional[Path],
        input_path: str,
        script_dir: Path,
        all_markdown_content: List[str],
        result_summary: Dict[str, Any],
    ) -> None:
        """儲存單頁的各種輸出"""
        # Markdown
        if markdown_output:
            self._process_with_tempdir(
                res,
                "save_to_markdown",
                "*.md",
                lambda f: all_markdown_content.append(
                    f"<!-- Page {page_count} -->\n"
                    + open(f, "r", encoding="utf-8").read()
                ),
            )

        # JSON
        if json_output and json_path:

            def save_json(file):
                target = json_path.parent / f"{json_path.stem}_page{page_count}.json"
                shutil.copy(file, target)
                result_summary["json_files"].append(str(target))

            self._process_with_tempdir(res, "save_to_json", "*.json", save_json)

        # Excel
        if excel_output:
            if not HAS_OPENPYXL:
                if page_count == 1:
                    print("警告：需要安裝 openpyxl: pip install openpyxl")
            else:
                excel_path = Path(excel_output)

                def save_excel(file):
                    target = (
                        excel_path.parent / f"{excel_path.stem}_page{page_count}.xlsx"
                        if excel_path.suffix == ".xlsx"
                        else Path(excel_output)
                        / f"{Path(input_path).stem}_page{page_count}.xlsx"
                    )
                    shutil.copy(file, target)
                    result_summary["excel_files"].append(str(target))

                self._process_with_tempdir(res, "save_to_xlsx", "*.xlsx", save_excel)

        # HTML
        if html_output:
            html_path = (
                Path(html_output)
                if Path(html_output).is_absolute()
                else script_dir / html_output
            )

            def save_html(file):
                target = (
                    html_path.parent / f"{html_path.stem}_page{page_count}.html"
                    if html_path.suffix == ".html"
                    else (html_path.mkdir(parents=True, exist_ok=True) or html_path)
                    / f"{Path(input_path).stem}_page{page_count}.html"
                )
                shutil.copy(file, target)
                result_summary["html_files"].append(str(target))

            self._process_with_tempdir(res, "save_to_html", "*.html", save_html)

    def _save_structured_markdown(
        self,
        all_markdown_content: List[str],
        md_path: Path,
        result_summary: Dict[str, Any],
    ) -> None:
        """儲存合併後的 Markdown 檔案"""
        if all_markdown_content:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write("\n\n---\n\n".join(all_markdown_content))
            result_summary["markdown_files"].append(str(md_path))
            print(f"[OK] Markdown 已儲存：{md_path}")

    def process_structured(
        self,
        input_path: str,
        markdown_output: Optional[str] = None,
        json_output: Optional[str] = None,
        excel_output: Optional[str] = None,
        html_output: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        使用 PP-StructureV3 或 PaddleOCR-VL 處理文件

        適用於 structure 和 vl 模式，直接輸出 Markdown/JSON/Excel/HTML 格式

        Args:
            input_path: 輸入檔案路徑（PDF 或圖片）
            markdown_output: Markdown 輸出目錄（可選）
            json_output: JSON 輸出目錄（可選）
            excel_output: Excel 輸出路徑（可選，僅表格）
            html_output: HTML 輸出路徑（可選）

        Returns:
            Dict[str, Any]: 處理結果摘要
        """
        if self.mode not in ["structure", "vl"]:
            raise ValueError(
                f"process_structured 僅適用於 structure 或 vl 模式，當前模式: {self.mode}"
            )

        result_summary = {
            "input": input_path,
            "mode": self.mode,
            "pages_processed": 0,
            "markdown_files": [],
            "json_files": [],
            "excel_files": [],
            "html_files": [],
        }

        try:
            print(f"正在處理: {input_path}")

            # 使用 predict() 方法處理
            output = self.ocr.predict(input=input_path)

            # 获取脚本所在目录作为默认输出目录
            script_dir = Path(__file__).parent.resolve()

            # 设定输出路径
            md_path, json_path = self._setup_structured_output_paths(
                markdown_output, json_output, script_dir
            )

            # 处理每个结果
            page_count = 0
            all_markdown_content = []

            for res in output:
                page_count += 1

                # 保存单页的各种输出
                self._save_structured_page_outputs(
                    res,
                    page_count,
                    markdown_output,
                    json_output,
                    excel_output,
                    html_output,
                    md_path,
                    json_path,
                    input_path,
                    script_dir,
                    all_markdown_content,
                    result_summary,
                )

            # 儲存合併的 Markdown
            if markdown_output and md_path:
                self._save_structured_markdown(
                    all_markdown_content, md_path, result_summary
                )

            # 完成訊息
            if result_summary.get("excel_files"):
                print(f"[OK] Excel 已儲存：{len(result_summary['excel_files'])} 個檔案")

            if result_summary.get("html_files"):
                print(f"[OK] HTML 已儲存：{len(result_summary['html_files'])} 個檔案")

            result_summary["pages_processed"] = page_count
            print(f"[OK] 處理完成：{page_count} 頁")

            return result_summary

        except Exception as e:
            print(f"錯誤：處理失敗 ({input_path}): {e}")
            result_summary["error"] = str(e)
            return result_summary

    # ========== PDF 处理辅助方法 ==========

    def _setup_pdf_generator(
        self, pdf_path: str, output_path: Optional[str], searchable: bool
    ) -> Tuple[Optional[str], Optional["PDFGenerator"]]:
        """設定 PDF 生成器"""
        if not searchable:
            return None, None
        if not output_path:
            base_name = Path(pdf_path).stem
            output_path = str(Path(pdf_path).parent / f"{base_name}_searchable.pdf")
        logging.info(f"準備生成可搜尋 PDF: {output_path}")
        return output_path, PDFGenerator(output_path, debug_mode=self.debug_mode)

    def _process_single_pdf_page(
        self,
        page,
        page_num: int,
        total_pages: int,
        dpi: int,
        pdf_generator: Optional["PDFGenerator"],
        show_progress: bool,
    ) -> List[OCRResult]:
        """處理單個 PDF 頁面"""
        logging.info(f"開始處理第 {page_num + 1}/{total_pages} 頁")
        if not (show_progress and HAS_TQDM):
            print(f"  處理第 {page_num + 1}/{total_pages} 頁...")

        # 轉換為圖片並執行 OCR
        zoom = dpi / 72.0
        pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        img_array = pixmap_to_numpy(pixmap)
        page_results = self.process_image_array(img_array)

        # 縮放座標
        scale_factor = 72.0 / dpi
        for result in page_results:
            result.bbox = [
                [p[0] * scale_factor, p[1] * scale_factor] for p in result.bbox
            ]

        # 新增到可搜尋 PDF
        if pdf_generator:
            original_pixmap = page.get_pixmap()
            pdf_generator.add_page_from_pixmap(original_pixmap, page_results)
            del original_pixmap

        # 清理
        del pixmap, img_array
        gc.collect()
        return page_results

    def process_pdf(
        self,
        pdf_path: str,
        output_path: Optional[str] = None,
        searchable: bool = False,
        dpi: int = 200,
        show_progress: bool = True,
    ) -> Tuple[List[List[OCRResult]], Optional[str]]:
        """
        處理 PDF 檔案進行 OCR

        Args:
            pdf_path: PDF 檔案路徑
            output_path: 輸出檔案路徑（可選）
            searchable: 是否生成可搜尋 PDF
            dpi: PDF 轉圖片的解析度

        Returns:
            Tuple[List[List[OCRResult]], Optional[str]]:
                (每頁的 OCR 結果列表, 輸出檔案路徑)
        """
        # === Stage 3: 使用 PDFProcessor ===
        if self._using_stage3 and hasattr(self, "pdf_processor"):
            return self.pdf_processor.process_pdf(
                pdf_path=pdf_path,
                output_path=output_path,
                searchable=searchable,
                dpi=dpi,
                show_progress=show_progress,
            )

        # === 傳統實作（向後相容） ===
        all_results = []

        try:
            # 打開 PDF
            logging.info(f"打開 PDF: {pdf_path}")
            pdf_doc = fitz.open(pdf_path)
            total_pages = len(pdf_doc)
            print(f"正在處理 PDF: {pdf_path} ({total_pages} 頁)")

            # 設定 PDF 生成器
            output_path, pdf_generator = self._setup_pdf_generator(
                pdf_path, output_path, searchable
            )

            # 處理每一頁
            page_iterator = range(total_pages)
            if show_progress and HAS_TQDM:
                page_iterator = tqdm(page_iterator, desc="OCR 處理中", unit="頁", ncols=80)

            for page_num in page_iterator:
                try:
                    page = pdf_doc[page_num]
                    page_results = self._process_single_pdf_page(
                        page, page_num, total_pages, dpi, pdf_generator, show_progress
                    )
                    all_results.append(page_results)
                except Exception as page_error:
                    logging.error(f"處理第 {page_num + 1} 頁錯誤: {page_error}")
                    print(f"  [WARN] 處理第 {page_num + 1} 頁錯誤: {page_error}")
                    all_results.append([])
                    gc.collect()

            pdf_doc.close()

            # 儲存可搜尋 PDF
            if pdf_generator:
                pdf_generator.save()

            logging.info(f"[OK] 完成處理 {total_pages} 頁")
            return all_results, output_path

        except Exception as e:
            logging.error(f"處理 PDF 失敗 ({pdf_path}): {e}")
            print(f"錯誤：處理 PDF 失敗: {e}")
            return all_results, None

    def process_directory(
        self,
        dir_path: str,
        output_path: Optional[str] = None,
        searchable: bool = False,
        recursive: bool = False,
    ) -> Dict[str, List[OCRResult]]:
        """
        批次處理目錄中的所有圖片和 PDF

        Args:
            dir_path: 目錄路徑
            output_path: 輸出路徑（可選）
            searchable: 是否生成可搜尋 PDF
            recursive: 是否遞迴處理子目錄

        Returns:
            Dict[str, List[OCRResult]]: 檔案路徑到 OCR 結果的對應
        """
        all_results = {}
        dir_path = Path(dir_path)

        # 收集所有支援的檔案
        files = []
        pattern = "**/*" if recursive else "*"

        for ext in SUPPORTED_IMAGE_FORMATS:
            files.extend(dir_path.glob(f"{pattern}{ext}"))
        files.extend(dir_path.glob(f"{pattern}{SUPPORTED_PDF_FORMAT}"))

        if not files:
            print(f"警告：在目錄中未找到支援的檔案: {dir_path}")
            return all_results

        print(f"找到 {len(files)} 個檔案待處理")

        # 如果需要合併為可搜尋 PDF
        if searchable:
            if not output_path:
                output_path = str(dir_path / f"{dir_path.name}_searchable.pdf")
            pdf_generator = PDFGenerator(output_path, debug_mode=self.debug_mode)

            for file_path in sorted(files):
                file_str = str(file_path)
                ext = file_path.suffix.lower()

                if ext == SUPPORTED_PDF_FORMAT:
                    # 處理 PDF（展開為多頁）
                    results, _ = self.process_pdf(file_str, searchable=False)
                    all_results[file_str] = []
                    for page_results in results:
                        all_results[file_str].extend(page_results)
                else:
                    # 處理圖片
                    results = self.process_image(file_str)
                    all_results[file_str] = results
                    if results:
                        pdf_generator.add_page(file_str, results)

            pdf_generator.save()
        else:
            # 僅執行 OCR，不生成 PDF
            for file_path in sorted(files):
                file_str = str(file_path)
                ext = file_path.suffix.lower()

                if ext == SUPPORTED_PDF_FORMAT:
                    results, _ = self.process_pdf(file_str, searchable=False)
                    all_results[file_str] = []
                    for page_results in results:
                        all_results[file_str].extend(page_results)
                else:
                    results = self.process_image(file_str)
                    all_results[file_str] = results

        return all_results

    def get_text(self, results: List[OCRResult], separator: str = "\n") -> str:
        """
        從 OCR 結果中提取純文字

        Args:
            results: OCR 結果列表
            separator: 行分隔符

        Returns:
            str: 合併的純文字
        """
        # === Stage 3: 使用 PDFProcessor ===
        if self._using_stage3 and hasattr(self, "pdf_processor"):
            return self.pdf_processor.get_text(results, separator)

        # === 傳統實作 ===
        return separator.join(r.text for r in results if r.text.strip())

    def process_formula(
        self, input_path: str, latex_output: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用 PP-FormulaNet 處理數學公式識別

        Args:
            input_path: 輸入檔案路徑（圖片或 PDF）
            latex_output: LaTeX 輸出檔案路徑（可選）

        Returns:
            Dict[str, Any]: 處理結果摘要，包含識別的公式
        """
        if self.mode != "formula":
            raise ValueError(f"process_formula 僅適用於 formula 模式，當前模式: {self.mode}")

        result_summary = {
            "input": input_path,
            "formulas": [],
            "latex_file": None,
            "error": None,
        }

        try:
            print(f"正在識別公式: {input_path}")
            logging.info(f"開始公式識別: {input_path}")

            # 執行公式識別
            output = self.ocr.predict(input=input_path)

            all_latex = []
            for res in output:
                # 嘗試多種方式提取 LaTeX
                latex = None

                # 方式 1：直接屬性
                if hasattr(res, "rec_formula"):
                    latex = res.rec_formula
                # 方式 2：字典存取
                elif isinstance(res, dict):
                    latex = (
                        res.get("rec_formula") or res.get("formula") or res.get("latex")
                    )
                # 方式 3：結果物件的其他屬性
                elif hasattr(res, "__dict__"):
                    for key in ["rec_formula", "formula", "latex", "result"]:
                        if hasattr(res, key):
                            latex = getattr(res, key)
                            if latex:
                                break

                if latex:
                    all_latex.append(str(latex))
                    logging.info(f"識別到公式: {latex[:50]}...")

            result_summary["formulas"] = all_latex
            print(f"[OK] 識別到 {len(all_latex)} 個公式")

            # 儲存 LaTeX 檔案
            if latex_output and all_latex:
                with open(latex_output, "w", encoding="utf-8") as f:
                    f.write("% 公式識別結果\n")
                    f.write("% 由 PaddleOCR 工具生成\n")
                    f.write(f"% 來源文件: {input_path}\n\n")

                    for i, latex in enumerate(all_latex, 1):
                        f.write(f"% 公式 {i}\n")
                        f.write(f"$$ {latex} $$\n\n")

                result_summary["latex_file"] = latex_output
                print(f"[OK] LaTeX 已儲存：{latex_output}")
                logging.info(f"LaTeX 已儲存：{latex_output}")

            return result_summary

        except Exception as e:
            error_msg = f"公式識別失敗: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            print(f"錯誤：{error_msg}")
            result_summary["error"] = str(e)
            return result_summary

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
        混合模式：使用 PP-StructureV3 版面分析 + PP-OCRv5 精確座標

        生成閱讀順序正確的可搜尋 PDF 和 Markdown/JSON/HTML

        Args:
            input_path: 輸入檔案路徑（PDF 或圖片）
            output_path: 可搜尋 PDF 輸出路徑（可選）
            markdown_output: Markdown 輸出路徑（可選）
            json_output: JSON 輸出路徑（可選）
            excel_output: Excel 輸出路徑（可選，僅表格）
            html_output: HTML 輸出路徑（可選）

        Returns:
            Dict[str, Any]: 處理結果摘要
        """
        if self.mode != "hybrid":
            raise ValueError(f"process_hybrid 僅適用於 hybrid 模式，當前模式: {self.mode}")

        result_summary = {
            "input": input_path,
            "mode": "hybrid",
            "pages_processed": 0,
            "searchable_pdf": None,
            "markdown_file": None,
            "text_content": [],
            "error": None,
        }

        input_path_obj = Path(input_path)

        try:
            # 設定輸出路徑
            if not output_path:
                output_path = str(
                    input_path_obj.parent / f"{input_path_obj.stem}_hybrid.pdf"
                )

            if not markdown_output:
                markdown_output = str(
                    input_path_obj.parent / f"{input_path_obj.stem}_hybrid.md"
                )

            print(f"正在處理（混合模式）: {input_path}")
            logging.info(f"開始混合模式處理: {input_path}")

            # 判斷輸入類型
            if input_path_obj.suffix.lower() == ".pdf":
                # 自動偵測 PDF 品質並調整 DPI
                quality = detect_pdf_quality(input_path)
                print(f"[偵測] {quality['reason']}")
                if quality["is_scanned"] or quality["is_blurry"]:
                    if quality["recommended_dpi"] > dpi:
                        dpi = quality["recommended_dpi"]
                print(f"   使用 DPI: {dpi}")

                return self._process_hybrid_pdf(
                    input_path,
                    output_path,
                    markdown_output,
                    json_output,
                    html_output,
                    dpi,
                    show_progress,
                    result_summary,
                    translate_config=translate_config,
                )
            else:
                return self._process_hybrid_image(
                    input_path, output_path, markdown_output, result_summary
                )

        except Exception as e:
            error_msg = f"混合模式處理失敗: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            print(f"錯誤：{error_msg}")
            result_summary["error"] = str(e)
            return result_summary

    # ========== Hybrid PDF 處理輔助方法 ==========

    def _setup_hybrid_generators(
        self, output_path: str
    ) -> Tuple[PDFGenerator, PDFGenerator, Optional["TextInpainter"], str]:
        """設定混合模式所需的生成器

        Args:
            output_path: 輸出 PDF 路徑

        Returns:
            Tuple of (pdf_generator, erased_generator, inpainter, erased_output_path)
        """
        erased_output_path = output_path.replace("_hybrid.pdf", "_erased.pdf")

        # 原文可搜尋 PDF
        pdf_generator = PDFGenerator(
            output_path,
            debug_mode=self.debug_mode,
            compress_images=self.compress_images,
            jpeg_quality=self.jpeg_quality,
        )

        # 擦除版 PDF
        erased_generator = PDFGenerator(
            erased_output_path,
            debug_mode=self.debug_mode,
            compress_images=self.compress_images,
            jpeg_quality=self.jpeg_quality,
        )

        # 擦除器
        inpainter = TextInpainter() if HAS_TRANSLATOR else None

        logging.info(
            f"[DEBUG] PDFGenerator compress_images={pdf_generator.compress_images}, jpeg_quality={pdf_generator.jpeg_quality}"
        )

        return pdf_generator, erased_generator, inpainter, erased_output_path

    def _extract_markdown_from_structure_output(
        self, structure_output, page_num: int
    ) -> str:
        """從 PP-StructureV3 輸出提取 Markdown

        Args:
            structure_output: Structure 引擎輸出
            page_num: 頁碼（0-based）

        Returns:
            str: 頁面的 Markdown 文字
        """
        page_markdown = f"## 第 {page_num + 1} 頁\n\n"

        for res in structure_output:
            temp_md_dir = tempfile.mkdtemp()
            try:
                if hasattr(res, "save_to_markdown"):
                    res.save_to_markdown(save_path=temp_md_dir)
                    # 讀取生成的 Markdown
                    for md_file in Path(temp_md_dir).glob("*.md"):
                        with open(md_file, "r", encoding="utf-8") as f:
                            page_markdown += f.read()
                        break
            except Exception as md_err:
                logging.warning(f"save_to_markdown 失敗: {md_err}")
                # 回退：使用 markdown 屬性
                if hasattr(res, "markdown") and isinstance(res.markdown, str):
                    page_markdown += res.markdown
            finally:
                shutil.rmtree(temp_md_dir, ignore_errors=True)

        return page_markdown

    def _generate_dual_pdfs(
        self,
        pixmap,
        img_array: np.ndarray,
        sorted_results: List[OCRResult],
        pdf_generator: PDFGenerator,
        erased_generator: PDFGenerator,
        inpainter: Optional["TextInpainter"],
    ) -> None:
        """生成原文 PDF 和擦除版 PDF

        Args:
            pixmap: PyMuPDF pixmap 物件
            img_array: 圖片陣列
            sorted_results: OCR 結果列表
            pdf_generator: 原文 PDF 生成器
            erased_generator: 擦除版 PDF 生成器
            inpainter: 文字擦除器
        """
        img_array_copy = img_array.copy()

        # 1. 原文可搜尋 PDF
        pdf_generator.add_page_from_pixmap(pixmap, sorted_results)

        # 2. 擦除版 PDF
        if inpainter:
            # 收集 bboxes
            bboxes = [
                result.bbox
                for result in sorted_results
                if result.text and result.text.strip()
            ]

            if bboxes:
                # 在圖片上擦除文字區域
                erased_image = inpainter.erase_multiple_regions(
                    img_array_copy, bboxes, fill_color=(255, 255, 255)
                )
            else:
                erased_image = img_array_copy

            # 儲存擦除版圖片並新增到 erased_generator
            tmp_erased_path = tempfile.mktemp(suffix=".png")
            try:
                Image.fromarray(erased_image).save(tmp_erased_path)
                # 擦除版 PDF 也新增文字層（用於後續翻譯）
                erased_generator.add_page(tmp_erased_path, sorted_results)
            finally:
                if os.path.exists(tmp_erased_path):
                    os.remove(tmp_erased_path)

    def _process_single_hybrid_page(
        self,
        page,
        page_num: int,
        dpi: int,
        pdf_generator: PDFGenerator,
        erased_generator: PDFGenerator,
        inpainter: Optional["TextInpainter"],
    ) -> Tuple[str, str, List[OCRResult]]:
        """處理單一頁面（混合模式）

        Args:
            page: PyMuPDF 頁面物件
            page_num: 頁碼（0-based）
            dpi: 解析度
            pdf_generator: PDF 生成器
            erased_generator: 擦除版生成器
            inpainter: 文字擦除器

        Returns:
            Tuple of (page_markdown, page_text, ocr_results)
        """
        logging.info(f"處理第 {page_num + 1} 頁")

        # 轉換為圖片
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)

        # 使用共用工具函數轉換為 numpy 陣列
        img_array = pixmap_to_numpy(pixmap)

        # 步驟 1：版面分析
        logging.info(f"  執行版面分析...")
        structure_output = self.structure_engine.predict(input=img_array)

        # 步驟 2：提取 Markdown
        page_markdown = self._extract_markdown_from_structure_output(
            structure_output, page_num
        )

        # 提取版面區塊資訊
        layout_blocks = []
        for res in structure_output:
            try:
                if hasattr(res, "layout_parsing_result"):
                    lp_result = res.layout_parsing_result
                    if hasattr(lp_result, "blocks"):
                        layout_blocks.extend(lp_result.blocks)
                if hasattr(res, "blocks"):
                    layout_blocks.extend(res.blocks)
                elif isinstance(res, dict):
                    blocks = res.get("blocks", []) or res.get("layout_blocks", [])
                    if blocks:
                        layout_blocks.extend(blocks)
            except Exception as block_err:
                logging.debug(f"提取版面區塊失敗: {block_err}")

        logging.info(f"  取得 {len(layout_blocks)} 個版面區塊")

        # 步驟 3：提取 OCR 座標（使用 Markdown 匹配過濾）
        logging.info(f"  提取文字座標（使用 Markdown 匹配過濾）...")
        sorted_results = self._extract_ocr_from_structure(
            structure_output, markdown_text=page_markdown
        )
        logging.info(f"  返回 {len(sorted_results)} 個結果")

        # 步驟 4：生成雙 PDF
        if sorted_results:
            self._generate_dual_pdfs(
                pixmap,
                img_array,
                sorted_results,
                pdf_generator,
                erased_generator,
                inpainter,
            )

        # 提取文字
        page_text = self.get_text(sorted_results)

        # 清理
        del pixmap
        gc.collect()

        return page_markdown, page_text, sorted_results

    def _save_markdown_output(
        self,
        all_markdown: List[str],
        markdown_output: str,
        result_summary: Dict[str, Any],
    ) -> None:
        """儲存 Markdown 輸出"""
        # 套用英文空格修復
        fixed_markdown = [fix_english_spacing(md) for md in all_markdown]
        with open(markdown_output, "w", encoding="utf-8") as f:
            f.write("\n\n---\n\n".join(fixed_markdown))
        result_summary["markdown_file"] = markdown_output
        print(f"[OK] Markdown 已儲存：{markdown_output}")

    def _save_json_output(
        self,
        all_ocr_results: List[List[OCRResult]],
        json_output: str,
        pdf_path: str,
        result_summary: Dict[str, Any],
    ) -> None:
        """儲存 JSON 輸出項目"""
        try:
            import json

            # 將 OCR 結果轉換為可序列化的格式
            json_data = {"input": pdf_path, "pages": []}
            for page_num, page_results in enumerate(all_ocr_results, 1):
                page_data = {"page": page_num, "text_blocks": []}
                for result in page_results:
                    page_data["text_blocks"].append(
                        {
                            "text": result.text,
                            "confidence": result.confidence,
                            "bbox": [[float(p[0]), float(p[1])] for p in result.bbox],
                        }
                    )
                json_data["pages"].append(page_data)

            with open(json_output, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            result_summary["json_file"] = json_output
            print(f"[OK] JSON 已儲存：{json_output}")
        except Exception as json_err:
            logging.warning(f"JSON 輸出失敗: {json_err}")

    def _save_html_output(
        self,
        all_markdown: List[str],
        html_output: str,
        pdf_path: str,
        result_summary: Dict[str, Any],
    ) -> None:
        """儲存 HTML 輸出"""
        try:
            # 將 Markdown 轉換為 HTML
            html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{Path(pdf_path).stem} - OCR 結果</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
        h1, h2, h3 {{ color: #333; }}
        hr {{ border: none; border-top: 1px solid #ddd; margin: 20px 0; }}
        pre {{ background: #f5f5f5; padding: 10px; overflow-x: auto; }}
        code {{ background: #f5f5f5; padding: 2px 5px; border-radius: 3px; }}
        img {{ max-width: 100%; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f5f5f5; }}
    </style>
</head>
<body>
"""
            # 簡單的 Markdown 到 HTML 轉換
            for md in all_markdown:
                fixed_md = fix_english_spacing(md)
                # 基本轉換
                lines = fixed_md.split("\n")
                for line in lines:
                    if line.startswith("### "):
                        html_content += f"<h3>{line[4:]}</h3>\n"
                    elif line.startswith("## "):
                        html_content += f"<h2>{line[3:]}</h2>\n"
                    elif line.startswith("# "):
                        html_content += f"<h1>{line[2:]}</h1>\n"
                    elif line.startswith("- "):
                        html_content += f"<li>{line[2:]}</li>\n"
                    elif line.startswith("* "):
                        html_content += f"<li>{line[2:]}</li>\n"
                    elif line.strip() == "---":
                        html_content += "<hr>\n"
                    elif line.strip():
                        html_content += f"<p>{line}</p>\n"
                html_content += "<hr>\n"

            html_content += """
</body>
</html>"""

            with open(html_output, "w", encoding="utf-8") as f:
                f.write(html_content)
            result_summary["html_file"] = html_output
            print(f"[OK] HTML 已儲存：{html_output}")
        except Exception as html_err:
            logging.warning(f"HTML 輸出失敗: {html_err}")

    def _save_hybrid_outputs(
        self,
        all_markdown: List[str],
        all_ocr_results: List[List[OCRResult]],
        markdown_output: Optional[str],
        json_output: Optional[str],
        html_output: Optional[str],
        pdf_path: str,
        result_summary: Dict[str, Any],
    ) -> None:
        """儲存混合模式的各種輸出檔案（統籌方法）"""
        # 儲存 Markdown
        if markdown_output and all_markdown:
            self._save_markdown_output(all_markdown, markdown_output, result_summary)

        # 儲存 JSON
        if json_output:
            self._save_json_output(
                all_ocr_results, json_output, pdf_path, result_summary
            )

        # 儲存 HTML
        if html_output:
            self._save_html_output(all_markdown, html_output, pdf_path, result_summary)

    def _process_hybrid_pdf(
        self,
        pdf_path: str,
        output_path: str,
        markdown_output: str,
        json_output: Optional[str],
        html_output: Optional[str],
        dpi: int,
        show_progress: bool,
        result_summary: Dict[str, Any],
        translate_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """處理 PDF 的混合模式

        同時生成：
        1. *_hybrid.pdf（原文可搜尋）
        2. *_erased.pdf（擦除版 + 文字層）
        3. *_hybrid.md（Markdown）
        4. *_hybrid.json（JSON，可選）
        5. *_hybrid.html（HTML，可選）

        Args:
            translate_config: 翻譯配置（可選），包含 source_lang, target_lang, ollama_model 等
        """

        # === 1. 初始化 ===
        pdf_doc = fitz.open(pdf_path)
        total_pages = len(pdf_doc)

        print(f"PDF 共 {total_pages} 页")
        logging.info(f"PDF 共 {total_pages} 页")

        # 设定生成器
        pdf_gen, erased_gen, inpainter, erased_path = self._setup_hybrid_generators(
            output_path
        )

        # 初始化收集器
        all_markdown = []
        all_text = []
        all_ocr_results = []  # 收集每页 OCR 结果，用于翻译

        # 初始化统计收集器
        stats_collector = StatsCollector(
            input_file=pdf_path, mode="hybrid", total_pages=total_pages
        )

        # === 2. 处理所有页面 ===
        page_iterator = range(total_pages)
        if show_progress and HAS_TQDM:
            page_iterator = tqdm(page_iterator, desc="混合模式处理中", unit="页", ncols=80)
            page_iterator = tqdm(page_iterator, desc="混合模式處理中", unit="頁", ncols=80)

        for page_num in page_iterator:
            try:
                stats_collector.start_page(page_num)
                page = pdf_doc[page_num]

                # 處理單頁
                page_md, page_txt, ocr_res = self._process_single_hybrid_page(
                    page, page_num, dpi, pdf_gen, erased_gen, inpainter
                )

                # 收集結果
                all_markdown.append(page_md)
                all_text.append(page_txt)
                all_ocr_results.append(ocr_res)

                result_summary["pages_processed"] += 1

                # 記錄頁面統計
                stats_collector.finish_page(
                    page_num=page_num, text=page_txt, ocr_results=ocr_res
                )

            except Exception as page_error:
                logging.error(f"處理第 {page_num + 1} 頁時發生錯誤: {page_error}")
                logging.error(traceback.format_exc())
                continue

        pdf_doc.close()

        # === 3. 儲存 PDF ===
        if pdf_gen.save():
            result_summary["searchable_pdf"] = output_path
            print(f"[OK] 可搜尋 PDF 已儲存：{output_path}")

        if erased_gen.save():
            result_summary["erased_pdf"] = erased_path
            print(f"[OK] 擦除版 PDF 已儲存：{erased_path}")

        # === 4. 儲存其他輸出 ===
        self._save_hybrid_outputs(
            all_markdown,
            all_ocr_results,
            markdown_output,
            json_output,
            html_output,
            pdf_path,
            result_summary,
        )

        result_summary["text_content"] = all_text

        # === 5. 翻譯處理（如果啟用）===
        # Debug 模式時關閉翻譯功能
        if translate_config and HAS_TRANSLATOR:
            if self.debug_mode:
                print(f"[DEBUG] Debug 模式已啟用，跳過翻譯處理")
                logging.info("Debug 模式已啟用，跳過翻譯處理")
            else:
                self._process_translation_on_pdf(
                    erased_pdf_path=erased_path,
                    ocr_results_per_page=all_ocr_results,
                    translate_config=translate_config,
                    result_summary=result_summary,
                    dpi=dpi,
                )

        # === 6. 完成統計 ===
        print(f"[OK] 混合模式處理完成：{result_summary['pages_processed']} 頁")

        final_stats = stats_collector.finish()
        final_stats.print_summary()
        result_summary["stats"] = final_stats.to_dict()

        return result_summary

    def _process_hybrid_image(
        self,
        image_path: str,
        output_path: str,
        markdown_output: str,
        result_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        """處理圖片的混合模式"""

        logging.info(f"處理圖片: {image_path}")

        # 執行雙引擎處理
        structure_output = self.structure_engine.predict(input=image_path)
        ocr_output = self.ocr_engine.predict(input=image_path)

        # 合併結果
        sorted_results, page_markdown = self._merge_hybrid_results(
            structure_output, ocr_output, 1
        )

        # 生成可搜尋 PDF
        if sorted_results:
            pdf_generator = PDFGenerator(output_path, debug_mode=self.debug_mode)
            pdf_generator.add_page(image_path, sorted_results)
            if pdf_generator.save():
                result_summary["searchable_pdf"] = output_path
                print(f"[OK] 可搜尋 PDF 已儲存：{output_path}")

        # 儲存 Markdown
        if markdown_output and page_markdown:
            with open(markdown_output, "w", encoding="utf-8") as f:
                f.write(page_markdown)
            result_summary["markdown_file"] = markdown_output
            print(f"[OK] Markdown 已儲存：{markdown_output}")

        result_summary["pages_processed"] = 1
        result_summary["text_content"] = [self.get_text(sorted_results)]

        return result_summary

    def _merge_hybrid_results(
        self, structure_output, ocr_output, page_num: int
    ) -> Tuple[List[OCRResult], str]:
        """
        合併版面分析和 OCR 結果

        Args:
            structure_output: PP-StructureV3 的輸出
            ocr_output: PP-OCRv5 的輸出
            page_num: 頁碼

        Returns:
            Tuple[List[OCRResult], str]: 排序後的 OCR 結果和 Markdown 內容
        """
        # 解析 OCR 結果取得精確座標
        ocr_results = self._parse_predict_result(ocr_output)

        # 嘗試從 structure 輸出取得版面資訊
        layout_blocks = []
        markdown_parts = []

        try:
            for res in structure_output:
                # 取得 Markdown 內容（如果有）
                md_content = None

                if hasattr(res, "markdown"):
                    md_content = res.markdown
                elif isinstance(res, dict):
                    md_content = res.get("markdown", None)

                # 確保只添加字串類型
                if md_content is not None:
                    if isinstance(md_content, str):
                        markdown_parts.append(md_content)
                    elif isinstance(md_content, dict):
                        # 如果是 dict，嘗試提取文字內容
                        text = md_content.get("text", "") or md_content.get(
                            "content", ""
                        )
                        if text and isinstance(text, str):
                            markdown_parts.append(text)
                    elif isinstance(md_content, list):
                        # 如果是 list，連接所有字串元素
                        for item in md_content:
                            if isinstance(item, str):
                                markdown_parts.append(item)
                            elif isinstance(item, dict):
                                text = item.get("text", "") or item.get("content", "")
                                if text and isinstance(text, str):
                                    markdown_parts.append(text)

                # 取得版面區塊資訊
                if hasattr(res, "layout_blocks"):
                    layout_blocks.extend(res.layout_blocks)
                elif hasattr(res, "blocks"):
                    layout_blocks.extend(res.blocks)
                elif isinstance(res, dict):
                    blocks = res.get("layout_blocks", []) or res.get("blocks", [])
                    if blocks:
                        layout_blocks.extend(blocks)

        except Exception as e:
            logging.warning(f"解析 structure 輸出時發生錯誤: {e}")

        # 如果有版面資訊，根據版面順序排序 OCR 結果
        if layout_blocks:
            sorted_results = self._sort_ocr_by_layout(ocr_results, layout_blocks)
        else:
            # 沒有版面資訊，使用預設的從上到下、從左到右排序
            sorted_results = self._sort_ocr_by_position(ocr_results)

        # 組合 Markdown
        if markdown_parts:
            # 過濾空字串
            valid_parts = [p for p in markdown_parts if p and isinstance(p, str)]
            if valid_parts:
                page_markdown = f"## 第 {page_num} 頁\n\n" + "\n\n".join(valid_parts)
            else:
                page_markdown = f"## 第 {page_num} 頁\n\n" + self.get_text(
                    sorted_results, separator="\n\n"
                )
        else:
            # 使用排序後的文字生成 Markdown
            page_markdown = f"## 第 {page_num} 頁\n\n" + self.get_text(
                sorted_results, separator="\n\n"
            )

        return sorted_results, page_markdown

    def _extract_ocr_from_structure(
        self, structure_output, markdown_text: str = None
    ) -> List[OCRResult]:
        """
        從 PP-StructureV3 輸出提取文字座標

        策略（修正版）：
        1. 優先使用 overall_ocr_res 的行級結果（精確座標）
        2. 如果 overall_ocr_res 不可用，才回退到 parsing_res_list 的區塊座標

        注意：overall_ocr_res 是行級結果，parsing_res_list 是段落級結果，
        兩者粒度不同，不應嘗試匹配。

        Args:
            structure_output: PP-StructureV3 的輸出（LayoutParsingResultV2 列表）
            markdown_text: 可選，Markdown 文字用於過濾 OCR 結果（目前不使用）

        Returns:
            List[OCRResult]: OCR 結果列表
        """
        ocr_results = []

        try:
            for res in structure_output:
                # ========== 方式 1：直接使用 overall_ocr_res（行級精確座標）==========
                if "overall_ocr_res" in res:
                    overall_ocr = res["overall_ocr_res"]
                    if overall_ocr is not None:
                        try:
                            texts = overall_ocr.get("rec_texts", [])
                            scores = overall_ocr.get("rec_scores", [])
                            rec_boxes = overall_ocr.get("rec_boxes")
                            dt_polys = overall_ocr.get("dt_polys", [])

                            logging.info(
                                f"  overall_ocr_res: texts={len(texts) if texts else 0}, boxes={len(rec_boxes) if rec_boxes is not None else 0}"
                            )

                            if texts:
                                # 優先使用 rec_boxes
                                if rec_boxes is not None and len(rec_boxes) > 0:
                                    boxes_list = (
                                        rec_boxes.tolist()
                                        if hasattr(rec_boxes, "tolist")
                                        else rec_boxes
                                    )
                                    for i, (box, text) in enumerate(
                                        zip(boxes_list, texts)
                                    ):
                                        if text and str(text).strip():
                                            x1, y1, x2, y2 = (
                                                float(box[0]),
                                                float(box[1]),
                                                float(box[2]),
                                                float(box[3]),
                                            )
                                            bbox = [
                                                [x1, y1],
                                                [x2, y1],
                                                [x2, y2],
                                                [x1, y2],
                                            ]
                                            conf = (
                                                float(scores[i])
                                                if i < len(scores)
                                                else 0.9
                                            )
                                            ocr_results.append(
                                                OCRResult(
                                                    text=fix_english_spacing(str(text)),
                                                    confidence=conf,
                                                    bbox=bbox,
                                                )
                                            )
                                    logging.info(
                                        f"  從 rec_boxes 提取了 {len(ocr_results)} 個結果"
                                    )

                                # 使用 dt_polys
                                elif dt_polys and len(dt_polys) > 0:
                                    for i, (poly, text) in enumerate(
                                        zip(dt_polys, texts)
                                    ):
                                        if (
                                            poly is not None
                                            and text
                                            and str(text).strip()
                                        ):
                                            poly_list = (
                                                poly.tolist()
                                                if hasattr(poly, "tolist")
                                                else poly
                                            )
                                            bbox = [
                                                [float(p[0]), float(p[1])]
                                                for p in poly_list
                                            ]
                                            conf = (
                                                float(scores[i])
                                                if i < len(scores)
                                                else 0.9
                                            )
                                            ocr_results.append(
                                                OCRResult(
                                                    text=fix_english_spacing(str(text)),
                                                    confidence=conf,
                                                    bbox=bbox,
                                                )
                                            )
                                    logging.info(
                                        f"  從 dt_polys 提取了 {len(ocr_results)} 個結果"
                                    )

                        except Exception as e:
                            logging.warning(f"  訪問 overall_ocr_res 失敗: {e}")
                            logging.warning(traceback.format_exc())

                # ========== 方式 2：回退到 parsing_res_list（區塊級座標）==========
                # 只有當 overall_ocr_res 沒有取得結果時才使用
                if not ocr_results and "parsing_res_list" in res:
                    parsing_list = res["parsing_res_list"]
                    if parsing_list:
                        logging.info(
                            f"  回退到 parsing_res_list，共 {len(parsing_list)} 個區塊"
                        )

                        for block in parsing_list:
                            try:
                                bbox = getattr(block, "bbox", None)
                                content = getattr(block, "content", None)

                                if (
                                    bbox is not None
                                    and content
                                    and str(content).strip()
                                ):
                                    content_str = str(content).strip()
                                    if len(bbox) >= 4:
                                        x1, y1, x2, y2 = (
                                            float(bbox[0]),
                                            float(bbox[1]),
                                            float(bbox[2]),
                                            float(bbox[3]),
                                        )
                                        bbox_points = [
                                            [x1, y1],
                                            [x2, y1],
                                            [x2, y2],
                                            [x1, y2],
                                        ]
                                        ocr_results.append(
                                            OCRResult(
                                                text=fix_english_spacing(content_str),
                                                confidence=0.85,
                                                bbox=bbox_points,
                                            )
                                        )
                            except Exception as e:
                                logging.debug(f"  處理 block 失敗: {e}")
                                continue

                        logging.info(f"  從 parsing_res_list 提取了 {len(ocr_results)} 個結果")

        except Exception as e:
            logging.warning(f"從 structure 輸出提取 OCR 結果失敗: {e}")
            logging.warning(traceback.format_exc())

        logging.info(f"  總共提取 {len(ocr_results)} 個 OCR 結果")
        return ocr_results

    def _sort_ocr_by_layout(
        self, ocr_results: List[OCRResult], layout_blocks: List
    ) -> List[OCRResult]:
        """根據版面區塊順序排序 OCR 結果"""

        if not layout_blocks:
            return self._sort_ocr_by_position(ocr_results)

        # 建立區塊到 OCR 結果的對應
        block_results = {i: [] for i in range(len(layout_blocks))}
        unassigned = []

        for ocr in ocr_results:
            assigned = False
            ocr_center = (ocr.x + ocr.width / 2, ocr.y + ocr.height / 2)

            for i, block in enumerate(layout_blocks):
                try:
                    # 取得區塊邊界
                    if hasattr(block, "bbox"):
                        bbox = block.bbox
                    elif isinstance(block, dict) and "bbox" in block:
                        bbox = block["bbox"]
                    else:
                        continue

                    # 檢查 OCR 結果是否在區塊內
                    if (
                        bbox[0] <= ocr_center[0] <= bbox[2]
                        and bbox[1] <= ocr_center[1] <= bbox[3]
                    ):
                        block_results[i].append(ocr)
                        assigned = True
                        break
                except:
                    continue

            if not assigned:
                unassigned.append(ocr)

        # 按區塊順序組合結果
        sorted_results = []
        for i in range(len(layout_blocks)):
            # 區塊內的結果按位置排序
            block_ocrs = self._sort_ocr_by_position(block_results[i])
            sorted_results.extend(block_ocrs)

        # 加入未分配的結果
        sorted_results.extend(self._sort_ocr_by_position(unassigned))

        return sorted_results

    # ========== Translation 處理輔助方法 ==========

    def _setup_translation_tools(
        self, erased_pdf_path: str, translate_config: Dict[str, Any]
    ) -> Tuple:
        """設定翻譯所需的工具和生成器

        Args:
            erased_pdf_path: 擦除版 PDF 路徑
            translate_config: 翻譯配置

        Returns:
            Tuple of (translator, renderer, pdf_doc, hybrid_doc,
                      mono_generator, bilingual_generator,
                      translated_path, bilingual_path)
        """
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

    def _get_page_images(
        self, pdf_doc, hybrid_doc, page_num: int, dpi: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """取得擦除版和原始版頁面圖片

        Args:
            pdf_doc: 擦除版 PDF 文件
            hybrid_doc: 原始 hybrid PDF 文件
            page_num: 頁碼（0-based）
            dpi: 解析度

        Returns:
            Tuple of (erased_image, original_image)
        """
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        # 取得擦除版圖片
        erased_page = pdf_doc[page_num]
        erased_pixmap = erased_page.get_pixmap(matrix=matrix)
        erased_image = pixmap_to_numpy(erased_pixmap, copy=True)

        # 取得原始圖片（用於雙語）
        original_image = erased_image.copy()
        if hybrid_doc:
            hybrid_page = hybrid_doc[page_num]
            hybrid_pixmap = hybrid_page.get_pixmap(matrix=matrix)
            original_image = pixmap_to_numpy(hybrid_pixmap, copy=True)

        return erased_image, original_image

    def _translate_page_texts(
        self,
        page_ocr_results: List[OCRResult],
        translator,
        source_lang: str,
        target_lang: str,
        page_num: int,
    ) -> List:
        """翻譯頁面的所有文字

        Args:
            page_ocr_results: 頁面的 OCR 結果
            translator: 翻譯器物件
            source_lang: 來源語言
            target_lang: 目標語言
            page_num: 頁碼（0-based）

        Returns:
            List[TranslatedBlock]: 翻譯後的文字塊列表
        """
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

    def _render_translated_text(
        self,
        erased_image: np.ndarray,
        erased_page,  # PyMuPDF page 物件
        translated_blocks: List,
        renderer,
        use_ocr_workaround: bool,
        dpi: int,
    ) -> np.ndarray:
        """在擦除版圖片上繪製翻譯文字

        Args:
            erased_image: 擦除版圖片
            erased_page: PyMuPDF 頁面物件（OCR workaround 模式需要）
            translated_blocks: 翻譯後的文字塊列表
            renderer: TextRenderer 物件
            use_ocr_workaround: 是否使用 OCR 補救模式
            dpi: 解析度

        Returns:
            np.ndarray: 繪製了翻譯文字的圖片
        """
        if use_ocr_workaround:
            # OCR 補救模式：直接在 PDF 頁面上操作
            logging.info("使用 OCR 補救模式繪製翻譯文字")
            workaround = OCRWorkaround(margin=2.0, force_black=True)

            for block in translated_blocks:
                # 計算座標
                x = min(p[0] for p in block.bbox)
                y = min(p[1] for p in block.bbox)
                width = max(p[0] for p in block.bbox) - x
                height = max(p[1] for p in block.bbox) - y

                text_block = TextBlock(
                    text=block.translated_text, x=x, y=y, width=width, height=height
                )
                workaround.add_text_with_mask(
                    erased_page, text_block, block.translated_text
                )

            # 從修改後的頁面取得圖片
            zoom = dpi / 72.0
            matrix = fitz.Matrix(zoom, zoom)
            modified_pixmap = erased_page.get_pixmap(matrix=matrix)
            translated_image = pixmap_to_numpy(modified_pixmap, copy=True)
        else:
            # 標準模式：使用 TextRenderer
            translated_image = erased_image.copy()
            translated_image = renderer.render_multiple_texts(
                translated_image, translated_blocks
            )

        return translated_image

    def _process_single_translation_page(
        self,
        page_num: int,
        ocr_results_per_page: List[List[OCRResult]],
        pdf_doc,
        hybrid_doc,
        translator,
        renderer,
        mono_generator,
        bilingual_generator,
        translate_config: Dict[str, Any],
        dpi: int,
    ) -> None:
        """處理單頁翻譯

        完整流程：取得圖片 → 翻譯 → 繪製 → 新增到生成器

        Args:
            page_num: 頁碼（0-based）
            ocr_results_per_page: 每頁的 OCR 結果
            pdf_doc: 擦除版 PDF 文件
            hybrid_doc: 原始 hybrid PDF 文件
            translator: 翻譯器物件
            renderer: TextRenderer 物件
            mono_generator: 單語 PDF 生成器
            bilingual_generator: 雙語 PDF 生成器
            translate_config: 翻譯配置
            dpi: 解析度
        """
        # 檢查 OCR 結果
        if page_num >= len(ocr_results_per_page):
            logging.warning(f"第 {page_num + 1} 頁沒有 OCR 結果")
            return

        page_ocr_results = ocr_results_per_page[page_num]

        # 獲取頁面圖片
        erased_image, original_image = self._get_page_images(
            pdf_doc, hybrid_doc, page_num, dpi
        )

        # 如果沒有 OCR 結果，直接新增空白頁
        if not page_ocr_results:
            if mono_generator:
                mono_generator.add_page(erased_image)
            if bilingual_generator:
                bilingual_generator.add_bilingual_page(original_image, erased_image)
            return

        # 翻譯文字
        translated_blocks = self._translate_page_texts(
            page_ocr_results,
            translator,
            translate_config["source_lang"],
            translate_config["target_lang"],
            page_num,
        )

        # 如果沒有需要翻譯的文字
        if not translated_blocks:
            if mono_generator:
                mono_generator.add_page(erased_image)
            if bilingual_generator:
                bilingual_generator.add_bilingual_page(original_image, erased_image)
            return

        # 繪製翻譯文字
        erased_page = (
            pdf_doc[page_num] if translate_config.get("ocr_workaround") else None
        )
        translated_image = self._render_translated_text(
            erased_image,
            erased_page,
            translated_blocks,
            renderer,
            translate_config.get("ocr_workaround", False),
            dpi,
        )

        # 新增到生成器
        if mono_generator:
            mono_generator.add_page(translated_image)
        if bilingual_generator:
            bilingual_generator.add_bilingual_page(original_image, translated_image)

        # 清理
        gc.collect()

    def _save_translation_pdfs(
        self,
        mono_generator,
        bilingual_generator,
        translated_path: Optional[str],
        bilingual_path: Optional[str],
        result_summary: Dict[str, Any],
    ) -> None:
        """儲存翻譯版和雙語版 PDF

        Args:
            mono_generator: 單語 PDF 生成器
            bilingual_generator: 雙語 PDF 生成器
            translated_path: 翻譯版 PDF 路徑
            bilingual_path: 雙語版 PDF 路徑
            result_summary: 結果摘要（會被更新）
        """
        # 儲存翻譯版 PDF
        if mono_generator and translated_path:
            if mono_generator.save(translated_path):
                result_summary["translated_pdf"] = translated_path
                print(f"[OK] 翻譯 PDF 已儲存：{translated_path}")
            mono_generator.close()

        # 儲存雙語版 PDF
        if bilingual_generator and bilingual_path:
            if bilingual_generator.save(bilingual_path):
                result_summary["bilingual_pdf"] = bilingual_path
                print(f"[OK] 雙語對照 PDF 已儲存：{bilingual_path}")
            bilingual_generator.close()

    def _sort_ocr_by_position(self, ocr_results: List[OCRResult]) -> List[OCRResult]:
        """按位置排序 OCR 結果（從上到下、從左到右）"""

        if not ocr_results:
            return []

        # 按 Y 座標分組（同一行）
        line_threshold = 10  # 像素閾值
        lines = []

        sorted_by_y = sorted(ocr_results, key=lambda r: r.y)

        current_line = [sorted_by_y[0]]
        current_y = sorted_by_y[0].y

        for ocr in sorted_by_y[1:]:
            if abs(ocr.y - current_y) <= line_threshold:
                current_line.append(ocr)
            else:
                lines.append(current_line)
                current_line = [ocr]
                current_y = ocr.y

        lines.append(current_line)

        # 每行按 X 座標排序
        sorted_results = []
        for line in lines:
            sorted_line = sorted(line, key=lambda r: r.x)
            sorted_results.extend(sorted_line)

        return sorted_results

    def _process_translation_on_pdf(
        self,
        erased_pdf_path: str,  # 使用擦除版 PDF 作為翻譯基礎
        ocr_results_per_page: List[List[OCRResult]],
        translate_config: Dict[str, Any],
        result_summary: Dict[str, Any],
        dpi: int = 150,
    ) -> None:
        """在擦除版 PDF 基礎上進行翻譯處理

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
        """
        print(f"\n[翻譯] 開始翻譯處理...")
        logging.info(f"開始翻譯處理: {erased_pdf_path}")

        print(f"   來源語言: {translate_config.get('source_lang', 'auto')}")
        print(f"   目標語言: {translate_config.get('target_lang', 'en')}")
        print(f"   Ollama 模型: {translate_config.get('ollama_model', 'qwen2.5:7b')}")

        try:
            # === 1. 初始化工具 ===
            (
                translator,
                renderer,
                pdf_doc,
                hybrid_doc,
                mono_gen,
                bilingual_gen,
                trans_path,
                bi_path,
            ) = self._setup_translation_tools(erased_pdf_path, translate_config)

            total_pages = len(pdf_doc)

            # === 2. 處理所有頁面 ===
            page_iter = range(total_pages)
            if HAS_TQDM:
                page_iter = tqdm(page_iter, desc="翻譯頁面", unit="頁", ncols=80)

            for page_num in page_iter:
                try:
                    self._process_single_translation_page(
                        page_num,
                        ocr_results_per_page,
                        pdf_doc,
                        hybrid_doc,
                        translator,
                        renderer,
                        mono_gen,
                        bilingual_gen,
                        translate_config,
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

        except Exception as e:
            error_msg = f"翻譯處理失敗: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            print(f"錯誤：{error_msg}")
            result_summary["translation_error"] = str(e)

    def process_translate(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        source_lang: str = "auto",
        target_lang: str = "en",
        ollama_model: str = "qwen2.5:7b",
        ollama_url: str = "http://localhost:11434",
        no_mono: bool = False,
        no_dual: bool = False,
        dual_mode: str = "alternating",
        dual_translate_first: bool = False,
        font_path: Optional[str] = None,
        dpi: int = 150,
        show_progress: bool = True,
        json_output: Optional[str] = None,
        html_output: Optional[str] = None,
        ocr_workaround: bool = False,
    ) -> Dict[str, Any]:
        """
        翻譯 PDF 並生成多種輸出（簡化版，調用 process_hybrid）

        輸出檔案：
        - *_hybrid.pdf：可搜尋 PDF（原文）
        - *_hybrid.md：Markdown 輸出
        - *_hybrid.json：JSON 輸出（可選）
        - *_hybrid.html：HTML 輸出（可選）
        - *_translated_{lang}.pdf：翻譯 PDF（可搜尋）
        - *_bilingual_{lang}.pdf：雙語對照 PDF（除非 --no-dual）

        Args:
            input_path: 輸入 PDF 路徑
            output_path: 可搜尋 PDF 輸出路徑（可選）
            source_lang: 來源語言（auto=自動偵測）
            target_lang: 目標語言
            ollama_model: Ollama 模型名稱
            ollama_url: Ollama API 地址
            no_mono: 不輸出純翻譯 PDF
            no_dual: 不輸出雙語對照 PDF
            dual_mode: 雙語模式（alternating 或 side-by-side）
            dual_translate_first: 雙語模式中譯文在前
            font_path: 自訂字體路徑（目前未使用）
            dpi: PDF 轉圖片解析度
            show_progress: 是否顯示進度條
            json_output: JSON 輸出路徑（可選）
            html_output: HTML 輸出路徑（可選）

        Returns:
            Dict[str, Any]: 處理結果摘要
        """
        if not HAS_TRANSLATOR:
            raise ImportError("翻譯模組不可用，請確認 pdf_translator.py 存在且依賴已安裝")

        if self.mode != "hybrid":
            raise ValueError(f"process_translate 需要 hybrid 模式，當前模式: {self.mode}")

        print(f"\n[翻譯] 正在處理: {input_path}")
        print(f"   來源語言: {source_lang}")
        print(f"   目標語言: {target_lang}")
        print(f"   Ollama 模型: {ollama_model}")
        logging.info(f"開始翻譯模式處理: {input_path}")

        # 建立翻譯配置
        translate_config = {
            "source_lang": source_lang,
            "target_lang": target_lang,
            "ollama_model": ollama_model,
            "ollama_url": ollama_url,
            "no_mono": no_mono,
            "no_dual": no_dual,
            "dual_mode": dual_mode,
            "dual_translate_first": dual_translate_first,
            "font_path": font_path,
            "ocr_workaround": ocr_workaround,
        }

        # 直接調用 process_hybrid，傳入翻譯配置
        # process_hybrid 會在生成可搜尋 PDF 後自動調用 _process_translation_on_pdf
        result = self.process_hybrid(
            input_path=input_path,
            output_path=output_path,
            json_output=json_output,
            html_output=html_output,
            dpi=dpi,
            show_progress=show_progress,
            translate_config=translate_config,
        )

        # 更新結果摘要
        result["mode"] = "translate"
        result["source_lang"] = source_lang
        result["target_lang"] = target_lang

        return result


def main():
    """命令列入口點"""
    # === 1. 導入 CLI 模組 ===
    from paddleocr_toolkit.cli import (
        ModeProcessor,
        OutputPathManager,
        create_argument_parser,
        process_args_overrides,
    )

    # === 2. 參數解析 ===
    parser = create_argument_parser()
    args = parser.parse_args()

    # === 3. 輸入驗證 ===
    input_path = Path(args.input)
    if not input_path.exists():
        logging.error(f"輸入路徑不存在: {args.input}")
        print(f"錯誤：輸入路徑不存在: {args.input}")
        sys.exit(1)

    script_dir = Path(__file__).parent.resolve()

    logging.info(f"=" * 60)
    logging.info(f"開始執行 PaddleOCR 工具")
    logging.info(f"輸入路徑: {input_path}")
    logging.info(f"OCR 模式: {args.mode}")

    # === 5. 處理參數覆蓋 ===
    args = process_args_overrides(args)

    # === 6. 設定輸出路徑 ===
    output_manager = OutputPathManager(str(input_path), args.mode)
    args = output_manager.process_mode_outputs(args, script_dir)

    # 顯示輸出設定摘要
    output_manager.print_output_summary(args)
    if not args.no_progress and HAS_TQDM:
        print(f"[進度條] 啟用")
    print()

    # === 7. 檢查模式依賴 ===
    mode_dependencies = {
        "structure": (HAS_STRUCTURE, "PP-StructureV3"),
        "vl": (HAS_VL, "PaddleOCR-VL"),
        "formula": (HAS_FORMULA, "FormulaRecPipeline"),
        "hybrid": (HAS_STRUCTURE, "Hybrid 模式需要 PP-StructureV3"),
    }

    if args.mode in mode_dependencies:
        available, module_name = mode_dependencies[args.mode]
        if not available:
            print(f"錯誤：{module_name} 模組不可用")
            print("請確認已安裝最新版 paddleocr: pip install -U paddleocr")
            sys.exit(1)

    # === 8. 初始化 OCR 工具 ===
    tool = PaddleOCRTool(
        mode=args.mode,
        use_orientation_classify=args.orientation_classify,
        use_doc_unwarping=args.unwarping,
        use_textline_orientation=args.textline_orientation,
        device=args.device,
        debug_mode=args.debug_text,
        compress_images=not args.no_compress,
        jpeg_quality=args.jpeg_quality,
    )

    # 顯示壓縮設定
    if not args.no_compress:
        print(f"[壓縮] 啟用（JPEG 品質：{args.jpeg_quality}%）")
    else:
        print(f"[壓縮] 停用（使用 PNG 無損格式）")

    # === 9. 執行 OCR ===
    processor = ModeProcessor(tool, args, input_path, script_dir)
    result = processor.process()


if __name__ == "__main__":
    log_file = None
    try:
        # 先設定日誌（在任何其他操作之前）
        log_file = setup_logging()

        # 執行主程式
        main()

    except KeyboardInterrupt:
        if log_file:
            logging.info("\n使用者中斷執行 (Ctrl+C)")
        print("\n\n已中斷執行")
        sys.exit(0)

    except Exception as e:
        error_msg = f"程式執行時發生嚴重錯誤: {str(e)}"
        if log_file:
            logging.error("=" * 60)
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            logging.error("=" * 60)
            # 強制 flush
            for handler in logging.root.handlers:
                handler.flush()

        print(f"\n{'='*60}")
        print(f"錯誤：{error_msg}")
        print(f"詳細錯誤訊息已記錄到：{log_file}")
        print(f"{'='*60}\n")
        traceback.print_exc()
        sys.exit(1)

    finally:
        # 確保日誌被 flush
        if log_file:
            logging.info("程式結束")
            for handler in logging.root.handlers:
                handler.flush()
                handler.close()
