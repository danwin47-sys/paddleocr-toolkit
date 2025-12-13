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
import os
import sys
import tempfile
import shutil
import logging
import traceback
import gc
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

# 停用模型來源檢查以加快啟動速度（已有本機模型時不需要連線檢查）
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

# ===== 從 paddleocr_toolkit 套件匯入模組 =====
try:
    from paddleocr_toolkit.processors import (
        fix_english_spacing as toolkit_fix_english_spacing,
        detect_pdf_quality as toolkit_detect_pdf_quality,
        GlossaryManager,
        StatsCollector,
        auto_preprocess,
    )
    from paddleocr_toolkit.core import (
        OCRResult as ToolkitOCRResult,
        PDFGenerator as ToolkitPDFGenerator,
        OCRMode as ToolkitOCRMode,
    )
    HAS_TOOLKIT = True
except ImportError:
    HAS_TOOLKIT = False

# 設定日誌
def setup_logging(log_file: Optional[str] = None):
    """設定日誌記錄"""
    if log_file is None:
        log_file = Path(__file__).parent / f"paddle_ocr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # 移除現有的所有 handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # 創建檔案 handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='w')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    
    # 創建控制台 handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    
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
    from PIL import Image
    import numpy as np
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
        OllamaTranslator,
        TextInpainter,
        TextRenderer,
        TranslatedBlock,
        MonolingualPDFGenerator,
        BilingualPDFGenerator
    )
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False
    logging.warning("翻譯模組 (pdf_translator) 未安裝，翻譯功能不可用")


# OCR 模式枚舉
class OCRMode(Enum):
    BASIC = "basic"           # PP-OCRv5 基本文字識別
    STRUCTURE = "structure"   # PP-StructureV3 結構化文件解析
    VL = "vl"                 # PaddleOCR-VL 視覺語言模型
    FORMULA = "formula"       # PP-FormulaNet 公式識別
    HYBRID = "hybrid"         # 混合模式：版面分析 + 精確 OCR


# 支援的檔案格式
SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
SUPPORTED_PDF_FORMAT = '.pdf'


def fix_english_spacing(text: str, use_wordninja: bool = True) -> str:
    """
    修復英文 OCR 結果中的空格問題
    
    策略：
    1. 保護專業術語不被拆分
    2. CamelCase 分詞：FoundryService → Foundry Service
    3. wordninja 智能分詞（可選）：aprogramoffered → a program offered
    4. 修復連字符詞：wellestablished → well-established
    5. 數字前後空格：Dec.1992and → Dec. 1992 and
    
    Args:
        text: 輸入文字
        use_wordninja: 是否使用 wordninja 智能分詞（預設開啟）
    """
    import re
    
    if not text:
        return text
    
    result = text
    
    # ========== 0. 首先合併被 OCR 錯誤分詞的術語 ==========
    # OCR 可能會把 PolyMUMPs 識別為 Poly MUMPs
    MERGE_TERMS = {
        'Poly MUMPs': 'PolyMUMPs',
        'Poly MUMPS': 'PolyMUMPs',
        'SOIMUMP s': 'SOIMUMPs',
        'SOI MUMPs': 'SOIMUMPs',
        'Metal MUMPs': 'MetalMUMPs',
        # MEMScAP 各種錯誤識別
        'MEMS cAP': 'MEMScAP',
        'MEMSc AP': 'MEMScAP',
        'MEMSC AP': 'MEMScAP',
        'MEMSc ap': 'MEMScAP',
        # MEMS Processes（保留空格）
        'MEMSProcesses': 'MEMS Processes',
        'MEMSprocesses': 'MEMS processes',
        # 符號空格修復
        '2025©': '2025 ©',
        '2024©': '2024 ©',
        '2023©': '2023 ©',
        '©Chiu': '© Chiu',
        # 逗號後加空格
        ',Yi': ', Yi',
        ',Fall': ', Fall',
        'Fall,2': 'Fall, 2',  # Fall,2025 → Fall, 2025
        # 數字後黏連修復
        '81runs': '81 runs',
        '82runs': '82 runs',
        '9thrun': '9th run',
        # 常見黏連詞
        'micromachiningby': 'micromachining by',
        'micromachiningfor': 'micromachining for',
        # 版本號 OCR 錯誤修正（1 被丟失）
        '.v0.pdf': '.v10.pdf',
        '.v0.doc': '.v10.doc',
        '_v0.pdf': '_v10.pdf',
        '_v0.doc': '_v10.doc',
        'dr.v0': 'dr.v10',
    }
    for wrong, correct in MERGE_TERMS.items():
        result = result.replace(wrong, correct)
    
    # 保護不應該被拆分的專業術語
    PROTECTED_TERMS = {
        # MEMS 相關術語（不應被拆分）
        'MUMPs', 'PolyMUMPs', 'SOIMUMPs', 'MetalMUMPs',
        'MEMScAP', 'MEMSCAP', 'MEMSProcesses', 'MEMSdevices',
        'micromachining', 'Micromachining', 'MICROMACHINING',
        'FoundryService', 'CMOS', 'MEMS', 'OCR', 'PDF',
        # 科技術語
        'PaddleOCR', 'PowerPoint', 'JavaScript', 'TypeScript',
        'GitHub', 'LinkedIn', 'YouTube', 'Facebook',
        'iPhone', 'iPad', 'macOS', 'iOS', 'WiFi',
        # 常見縮寫
        'TM', 'PhD', 'CEO', 'CTO', 'CFO',
        # 序數後綴（不應在數字和 th/st/nd/rd 之間加空格）
        '0th', '1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th',
        '10th', '11th', '12th', '13th', '14th', '15th', '16th', '17th', '18th', '19th',
        '20th', '21st', '22nd', '23rd', '24th', '25th', '30th', '40th', '50th',
        # 版本號
        'v0', 'v1', 'v2', 'v3', 'v4', 'v5', 'v6', 'v7', 'v8', 'v9', 'v10',
    }
    
    # 先用佔位符保護這些詞
    protected_map = {}
    for i, term in enumerate(PROTECTED_TERMS):
        if term in result:
            placeholder = f"__PROT_{i}__"
            protected_map[placeholder] = term
            result = result.replace(term, placeholder)
    
    # 1. CamelCase 分詞（小寫後接大寫）
    # 例如：FoundryService → Foundry Service
    result = re.sub(r'([a-z])([A-Z])', r'\1 \2', result)
    
    # 1.1 修復小寫後接佔位符（例如 byMEMScAP → by MEMScAP）
    result = re.sub(r'([a-z])(__PROT_)', r'\1 \2', result)
    
    # 2. 大寫字母序列後接小寫（例如 CMOSMems → CMOS Mems）
    result = re.sub(r'([A-Z]{2,})([A-Z][a-z])', r'\1 \2', result)
    
    # 3. 修復數字和字母之間缺少空格
    # 但排除版本號（v10）和序數（9th）
    result = re.sub(r'(\d)([a-zA-Z])', lambda m: m.group(0) if m.group(2).lower() in ['t','s','n','r','v'] else m.group(1) + ' ' + m.group(2), result)
    # 小寫後接數字（但排除 v + 數字）
    result = re.sub(r'([a-uw-z])(\d)', r'\1 \2', result)  # 排除 v
    
    # 4. 修復標點符號後缺少空格
    result = re.sub(r'\.(\d)', r'. \1', result)  # 句號後接數字
    result = re.sub(r'\.([A-Z])', r'. \1', result)  # 句號後接大寫
    result = re.sub(r',([A-Za-z])', r', \1', result)  # 逗號後接字母
    
    # 5. 修復括號前後空格
    result = re.sub(r'([a-zA-Z])\(', r'\1 (', result)
    result = re.sub(r'\)([a-zA-Z])', r') \1', result)
    
    # 5.1 修復常見的黏連詞
    # Aprogramoffered → A program offered
    common_splits = {
        'Aprogram': 'A program',
        'aprogram': 'a program',
        'Theprogram': 'The program',
        'theprogram': 'the program',
        'programoffered': 'program offered',
        'isdesigned': 'is designed',
        'wasestablished': 'was established',
        'hasbeen': 'has been',
        'canbe': 'can be',
        'willbe': 'will be',
        'tobe': 'to be',
        'forthe': 'for the',
        'tothe': 'to the',
        'ofthe': 'of the',
        'inthe': 'in the',
        'onthe': 'on the',
        'bythe': 'by the',
        'andthe': 'and the',
        'isthe': 'is the',
        'asthe': 'as the',
        'withthe': 'with the',
        # 新增
        'Designof': 'Design of',
        'designof': 'design of',
        'micromachiningby': 'micromachining by',
        'isused': 'is used',
        'areused': 'are used',
        'canbeused': 'can be used',
        'providescustomers': 'provides customers',
        'includesthe': 'includes the',
        'suchas': 'such as',
        'aswellas': 'as well as',
        'inorder': 'in order',
        'orderto': 'order to',
        'dueto': 'due to',
        'byvarious': 'by various',
        'forvarious': 'for various',
        'withcost': 'with cost',
        'tofabricate': 'to fabricate',
        'todesign': 'to design',
        'toannounce': 'to announce',
    }
    for wrong, correct in common_splits.items():
        result = result.replace(wrong, correct)
    
    # 6. 修復常見的連字符詞
    common_hyphenated = {
        'wellestablished': 'well-established',
        'costeffective': 'cost-effective',
        'highperformance': 'high-performance',
        'lowpower': 'low-power',
        'stateoftheart': 'state-of-the-art',
        'realtime': 'real-time',
        'onchip': 'on-chip',
        'offchip': 'off-chip',
        'multiuser': 'multi-user',
        'Multi User': 'Multi-User',
        'waferlevel': 'wafer-level',
        'Wafer Level': 'Wafer-Level',
    }
    for wrong, correct in common_hyphenated.items():
        result = re.sub(wrong, correct, result, flags=re.IGNORECASE)
    
    # 7. wordninja 智能分詞（處理長連字）
    if use_wordninja and HAS_WORDNINJA:
        # 找出長度超過閾值的連續小寫單詞並嘗試分詞
        def split_long_words(match):
            word = match.group(0)
            if len(word) > 10:  # 只處理長單詞
                # 使用 wordninja 分詞
                parts = wordninja.split(word.lower())
                if len(parts) > 1:
                    # 保持首字母大小寫
                    if word[0].isupper():
                        parts[0] = parts[0].capitalize()
                    return ' '.join(parts)
            return word
        
        # 匹配沒有空格的長單詞
        result = re.sub(r'\b[A-Za-z]{11,}\b', split_long_words, result)
    
    # 恢復被保護的專業術語
    for placeholder, term in protected_map.items():
        result = result.replace(placeholder, term)
    
    # 8. 清理多餘空格
    result = re.sub(r' +', ' ', result)
    
    return result


def detect_pdf_quality(pdf_path: str) -> dict:
    """
    偵測 PDF 品質，判斷是否為掃描件或模糊文件
    
    Returns:
        dict: {
            'is_scanned': bool,      # 是否為掃描件
            'is_blurry': bool,       # 是否模糊
            'has_text': bool,        # 是否有可提取的文字
            'recommended_dpi': int,  # 建議的 DPI
            'reason': str            # 判斷原因
        }
    """
    try:
        import fitz
        
        result = {
            'is_scanned': False,
            'is_blurry': False,
            'has_text': False,
            'recommended_dpi': 150,
            'reason': ''
        }
        
        pdf_doc = fitz.open(pdf_path)
        
        if len(pdf_doc) == 0:
            result['reason'] = 'PDF 無頁面'
            pdf_doc.close()
            return result
        
        # 只檢查前幾頁
        pages_to_check = min(3, len(pdf_doc))
        total_text_length = 0
        total_images = 0
        
        for page_num in range(pages_to_check):
            page = pdf_doc[page_num]
            
            # 檢查可提取的文字
            text = page.get_text("text")
            total_text_length += len(text.strip())
            
            # 檢查圖片數量
            images = page.get_images()
            total_images += len(images)
        
        pdf_doc.close()
        
        # 判斷邏輯
        avg_text_per_page = total_text_length / pages_to_check
        avg_images_per_page = total_images / pages_to_check
        
        # 如果幾乎沒有可提取文字但有圖片，很可能是掃描件
        if avg_text_per_page < 50 and avg_images_per_page >= 1:
            result['is_scanned'] = True
            result['recommended_dpi'] = 300
            result['reason'] = f'偵測為掃描件（平均每頁 {avg_text_per_page:.0f} 字元，{avg_images_per_page:.1f} 張圖片）'
        
        # 如果有少量文字，可能是部分掃描
        elif avg_text_per_page < 200 and avg_images_per_page >= 1:
            result['is_scanned'] = True
            result['is_blurry'] = True
            result['recommended_dpi'] = 200
            result['reason'] = f'偵測為部分掃描文件（平均每頁 {avg_text_per_page:.0f} 字元）'
        
        # 有足夠文字，是一般 PDF
        else:
            result['has_text'] = True
            result['recommended_dpi'] = 150
            result['reason'] = f'偵測為一般 PDF（平均每頁 {avg_text_per_page:.0f} 字元）'
        
        return result
        
    except Exception as e:
        logging.warning(f"PDF 品質偵測失敗: {e}")
        return {
            'is_scanned': False,
            'is_blurry': False,
            'has_text': False,
            'recommended_dpi': 150,
            'reason': f'偵測失敗: {e}'
        }


@dataclass
class OCRResult:
    """OCR 辨識結果資料結構"""
    text: str                    # 辨識的文字
    confidence: float            # 信賴度 (0-1)
    bbox: List[List[float]]      # 邊界框座標 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    
    @property
    def x(self) -> float:
        """左上角 X 座標"""
        return min(p[0] for p in self.bbox)
    
    @property
    def y(self) -> float:
        """左上角 Y 座標"""
        return min(p[1] for p in self.bbox)
    
    @property
    def width(self) -> float:
        """邊界框寬度"""
        xs = [p[0] for p in self.bbox]
        return max(xs) - min(xs)
    
    @property
    def height(self) -> float:
        """邊界框高度"""
        ys = [p[1] for p in self.bbox]
        return max(ys) - min(ys)


class PDFGenerator:
    """
    PDF 生成器 - 使用 Umi-OCR 邏輯建立雙層可搜尋 PDF
    
    透過 PyMuPDF 在原始圖片上疊加透明文字層，
    使 PDF 可搜尋、可選取文字，同時保持原始視覺外觀。
    """
    
    def __init__(self, output_path: str, debug_mode: bool = False, compress_images: bool = False, jpeg_quality: int = 85):
        """
        初始化 PDF 生成器
        
        Args:
            output_path: 輸出 PDF 的檔案路徑
            debug_mode: 如果為 True，文字會顯示為粉紅色（方便調試）
            compress_images: 如果為 True，使用 JPEG 壓縮圖片以減少檔案大小
            jpeg_quality: JPEG 壓縮品質（0-100，預設 85）
        """
        self.output_path = output_path
        self.doc = fitz.open()  # 建立新的空白 PDF
        self.page_count = 0
        self.debug_mode = debug_mode
        self.compress_images = compress_images
        self.jpeg_quality = max(0, min(100, jpeg_quality))  # 確保在 0-100 範圍內
    
    def add_page(self, image_path: str, ocr_results: List[OCRResult]) -> bool:
        """
        新增一頁到 PDF
        
        Args:
            image_path: 原始圖片路徑
            ocr_results: OCR 辨識結果列表
            
        Returns:
            bool: 是否成功新增頁面
        """
        try:
            # 開啟圖片以取得尺寸
            img = Image.open(image_path)
            img_width, img_height = img.size
            
            # 建立新頁面，尺寸與圖片相同
            page = self.doc.new_page(
                width=img_width,
                height=img_height
            )
            
            # 插入圖片作為背景
            rect = fitz.Rect(0, 0, img_width, img_height)
            
            if self.compress_images:
                # 使用 JPEG 壓縮以減少檔案大小
                import io
                # 確保是 RGB 模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                # 儲存為 JPEG 到記憶體緩衝區
                jpeg_buffer = io.BytesIO()
                img.save(jpeg_buffer, format="JPEG", quality=self.jpeg_quality, optimize=True)
                jpeg_data = jpeg_buffer.getvalue()
                # 插入 JPEG 資料
                page.insert_image(rect, stream=jpeg_data)
            else:
                # 直接插入原始圖片（PNG 格式，無損但較大）
                page.insert_image(rect, filename=image_path)
            
            # 疊加透明文字層
            for result in ocr_results:
                self._insert_invisible_text(page, result)
            
            self.page_count += 1
            return True
            
        except Exception as e:
            print(f"警告：新增頁面失敗 ({image_path}): {e}")
            return False
    
    def add_page_from_pixmap(self, pixmap: fitz.Pixmap, ocr_results: List[OCRResult]) -> bool:
        """
        從 PyMuPDF Pixmap 新增一頁到 PDF
        
        Args:
            pixmap: PyMuPDF 的 Pixmap 物件
            ocr_results: OCR 辨識結果列表
            
        Returns:
            bool: 是否成功新增頁面
        """
        try:
            img_width = pixmap.width
            img_height = pixmap.height
            
            # 建立新頁面
            page = self.doc.new_page(
                width=img_width,
                height=img_height
            )
            
            # 插入圖片作為背景
            rect = fitz.Rect(0, 0, img_width, img_height)
            
            if self.compress_images:
                # 使用 JPEG 壓縮以減少檔案大小
                import io
                # 將 pixmap 轉換為 PIL Image
                pil_image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                # 儲存為 JPEG 到記憶體緩衝區
                jpeg_buffer = io.BytesIO()
                pil_image.save(jpeg_buffer, format="JPEG", quality=self.jpeg_quality, optimize=True)
                jpeg_data = jpeg_buffer.getvalue()
                # 插入 JPEG 資料
                page.insert_image(rect, stream=jpeg_data)
            else:
                # 直接插入 pixmap（PNG 格式，無損但較大）
                page.insert_image(rect, pixmap=pixmap)
            
            # 疊加透明文字層
            for result in ocr_results:
                self._insert_invisible_text(page, result)
            
            self.page_count += 1
            return True
            
        except Exception as e:
            print(f"警告：新增頁面失敗: {e}")
            return False
    
    def _insert_invisible_text(self, page: fitz.Page, result: OCRResult) -> None:
        """
        在頁面上插入透明文字
        
        使用 PDF 渲染模式 3（隱形）來確保文字不可見但可選取/搜尋
        
        智能字體大小計算：根據 bbox 寬度和高度來精確匹配原始文字
        
        Args:
            page: PyMuPDF 頁面物件
            result: OCR 辨識結果
        """
        if not result.text.strip():
            return
        
        try:
            # 計算文字區域
            x = result.x
            y = result.y
            width = result.width
            height = result.height
            text = result.text
            
            # 選擇最佳字體
            fonts_to_try = ["helv", "china-s", "cour"]
            best_font = "helv"
            best_font_size = height * 0.6  # 預設值
            
            for fontname in fonts_to_try:
                try:
                    # 智能字體大小計算：根據 bbox 寬度和高度
                    # 方法：計算一個初始字體大小，然後調整使文字寬度接近 bbox 寬度
                    
                    # 先用高度估算初始字體大小
                    initial_size = height * 0.7
                    if initial_size < 4:
                        initial_size = 4
                    if initial_size > 100:
                        initial_size = 100
                    
                    # 計算文字在此字體大小下的寬度
                    text_width = fitz.get_text_length(text, fontname=fontname, fontsize=initial_size)
                    
                    if text_width > 0 and width > 0:
                        # 計算寬度比例並調整字體大小
                        width_ratio = width / text_width
                        
                        # 調整字體大小使文字寬度接近 bbox 寬度
                        adjusted_size = initial_size * width_ratio
                        
                        # 但也不能太大（不能超過高度的 90%）
                        max_by_height = height * 0.9
                        if adjusted_size > max_by_height:
                            adjusted_size = max_by_height
                        
                        # 限制字體大小範圍
                        if adjusted_size < 4:
                            adjusted_size = 4
                        if adjusted_size > 100:
                            adjusted_size = 100
                        
                        best_font = fontname
                        best_font_size = adjusted_size
                        break  # 找到合適的字體就停止
                    else:
                        # 無法計算，使用預設值
                        best_font = fontname
                        best_font_size = initial_size
                        break
                        
                except Exception:
                    continue
            
            # 計算文字基線位置
            # 文字基線約在 bbox 底部往上 (1 - font_size/height) 的位置
            baseline_offset = best_font_size * 0.2  # 基線下方的空間約為字體大小的 20%
            baseline_y = y + height - baseline_offset
            
            # 確保基線在合理範圍內
            if baseline_y < y + best_font_size * 0.8:
                baseline_y = y + best_font_size * 0.8
            if baseline_y > y + height:
                baseline_y = y + height
            # 根據 debug_mode 設定文字樣式
            if self.debug_mode:
                render_mode = 0  # 可見模式
                text_color = (1, 0.4, 0.6)  # 粉紅色
            else:
                render_mode = 3  # 隱形模式（可搜尋但不可見）
                text_color = (0, 0, 0)  # 黑色
            
            # 插入文字
            try:
                page.insert_text(
                    fitz.Point(x, baseline_y),
                    text,
                    fontsize=best_font_size,
                    fontname=best_font,
                    render_mode=render_mode,
                    color=text_color
                )
            except Exception as e:
                # 如果失敗，嘗試其他字體
                for fontname in fonts_to_try:
                    if fontname != best_font:
                        try:
                            page.insert_text(
                                fitz.Point(x, baseline_y),
                                text,
                                fontsize=best_font_size,
                                fontname=fontname,
                                render_mode=render_mode,
                                color=text_color
                            )
                            return
                        except:
                            continue
                logging.warning(f"無法插入文字 '{text[:30]}...': {e}")
            
        except Exception as e:
            logging.warning(f"插入文字失敗 '{result.text[:30]}...': {e}")
    
    def save(self) -> bool:
        """
        儲存 PDF 檔案
        
        Returns:
            bool: 是否成功儲存
        """
        try:
            if self.page_count == 0:
                print("警告：沒有頁面可儲存")
                return False
            
            self.doc.save(self.output_path)
            self.doc.close()
            print(f"[OK] PDF 已儲存：{self.output_path} ({self.page_count} 頁)")
            return True
            
        except Exception as e:
            print(f"錯誤：儲存 PDF 失敗: {e}")
            return False


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
        jpeg_quality: int = 85
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
        
        # 初始化對應的 OCR 引擎
        print(f"正在初始化 PaddleOCR 3.x (模式: {mode})...")
        if debug_mode:
            print("[DEBUG] 已啟用 DEBUG 模式：可搜尋 PDF 的隱形文字將顯示為粉紅色")
        
        try:
            if mode == "structure":
                if not HAS_STRUCTURE:
                    raise ImportError("PPStructureV3 模組不可用，請確認 paddleocr 版本")
                self.ocr = PPStructureV3(
                    use_doc_orientation_classify=use_orientation_classify,
                    use_doc_unwarping=use_doc_unwarping,
                    use_textline_orientation=use_textline_orientation,
                    device=device
                )
                print("[OK] PP-StructureV3 初始化完成（結構化文件解析模式）")
                
            elif mode == "vl":
                if not HAS_VL:
                    raise ImportError("PaddleOCRVL 模組不可用，請確認 paddleocr 版本")
                self.ocr = PaddleOCRVL(
                    use_doc_orientation_classify=use_orientation_classify,
                    use_doc_unwarping=use_doc_unwarping
                )
                print("[OK] PaddleOCR-VL 初始化完成（視覺語言模型模式）")
                
            elif mode == "formula":
                if not HAS_FORMULA:
                    raise ImportError("FormulaRecPipeline 模組不可用，請確認 paddleocr 版本")
                self.ocr = FormulaRecPipeline(
                    use_doc_orientation_classify=use_orientation_classify,
                    use_doc_unwarping=use_doc_unwarping,
                    device=device
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
                    device=device
                )
                
                # 設定 self.ocr 為 structure_engine 以便其他方法使用
                self.ocr = self.structure_engine
                print("[OK] Hybrid 模式初始化完成（PP-StructureV3 版面分析 + OCR）")
                
            else:  # basic 模式
                self.ocr = PaddleOCR(
                    use_doc_orientation_classify=use_orientation_classify,
                    use_doc_unwarping=use_doc_unwarping,
                    use_textline_orientation=use_textline_orientation
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
        results = []
        
        try:
            # PaddleOCR 3.x 回傳結果是一個列表，每個元素代表一個輸入
            for res in predict_result:
                # 取得 OCR 結果
                # 新版 API 的結果結構：res['rec_texts'], res['rec_scores'], res['dt_polys']
                if hasattr(res, 'rec_texts'):
                    texts = res.rec_texts if hasattr(res, 'rec_texts') else []
                    scores = res.rec_scores if hasattr(res, 'rec_scores') else []
                    polys = res.dt_polys if hasattr(res, 'dt_polys') else []
                    
                    for i, (text, score, poly) in enumerate(zip(texts, scores, polys)):
                        # 將 polygon 轉換為 bbox 格式
                        bbox = poly.tolist() if hasattr(poly, 'tolist') else list(poly)
                        results.append(OCRResult(
                            text=str(text),
                            confidence=float(score),
                            bbox=bbox
                        ))
                elif hasattr(res, '__getitem__'):
                    # 嘗試透過字典方式存取
                    texts = res.get('rec_texts', []) if isinstance(res, dict) else []
                    scores = res.get('rec_scores', []) if isinstance(res, dict) else []
                    polys = res.get('dt_polys', []) if isinstance(res, dict) else []
                    
                    for text, score, poly in zip(texts, scores, polys):
                        bbox = poly.tolist() if hasattr(poly, 'tolist') else list(poly)
                        results.append(OCRResult(
                            text=str(text),
                            confidence=float(score),
                            bbox=bbox
                        ))
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
        
        try:
            # PaddleOCR 3.x 使用 predict() 方法
            predict_result = self.ocr.predict(input=image_path)
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
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
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
    
    def process_structured(
        self,
        input_path: str,
        markdown_output: Optional[str] = None,
        json_output: Optional[str] = None,
        excel_output: Optional[str] = None,
        html_output: Optional[str] = None
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
            raise ValueError(f"process_structured 僅適用於 structure 或 vl 模式，當前模式: {self.mode}")
        
        result_summary = {
            "input": input_path,
            "mode": self.mode,
            "pages_processed": 0,
            "markdown_files": [],
            "json_files": [],
            "excel_files": [],
            "html_files": []
        }
        
        try:
            print(f"正在處理: {input_path}")
            
            # 使用 predict() 方法處理
            output = self.ocr.predict(input=input_path)
            
            # 取得腳本所在目錄作為預設輸出目錄
            script_dir = Path(__file__).parent.resolve()
            
            # 處理輸出路徑
            if markdown_output:
                md_path = Path(markdown_output)
                if not md_path.is_absolute():
                    md_path = script_dir / md_path
                md_output_dir = md_path.parent
                md_output_dir.mkdir(parents=True, exist_ok=True)
            
            if json_output:
                json_path = Path(json_output)
                if not json_path.is_absolute():
                    json_path = script_dir / json_path
                json_output_dir = json_path.parent
                json_output_dir.mkdir(parents=True, exist_ok=True)
            
            # 處理每個結果
            page_count = 0
            all_markdown_content = []
            
            for res in output:
                page_count += 1
                
                # 使用內建的儲存方法
                if markdown_output:
                    # 建立臨時目錄來收集 markdown
                    temp_dir = tempfile.mkdtemp()
                    try:
                        res.save_to_markdown(save_path=temp_dir)
                        # 收集生成的 markdown 內容
                        for md_file in Path(temp_dir).glob("*.md"):
                            with open(md_file, 'r', encoding='utf-8') as f:
                                all_markdown_content.append(f"<!-- Page {page_count} -->\n" + f.read())
                    finally:
                        shutil.rmtree(temp_dir, ignore_errors=True)
                
                if json_output:
                    temp_dir = tempfile.mkdtemp()
                    try:
                        res.save_to_json(save_path=temp_dir)
                        # 複製生成的 JSON 到目標位置
                        for json_file in Path(temp_dir).glob("*.json"):
                            target_json = json_path.parent / f"{json_path.stem}_page{page_count}.json"
                            shutil.copy(json_file, target_json)
                            result_summary["json_files"].append(str(target_json))
                    finally:
                        shutil.rmtree(temp_dir, ignore_errors=True)
                
                # 輸出 Excel（表格）
                if excel_output:
                    if not HAS_OPENPYXL:
                        print("警告：需要安裝 openpyxl: pip install openpyxl")
                    else:
                        temp_dir = tempfile.mkdtemp()
                        try:
                            # 嘗試呼叫 save_to_xlsx（如果結果物件支援）
                            if hasattr(res, 'save_to_xlsx'):
                                res.save_to_xlsx(save_path=temp_dir)
                                # 複製生成的 Excel 到目標位置
                                excel_path = Path(excel_output)
                                for xlsx_file in Path(temp_dir).glob("*.xlsx"):
                                    if excel_path.suffix == '.xlsx':
                                        target_xlsx = excel_path.parent / f"{excel_path.stem}_page{page_count}.xlsx"
                                    else:
                                        target_xlsx = Path(excel_output) / f"{Path(input_path).stem}_page{page_count}.xlsx"
                                    shutil.copy(xlsx_file, target_xlsx)
                                    result_summary["excel_files"].append(str(target_xlsx))
                        except Exception as excel_err:
                            logging.warning(f"Excel 輸出失敗 (頁 {page_count}): {excel_err}")
                        finally:
                            shutil.rmtree(temp_dir, ignore_errors=True)
                
                # 輸出 HTML
                if html_output:
                    temp_dir = tempfile.mkdtemp()
                    try:
                        # 嘗試呼叫 save_to_html（如果結果物件支援）
                        if hasattr(res, 'save_to_html'):
                            res.save_to_html(save_path=temp_dir)
                            # 複製生成的 HTML 到目標位置
                            html_path = Path(html_output)
                            if not html_path.is_absolute():
                                html_path = script_dir / html_path
                            for html_file in Path(temp_dir).glob("*.html"):
                                if html_path.suffix == '.html':
                                    target_html = html_path.parent / f"{html_path.stem}_page{page_count}.html"
                                else:
                                    html_path.mkdir(parents=True, exist_ok=True)
                                    target_html = html_path / f"{Path(input_path).stem}_page{page_count}.html"
                                shutil.copy(html_file, target_html)
                                result_summary["html_files"].append(str(target_html))
                        else:
                            logging.warning(f"結果物件不支援 save_to_html 方法")
                    except Exception as html_err:
                        logging.warning(f"HTML 輸出失敗 (頁 {page_count}): {html_err}")
                    finally:
                        shutil.rmtree(temp_dir, ignore_errors=True)
            
            # 合併所有 markdown 內容到單一檔案
            if markdown_output and all_markdown_content:
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write("\n\n---\n\n".join(all_markdown_content))
                result_summary["markdown_files"].append(str(md_path))
                print(f"[OK] Markdown 已儲存：{md_path}")
            
            # Excel 輸出完成訊息
            if result_summary.get("excel_files"):
                print(f"[OK] Excel 已儲存：{len(result_summary['excel_files'])} 個檔案")
            
            # HTML 輸出完成訊息
            if result_summary.get("html_files"):
                print(f"[OK] HTML 已儲存：{len(result_summary['html_files'])} 個檔案")
            
            result_summary["pages_processed"] = page_count
            print(f"[OK] 處理完成：{page_count} 頁")
            
            return result_summary
            
        except Exception as e:
            print(f"錯誤：處理失敗 ({input_path}): {e}")
            result_summary["error"] = str(e)
            return result_summary
    
    def process_pdf(
        self,
        pdf_path: str,
        output_path: Optional[str] = None,
        searchable: bool = False,
        dpi: int = 200,
        show_progress: bool = True
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
        all_results = []
        
        try:
            # 開啟 PDF
            logging.info(f"開啟 PDF: {pdf_path}")
            pdf_doc = fitz.open(pdf_path)
            total_pages = len(pdf_doc)
            logging.info(f"PDF 共 {total_pages} 頁")
            print(f"正在處理 PDF: {pdf_path} ({total_pages} 頁)")
            
            # 準備 PDF 生成器（如果需要生成可搜尋 PDF）
            pdf_generator = None
            if searchable:
                if not output_path:
                    base_name = Path(pdf_path).stem
                    output_path = str(Path(pdf_path).parent / f"{base_name}_searchable.pdf")
                logging.info(f"準備生成可搜尋 PDF: {output_path}")
                pdf_generator = PDFGenerator(output_path, debug_mode=self.debug_mode)
            
            # 處理每一頁（使用進度條）
            page_iterator = range(total_pages)
            if show_progress and HAS_TQDM:
                page_iterator = tqdm(
                    page_iterator,
                    desc="OCR 處理中",
                    unit="頁",
                    ncols=80
                )
            
            for page_num in page_iterator:
                try:
                    logging.info(f"開始處理第 {page_num + 1}/{total_pages} 頁")
                    if not (show_progress and HAS_TQDM):
                        print(f"  處理第 {page_num + 1}/{total_pages} 頁...")
                    
                    page = pdf_doc[page_num]
                    
                    # 將頁面轉換為圖片
                    logging.info(f"  轉換第 {page_num + 1} 頁為圖片 (DPI: {dpi})")
                    zoom = dpi / 72.0
                    matrix = fitz.Matrix(zoom, zoom)
                    pixmap = page.get_pixmap(matrix=matrix)
                    logging.info(f"  圖片尺寸: {pixmap.width}x{pixmap.height}, 色彩通道: {pixmap.n}")
                    
                    # 轉換為 numpy 陣列以供 PaddleOCR 使用
                    img_array = np.frombuffer(pixmap.samples, dtype=np.uint8)
                    img_array = img_array.reshape(pixmap.height, pixmap.width, pixmap.n)
                    
                    # 如果是 RGBA，轉換為 RGB
                    if pixmap.n == 4:
                        img_array = img_array[:, :, :3]
                        logging.info(f"  已轉換 RGBA 為 RGB")
                    
                    # 執行 OCR
                    logging.info(f"  執行 OCR...")
                    page_results = self.process_image_array(img_array)
                    logging.info(f"  第 {page_num + 1} 頁辨識到 {len(page_results)} 個文字區塊")
                    all_results.append(page_results)
                    
                    # 將座標縮放回原始 PDF 尺寸
                    scale_factor = 72.0 / dpi
                    for result in page_results:
                        result.bbox = [[p[0] * scale_factor, p[1] * scale_factor] for p in result.bbox]
                    
                    # 如果需要生成可搜尋 PDF
                    if pdf_generator:
                        logging.info(f"  新增第 {page_num + 1} 頁到可搜尋 PDF")
                        # 使用原始頁面尺寸
                        original_pixmap = page.get_pixmap()
                        pdf_generator.add_page_from_pixmap(original_pixmap, page_results)
                        # 清理 pixmap
                        del original_pixmap
                    
                    # 清理本頁使用的資源
                    del pixmap
                    del img_array
                    del page_results
                    gc.collect()  # 強制垃圾回收，防止記憶體洩漏
                    
                    logging.info(f"[OK] 第 {page_num + 1}/{total_pages} 頁處理完成")
                    
                except Exception as page_error:
                    error_msg = f"處理第 {page_num + 1} 頁時發生錯誤: {str(page_error)}"
                    logging.error(error_msg)
                    logging.error(traceback.format_exc())
                    print(f"  [WARN] {error_msg}")
                    # 清理資源後繼續處理下一頁
                    gc.collect()
                    all_results.append([])
            
            pdf_doc.close()
            logging.info("PDF 文件已關閉")
            
            # 儲存可搜尋 PDF
            if pdf_generator:
                logging.info("開始儲存可搜尋 PDF")
                pdf_generator.save()
            
            logging.info(f"[OK] 完成處理 {total_pages} 頁，成功 {len([r for r in all_results if r])} 頁")
            return all_results, output_path
            
        except Exception as e:
            error_msg = f"處理 PDF 失敗 ({pdf_path}): {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            print(f"錯誤：{error_msg}")
            return all_results, None
    
    def process_directory(
        self,
        dir_path: str,
        output_path: Optional[str] = None,
        searchable: bool = False,
        recursive: bool = False
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
        return separator.join(r.text for r in results if r.text.strip())
    
    def process_formula(
        self,
        input_path: str,
        latex_output: Optional[str] = None
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
            "error": None
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
                if hasattr(res, 'rec_formula'):
                    latex = res.rec_formula
                # 方式 2：字典存取
                elif isinstance(res, dict):
                    latex = res.get('rec_formula') or res.get('formula') or res.get('latex')
                # 方式 3：結果物件的其他屬性
                elif hasattr(res, '__dict__'):
                    for key in ['rec_formula', 'formula', 'latex', 'result']:
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
                with open(latex_output, 'w', encoding='utf-8') as f:
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
        translate_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        混合模式：使用 PP-StructureV3 版面分析 + PP-OCRv5 精確座標
        
        生成閱讀順序正確的可搜尋 PDF 和 Markdown/JSON/HTML
        
        Args:
            input_path: 輸入檔案路徑（PDF 或圖片）
            output_path: 可搜尋 PDF 輸出路徑（可選）
            markdown_output: Markdown 輸出路徑（可選）
            json_output: JSON 輸出路徑（可選）
            html_output: HTML 輸出路徑（可選）
            dpi: PDF 轉圖片解析度
            show_progress: 是否顯示進度條
            translate_config: 翻譯配置（可選），傳入後會在生成可搜尋 PDF 後自動執行翻譯
            
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
            "error": None
        }
        
        input_path_obj = Path(input_path)
        
        try:
            # 設定輸出路徑
            if not output_path:
                output_path = str(input_path_obj.parent / f"{input_path_obj.stem}_hybrid.pdf")
            
            if not markdown_output:
                markdown_output = str(input_path_obj.parent / f"{input_path_obj.stem}_hybrid.md")
            
            print(f"正在處理（混合模式）: {input_path}")
            logging.info(f"開始混合模式處理: {input_path}")
            
            # 判斷輸入類型
            if input_path_obj.suffix.lower() == '.pdf':
                # 自動偵測 PDF 品質並調整 DPI
                quality = detect_pdf_quality(input_path)
                print(f"[偵測] {quality['reason']}")
                if quality['is_scanned'] or quality['is_blurry']:
                    if quality['recommended_dpi'] > dpi:
                        dpi = quality['recommended_dpi']
                print(f"   使用 DPI: {dpi}")
                
                return self._process_hybrid_pdf(
                    input_path, output_path, markdown_output, json_output, html_output,
                    dpi, show_progress, result_summary,
                    translate_config=translate_config
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
        translate_config: Optional[Dict[str, Any]] = None
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
        
        pdf_doc = fitz.open(pdf_path)
        total_pages = len(pdf_doc)
        
        print(f"PDF 共 {total_pages} 頁")
        logging.info(f"PDF 共 {total_pages} 頁")
        
        # ========== 設定輸出路徑 ==========
        erased_output_path = output_path.replace('_hybrid.pdf', '_erased.pdf')
        
        # ========== 準備 PDF 生成器 ==========
        # 1. 原文可搜尋 PDF
        pdf_generator = PDFGenerator(
            output_path, 
            debug_mode=self.debug_mode,
            compress_images=self.compress_images,
            jpeg_quality=self.jpeg_quality
        )
        logging.info(f"[DEBUG] PDFGenerator compress_images={pdf_generator.compress_images}, jpeg_quality={pdf_generator.jpeg_quality}")
        # 2. 擦除版 PDF
        erased_generator = PDFGenerator(
            erased_output_path, 
            debug_mode=self.debug_mode,
            compress_images=self.compress_images,
            jpeg_quality=self.jpeg_quality
        )
        
        # 擦除器
        inpainter = TextInpainter() if HAS_TRANSLATOR else None
        
        all_markdown = []
        all_text = []
        all_ocr_results = []  # 收集每頁 OCR 結果，用於翻譯
        
        # 處理每一頁
        page_iterator = range(total_pages)
        if show_progress and HAS_TQDM:
            page_iterator = tqdm(page_iterator, desc="混合模式處理中", unit="頁", ncols=80)
        
        for page_num in page_iterator:
            try:
                logging.info(f"處理第 {page_num + 1}/{total_pages} 頁")
                
                page = pdf_doc[page_num]
                
                # 轉換為圖片
                zoom = dpi / 72.0
                matrix = fitz.Matrix(zoom, zoom)
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                
                # 轉換為 numpy 陣列
                img_array = np.frombuffer(pixmap.samples, dtype=np.uint8)
                img_array = img_array.reshape(pixmap.height, pixmap.width, pixmap.n)
                # pixmap.n 應該為 3 (RGB)，但保留檢查以防萬一
                if pixmap.n == 4:
                    img_array = img_array[:, :, :3]
                
                # 步驟 1：使用 Structure 引擎取得版面資訊和 Markdown
                logging.info(f"  執行版面分析...")
                structure_output = self.structure_engine.predict(input=img_array)
                
                # 直接從 PP-StructureV3 取得高精度 Markdown
                page_markdown = f"## 第 {page_num + 1} 頁\n\n"
                for res in structure_output:
                    # 使用 save_to_markdown 保存到臨時目錄
                    temp_md_dir = tempfile.mkdtemp()
                    try:
                        if hasattr(res, 'save_to_markdown'):
                            res.save_to_markdown(save_path=temp_md_dir)
                            # 讀取生成的 Markdown
                            for md_file in Path(temp_md_dir).glob("*.md"):
                                with open(md_file, 'r', encoding='utf-8') as f:
                                    page_markdown += f.read()
                                break
                    except Exception as md_err:
                        logging.warning(f"save_to_markdown 失敗: {md_err}")
                        # 回退：使用 markdown 屬性
                        if hasattr(res, 'markdown') and isinstance(res.markdown, str):
                            page_markdown += res.markdown
                    finally:
                        shutil.rmtree(temp_md_dir, ignore_errors=True)
                
                # 從 PP-StructureV3 輸出提取版面區塊資訊
                layout_blocks = []
                for res in structure_output:
                    try:
                        if hasattr(res, 'layout_parsing_result'):
                            # 嘗試從 layout_parsing_result 提取
                            lp_result = res.layout_parsing_result
                            if hasattr(lp_result, 'blocks'):
                                layout_blocks.extend(lp_result.blocks)
                        if hasattr(res, 'blocks'):
                            layout_blocks.extend(res.blocks)
                        elif isinstance(res, dict):
                            blocks = res.get('blocks', []) or res.get('layout_blocks', [])
                            if blocks:
                                layout_blocks.extend(blocks)
                    except Exception as block_err:
                        logging.debug(f"提取版面區塊失敗: {block_err}")
                
                logging.info(f"  取得 {len(layout_blocks)} 個版面區塊")
                
                # 步驟 2：從 PP-StructureV3 輸出提取文字座標，並使用 Markdown 過濾
                logging.info(f"  提取文字座標（使用 Markdown 匹配過濾）...")
                sorted_results = self._extract_ocr_from_structure(structure_output, markdown_text=page_markdown)
                logging.info(f"  _extract_ocr_from_structure 返回 {len(sorted_results)} 個結果")
                
                if sorted_results:
                    logging.info(f"  第一個結果: text='{sorted_results[0].text[:20] if sorted_results[0].text else ''}...', x={sorted_results[0].x}, y={sorted_results[0].y}")
                else:
                    logging.warning(f"  未提取到任何 OCR 結果!")
                
                # ========== 步驟 3：同時生成兩個 PDF ==========
                if sorted_results:
                    # 需要複製 img_array（因為後面會用到）
                    img_array_copy = img_array.copy()
                    
                    # 3.1 生成原文可搜尋 PDF（*_hybrid.pdf）
                    # 直接使用 pixmap，避免 I/O 開銷
                    pdf_generator.add_page_from_pixmap(pixmap, sorted_results)
                    
                    # 3.2 生成擦除版 PDF（*_erased.pdf）
                    if inpainter:
                        # 收集 bboxes
                        bboxes = [result.bbox for result in sorted_results if result.text and result.text.strip()]
                        
                        if bboxes:
                            # 在圖片上擦除文字區域
                            erased_image = inpainter.erase_multiple_regions(
                                img_array_copy, bboxes, fill_color=(255, 255, 255)
                            )
                        else:
                            erased_image = img_array_copy
                        
                        # 儲存擦除版圖片並添加到 erased_generator
                        tmp_erased_path = tempfile.mktemp(suffix='.png')
                        try:
                            Image.fromarray(erased_image).save(tmp_erased_path)
                            # 擦除版 PDF 也添加文字層（用於後續翻譯）
                            erased_generator.add_page(tmp_erased_path, sorted_results)
                        finally:
                            if os.path.exists(tmp_erased_path):
                                os.remove(tmp_erased_path)
                
                # 收集 Markdown、文字和 OCR 結果
                all_markdown.append(page_markdown)
                page_text = self.get_text(sorted_results)
                all_text.append(page_text)
                all_ocr_results.append(sorted_results)  # 收集 OCR 結果用於翻譯
                
                result_summary["pages_processed"] += 1
                
                # 清理記憶體
                del pixmap
                gc.collect()
                
            except Exception as page_error:
                logging.error(f"處理第 {page_num + 1} 頁時發生錯誤: {page_error}")
                logging.error(traceback.format_exc())
                continue
        
        pdf_doc.close()
        
        # 儲存可搜尋 PDF
        if pdf_generator.save():
            result_summary["searchable_pdf"] = output_path
            print(f"[OK] 可搜尋 PDF 已儲存：{output_path}")
        
        # 儲存擦除版 PDF
        if erased_generator.save():
            result_summary["erased_pdf"] = erased_output_path
            print(f"[OK] 擦除版 PDF 已儲存：{erased_output_path}")
        
        # 儲存 Markdown
        if markdown_output and all_markdown:
            # 應用英文空格修復
            fixed_markdown = [fix_english_spacing(md) for md in all_markdown]
            with open(markdown_output, 'w', encoding='utf-8') as f:
                f.write("\n\n---\n\n".join(fixed_markdown))
            result_summary["markdown_file"] = markdown_output
            print(f"[OK] Markdown 已儲存：{markdown_output}")
        
        # ========== JSON 輸出（如果啟用）==========
        if json_output:
            try:
                import json
                # 將 OCR 結果轉換為可序列化的格式
                json_data = {
                    "input": pdf_path,
                    "pages": []
                }
                for page_num, page_results in enumerate(all_ocr_results, 1):
                    page_data = {
                        "page": page_num,
                        "text_blocks": []
                    }
                    for result in page_results:
                        page_data["text_blocks"].append({
                            "text": result.text,
                            "confidence": result.confidence,
                            "bbox": [[float(p[0]), float(p[1])] for p in result.bbox]
                        })
                    json_data["pages"].append(page_data)
                
                with open(json_output, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                result_summary["json_file"] = json_output
                print(f"[OK] JSON 已儲存：{json_output}")
            except Exception as json_err:
                logging.warning(f"JSON 輸出失敗: {json_err}")
        
        # ========== HTML 輸出（如果啟用）==========
        if html_output:
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
                    lines = fixed_md.split('\n')
                    for line in lines:
                        if line.startswith('### '):
                            html_content += f"<h3>{line[4:]}</h3>\n"
                        elif line.startswith('## '):
                            html_content += f"<h2>{line[3:]}</h2>\n"
                        elif line.startswith('# '):
                            html_content += f"<h1>{line[2:]}</h1>\n"
                        elif line.startswith('- '):
                            html_content += f"<li>{line[2:]}</li>\n"
                        elif line.startswith('* '):
                            html_content += f"<li>{line[2:]}</li>\n"
                        elif line.strip() == '---':
                            html_content += "<hr>\n"
                        elif line.strip():
                            html_content += f"<p>{line}</p>\n"
                    html_content += "<hr>\n"
                
                html_content += """
</body>
</html>"""
                
                with open(html_output, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                result_summary["html_file"] = html_output
                print(f"[OK] HTML 已儲存：{html_output}")
            except Exception as html_err:
                logging.warning(f"HTML 輸出失敗: {html_err}")
        
        result_summary["text_content"] = all_text
        
        # ========== 翻譯處理（如果啟用）==========
        # Debug 模式時關閉翻譯功能
        if translate_config and HAS_TRANSLATOR:
            if self.debug_mode:
                print(f"[DEBUG] Debug 模式已啟用，跳過翻譯處理")
                logging.info("Debug 模式已啟用，跳過翻譯處理")
            else:
                self._process_translation_on_pdf(
                    erased_pdf_path=erased_output_path,
                    ocr_results_per_page=all_ocr_results,
                    translate_config=translate_config,
                    result_summary=result_summary,
                    dpi=dpi
                )
        
        print(f"[OK] 混合模式處理完成：{result_summary['pages_processed']} 頁")
        
        return result_summary
    
    def _process_hybrid_image(
        self,
        image_path: str,
        output_path: str,
        markdown_output: str,
        result_summary: Dict[str, Any]
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
            with open(markdown_output, 'w', encoding='utf-8') as f:
                f.write(page_markdown)
            result_summary["markdown_file"] = markdown_output
            print(f"[OK] Markdown 已儲存：{markdown_output}")
        
        result_summary["pages_processed"] = 1
        result_summary["text_content"] = [self.get_text(sorted_results)]
        
        return result_summary
    
    def _merge_hybrid_results(
        self,
        structure_output,
        ocr_output,
        page_num: int
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
                
                if hasattr(res, 'markdown'):
                    md_content = res.markdown
                elif isinstance(res, dict):
                    md_content = res.get('markdown', None)
                
                # 確保只添加字串類型
                if md_content is not None:
                    if isinstance(md_content, str):
                        markdown_parts.append(md_content)
                    elif isinstance(md_content, dict):
                        # 如果是 dict，嘗試提取文字內容
                        text = md_content.get('text', '') or md_content.get('content', '')
                        if text and isinstance(text, str):
                            markdown_parts.append(text)
                    elif isinstance(md_content, list):
                        # 如果是 list，連接所有字串元素
                        for item in md_content:
                            if isinstance(item, str):
                                markdown_parts.append(item)
                            elif isinstance(item, dict):
                                text = item.get('text', '') or item.get('content', '')
                                if text and isinstance(text, str):
                                    markdown_parts.append(text)
                
                # 取得版面區塊資訊
                if hasattr(res, 'layout_blocks'):
                    layout_blocks.extend(res.layout_blocks)
                elif hasattr(res, 'blocks'):
                    layout_blocks.extend(res.blocks)
                elif isinstance(res, dict):
                    blocks = res.get('layout_blocks', []) or res.get('blocks', [])
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
                page_markdown = f"## 第 {page_num} 頁\n\n" + self.get_text(sorted_results, separator="\n\n")
        else:
            # 使用排序後的文字生成 Markdown
            page_markdown = f"## 第 {page_num} 頁\n\n" + self.get_text(sorted_results, separator="\n\n")
        
        return sorted_results, page_markdown
    
    def _extract_ocr_from_structure(self, structure_output, markdown_text: str = None) -> List[OCRResult]:
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
                if 'overall_ocr_res' in res:
                    overall_ocr = res['overall_ocr_res']
                    if overall_ocr is not None:
                        try:
                            texts = overall_ocr.get('rec_texts', [])
                            scores = overall_ocr.get('rec_scores', [])
                            rec_boxes = overall_ocr.get('rec_boxes')
                            dt_polys = overall_ocr.get('dt_polys', [])
                            
                            logging.info(f"  overall_ocr_res: texts={len(texts) if texts else 0}, boxes={len(rec_boxes) if rec_boxes is not None else 0}")
                            
                            if texts:
                                # 優先使用 rec_boxes
                                if rec_boxes is not None and len(rec_boxes) > 0:
                                    boxes_list = rec_boxes.tolist() if hasattr(rec_boxes, 'tolist') else rec_boxes
                                    for i, (box, text) in enumerate(zip(boxes_list, texts)):
                                        if text and str(text).strip():
                                            x1, y1, x2, y2 = float(box[0]), float(box[1]), float(box[2]), float(box[3])
                                            bbox = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
                                            conf = float(scores[i]) if i < len(scores) else 0.9
                                            ocr_results.append(OCRResult(
                                                text=fix_english_spacing(str(text)),
                                                confidence=conf,
                                                bbox=bbox
                                            ))
                                    logging.info(f"  從 rec_boxes 提取了 {len(ocr_results)} 個結果")
                                
                                # 使用 dt_polys
                                elif dt_polys and len(dt_polys) > 0:
                                    for i, (poly, text) in enumerate(zip(dt_polys, texts)):
                                        if poly is not None and text and str(text).strip():
                                            poly_list = poly.tolist() if hasattr(poly, 'tolist') else poly
                                            bbox = [[float(p[0]), float(p[1])] for p in poly_list]
                                            conf = float(scores[i]) if i < len(scores) else 0.9
                                            ocr_results.append(OCRResult(
                                                text=fix_english_spacing(str(text)),
                                                confidence=conf,
                                                bbox=bbox
                                            ))
                                    logging.info(f"  從 dt_polys 提取了 {len(ocr_results)} 個結果")
                                    
                        except Exception as e:
                            logging.warning(f"  訪問 overall_ocr_res 失敗: {e}")
                            logging.warning(traceback.format_exc())
                
                # ========== 方式 2：回退到 parsing_res_list（區塊級座標）==========
                # 只有當 overall_ocr_res 沒有取得結果時才使用
                if not ocr_results and 'parsing_res_list' in res:
                    parsing_list = res['parsing_res_list']
                    if parsing_list:
                        logging.info(f"  回退到 parsing_res_list，共 {len(parsing_list)} 個區塊")
                        
                        for block in parsing_list:
                            try:
                                bbox = getattr(block, 'bbox', None)
                                content = getattr(block, 'content', None)
                                
                                if bbox is not None and content and str(content).strip():
                                    content_str = str(content).strip()
                                    if len(bbox) >= 4:
                                        x1, y1, x2, y2 = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
                                        bbox_points = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
                                        ocr_results.append(OCRResult(
                                            text=fix_english_spacing(content_str),
                                            confidence=0.85,
                                            bbox=bbox_points
                                        ))
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
        self,
        ocr_results: List[OCRResult],
        layout_blocks: List
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
                    if hasattr(block, 'bbox'):
                        bbox = block.bbox
                    elif isinstance(block, dict) and 'bbox' in block:
                        bbox = block['bbox']
                    else:
                        continue
                    
                    # 檢查 OCR 結果是否在區塊內
                    if (bbox[0] <= ocr_center[0] <= bbox[2] and
                        bbox[1] <= ocr_center[1] <= bbox[3]):
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
        dpi: int = 150
    ) -> None:
        """
        在擦除版 PDF 基礎上進行翻譯處理
        
        流程：
        1. 開啟 *_erased.pdf（已擦除）
        2. 翻譯文字
        3. 在擦除後的圖片上繪製翻譯文字
        4. 生成 *_translated_{lang}.pdf 和 *_bilingual_{lang}.pdf
        
        Args:
            erased_pdf_path: 已擦除的 PDF 路徑（*_erased.pdf）
            ocr_results_per_page: 每頁的 OCR 結果列表
            translate_config: 翻譯配置
            result_summary: 結果摘要（會被更新）
            dpi: PDF 轉圖片時使用的 DPI
        """
        print(f"\n[翻譯] 開始翻譯處理...")
        logging.info(f"開始翻譯處理: {erased_pdf_path}")
        
        source_lang = translate_config.get('source_lang', 'auto')
        target_lang = translate_config.get('target_lang', 'en')
        ollama_model = translate_config.get('ollama_model', 'qwen2.5:7b')
        ollama_url = translate_config.get('ollama_url', 'http://localhost:11434')
        no_mono = translate_config.get('no_mono', False)
        no_dual = translate_config.get('no_dual', False)
        dual_mode = translate_config.get('dual_mode', 'alternating')
        font_path = translate_config.get('font_path', None)
        # 翻譯 debug 模式（暫時不用，預設關閉，之後會用）
        translate_debug = translate_config.get('translate_debug', False)
        
        print(f"   來源語言: {source_lang}")
        print(f"   目標語言: {target_lang}")
        print(f"   Ollama 模型: {ollama_model}")
        
        try:
            # 初始化翻譯器和繪製器
            translator = OllamaTranslator(model=ollama_model, base_url=ollama_url)
            renderer = TextRenderer(font_path=font_path)  # 用於繪製翻譯文字
            
            # 開啟擦除版 PDF
            pdf_doc = fitz.open(erased_pdf_path)
            total_pages = len(pdf_doc)
            
            # 開啟原始 hybrid.pdf 用於生成雙語對照
            hybrid_pdf_path = erased_pdf_path.replace('_erased.pdf', '_hybrid.pdf')
            hybrid_doc = None
            if not no_dual and os.path.exists(hybrid_pdf_path):
                hybrid_doc = fitz.open(hybrid_pdf_path)
            
            # 建立輸出路徑
            base_path = erased_pdf_path.replace('_erased.pdf', '')
            translated_path = f"{base_path}_translated_{target_lang}.pdf" if not no_mono else None
            bilingual_path = f"{base_path}_bilingual_{target_lang}.pdf" if not no_dual else None
            
            # 建立 PDF 生成器
            mono_generator = MonolingualPDFGenerator() if translated_path else None
            bilingual_generator = BilingualPDFGenerator(
                mode=dual_mode,
                translate_first=translate_config.get('dual_translate_first', False)
            ) if bilingual_path else None
            
            # 進度條
            page_iter = range(total_pages)
            if HAS_TQDM:
                page_iter = tqdm(page_iter, desc="翻譯頁面", unit="頁", ncols=80)
            
            for page_num in page_iter:
                try:
                    # 取得該頁的 OCR 結果
                    if page_num >= len(ocr_results_per_page):
                        logging.warning(f"第 {page_num + 1} 頁沒有 OCR 結果")
                        continue
                    
                    page_ocr_results = ocr_results_per_page[page_num]
                    
                    # ========== 取得擦除版圖片（已經擦除過了）==========
                    erased_page = pdf_doc[page_num]
                    zoom = dpi / 72.0
                    matrix = fitz.Matrix(zoom, zoom)
                    erased_pixmap = erased_page.get_pixmap(matrix=matrix)
                    
                    erased_image = np.frombuffer(erased_pixmap.samples, dtype=np.uint8)
                    erased_image = erased_image.reshape(erased_pixmap.height, erased_pixmap.width, erased_pixmap.n).copy()
                    if erased_pixmap.n == 4:
                        erased_image = erased_image[:, :, :3].copy()
                    
                    # 取得原始圖片（用於雙語對照）
                    original_image = erased_image.copy()
                    if hybrid_doc:
                        hybrid_page = hybrid_doc[page_num]
                        hybrid_pixmap = hybrid_page.get_pixmap(matrix=matrix)
                        original_image = np.frombuffer(hybrid_pixmap.samples, dtype=np.uint8)
                        original_image = original_image.reshape(hybrid_pixmap.height, hybrid_pixmap.width, hybrid_pixmap.n).copy()
                        if hybrid_pixmap.n == 4:
                            original_image = original_image[:, :, :3].copy()
                    
                    if not page_ocr_results:
                        # 沒有文字需要翻譯，保留擦除版圖片
                        if mono_generator:
                            mono_generator.add_page(erased_image)
                        if bilingual_generator:
                            bilingual_generator.add_bilingual_page(original_image, erased_image)
                        continue
                    
                    # 收集需要翻譯的文字和 bbox
                    texts_to_translate = []
                    valid_results = []
                    bboxes = []
                    for result in page_ocr_results:
                        if result.text and result.text.strip():
                            texts_to_translate.append(result.text)
                            valid_results.append(result)
                            bboxes.append(result.bbox)
                    
                    if not texts_to_translate:
                        if mono_generator:
                            mono_generator.add_page(erased_image)
                        if bilingual_generator:
                            bilingual_generator.add_bilingual_page(original_image, erased_image)
                        continue
                    
                    logging.info(f"第 {page_num + 1} 頁: 翻譯 {len(texts_to_translate)} 個文字區塊")
                    
                    # ========== 批次翻譯 ==========
                    translated_texts = translator.translate_batch(
                        texts_to_translate, source_lang, target_lang, show_progress=False
                    )
                    
                    # ========== 在擦除後的圖片上繪製翻譯文字 ==========
                    translated_blocks = []
                    for orig, trans, bbox in zip(texts_to_translate, translated_texts, bboxes):
                        translated_blocks.append(TranslatedBlock(
                            original_text=orig,
                            translated_text=trans,
                            bbox=bbox
                        ))
                    
                    translated_image = erased_image.copy()
                    translated_image = renderer.render_multiple_texts(
                        translated_image, translated_blocks
                    )
                    
                    # 添加到純翻譯 PDF
                    if mono_generator:
                        mono_generator.add_page(translated_image)
                    
                    # 添加到雙語對照 PDF
                    if bilingual_generator:
                        bilingual_generator.add_bilingual_page(original_image, translated_image)
                    
                    # 清理記憶體
                    del erased_pixmap
                    gc.collect()
                    
                except Exception as page_err:
                    logging.error(f"翻譯第 {page_num + 1} 頁時發生錯誤: {page_err}")
                    logging.error(traceback.format_exc())
                    continue
            
            pdf_doc.close()
            if hybrid_doc:
                hybrid_doc.close()
            
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
        html_output: Optional[str] = None
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
            'source_lang': source_lang,
            'target_lang': target_lang,
            'ollama_model': ollama_model,
            'ollama_url': ollama_url,
            'no_mono': no_mono,
            'no_dual': no_dual,
            'dual_mode': dual_mode,
            'dual_translate_first': dual_translate_first,
            'font_path': font_path,
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
            translate_config=translate_config
        )
        
        # 更新結果摘要
        result["mode"] = "translate"
        result["source_lang"] = source_lang
        result["target_lang"] = target_lang
        
        return result


def main():
    """命令列入口點"""
    parser = argparse.ArgumentParser(
        description="PaddleOCR 工具 - 多功能文件辨識與處理器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
    # 基本 OCR（輸出文字到終端機）
    python paddle_ocr_tool.py input.pdf
    
    # 生成可搜尋 PDF
    python paddle_ocr_tool.py input.pdf --searchable
    
    # PP-StructureV3 模式（輸出 Markdown 和 Excel）
    python paddle_ocr_tool.py input.pdf --mode structure --markdown-output result.md --excel-output tables.xlsx
    
    # PaddleOCR-VL 模式（輸出 JSON）
    python paddle_ocr_tool.py input.pdf --mode vl --json-output result.json
    
    # 公式識別模式（輸出 LaTeX）
    python paddle_ocr_tool.py math_image.png --mode formula --latex-output formulas.tex
    
    # 啟用文件方向校正
    python paddle_ocr_tool.py input.pdf --orientation-classify --text-output result.txt
    
    # 批次處理目錄
    python paddle_ocr_tool.py ./images/ --searchable
    
    # 儲存文字到檔案
    python paddle_ocr_tool.py input.pdf --text-output result.txt
        """
    )
    
    parser.add_argument(
        "input",
        help="輸入檔案或目錄路徑"
    )
    
    # OCR 模式選項
    parser.add_argument(
        "--mode", "-m",
        type=str,
        default="basic",
        choices=["basic", "structure", "vl", "formula", "hybrid"],
        help="OCR 模式: basic, structure, vl, formula, hybrid (版面分析+精確OCR)"
    )
    
    # 文件校正選項
    parser.add_argument(
        "--orientation-classify",
        action="store_true",
        help="啟用文件方向自動校正"
    )
    
    parser.add_argument(
        "--unwarping",
        action="store_true",
        help="啟用文件彎曲校正"
    )
    
    parser.add_argument(
        "--textline-orientation",
        action="store_true",
        help="啟用文字行方向偵測"
    )
    
    # 輸出選項
    parser.add_argument(
        "--searchable", "-s",
        action="store_true",
        default=True,
        help="生成可搜尋 PDF（僅 basic 模式，預設：啟用）"
    )
    
    parser.add_argument(
        "--no-searchable",
        action="store_true",
        help="停用可搜尋 PDF 生成"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="輸出檔案路徑（預設：[原始檔名]_searchable.pdf）"
    )
    
    parser.add_argument(
        "--text-output", "-t",
        type=str,
        nargs='?',
        const='AUTO',
        default='AUTO',
        help="將識別的文字儲存到檔案（basic 模式，預設：[原始檔名]_ocr.txt）"
    )
    
    parser.add_argument(
        "--no-text-output",
        action="store_true",
        help="停用文字輸出"
    )
    
    parser.add_argument(
        "--markdown-output",
        type=str,
        nargs='?',
        const='AUTO',
        default='AUTO',
        help="輸出 Markdown 格式（structure/vl 模式，預設：[原始檔名]_ocr.md）"
    )
    
    parser.add_argument(
        "--no-markdown-output",
        action="store_true",
        help="停用 Markdown 輸出"
    )
    
    parser.add_argument(
        "--json-output",
        type=str,
        nargs='?',
        const='AUTO',
        default='AUTO',
        help="輸出 JSON 格式（structure/vl 模式，預設：[原始檔名]_ocr.json）"
    )
    
    parser.add_argument(
        "--no-json-output",
        action="store_true",
        help="停用 JSON 輸出"
    )
    
    # Excel 輸出（表格識別）
    parser.add_argument(
        "--excel-output",
        type=str,
        nargs='?',
        const='AUTO',
        default=None,
        help="輸出 Excel 格式（structure 模式，僅表格：[原始檔名]_tables.xlsx）"
    )
    
    # HTML 輸出（structure 模式）
    parser.add_argument(
        "--html-output",
        type=str,
        nargs='?',
        const='AUTO',
        default=None,
        help="輸出 HTML 格式（structure/hybrid 模式：[原始檔名]_page*.html）"
    )
    
    # 輸出全部格式
    parser.add_argument(
        "--all",
        action="store_true",
        help="一次輸出所有格式（Markdown + JSON + HTML，structure/hybrid 模式）"
    )
    
    # LaTeX 輸出（公式識別）
    parser.add_argument(
        "--latex-output",
        type=str,
        nargs='?',
        const='AUTO',
        default=None,
        help="輸出 LaTeX 格式（formula 模式，預設：[原始檔名]_formula.tex）"
    )
    
    # 進度條控制
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="停用進度條顯示"
    )
    
    # 其他選項
    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="PDF 轉圖片的解析度（預設：150，降低以減少記憶體使用）"
    )
    
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        choices=["gpu", "cpu"],
        help="運算設備（預設：cpu，如有 CUDA 可用 --device gpu）"
    )
    
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="遞迴處理子目錄（僅適用於目錄輸入）"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="顯示詳細日誌"
    )
    
    parser.add_argument(
        "--debug-text",
        action="store_true",
        help="DEBUG 模式：將可搜尋 PDF 的隱形文字改為粉紅色可見文字（方便調試文字位置）"
    )
    
    parser.add_argument(
        "--no-compress",
        action="store_true",
        help="停用 PDF 壓縮：使用 PNG 無損格式（檔案較大但品質最佳）"
    )
    
    parser.add_argument(
        "--jpeg-quality",
        type=int,
        default=85,
        help="JPEG 壓縮品質（0-100，預設 85）。較低值 = 較小檔案但品質較差"
    )
    
    # ========== 翻譯選項 ==========
    translate_group = parser.add_argument_group('翻譯選項', '使用 Ollama 本地模型翻譯 PDF 內容')
    
    translate_group.add_argument(
        "--translate",
        action="store_true",
        help="啟用翻譯功能（需要 Ollama 服務和 hybrid 模式）"
    )
    
    translate_group.add_argument(
        "--source-lang",
        type=str,
        default="auto",
        help="來源語言（auto=自動偵測，zh=中文，zh-cn=簡體中文，zh-tw=繁體中文，en=英文，預設：auto）"
    )
    
    translate_group.add_argument(
        "--target-lang",
        type=str,
        default="en",
        help="目標語言（zh=中文，zh-cn=簡體中文，zh-tw=繁體中文，en=英文，ja=日文，預設：en）"
    )
    
    translate_group.add_argument(
        "--ollama-model",
        type=str,
        default="qwen2.5:7b",
        help="Ollama 模型名稱（預設：qwen2.5:7b）"
    )
    
    translate_group.add_argument(
        "--ollama-url",
        type=str,
        default="http://localhost:11434",
        help="Ollama API 地址（預設：http://localhost:11434）"
    )
    
    translate_group.add_argument(
        "--no-mono",
        action="store_true",
        help="不輸出純翻譯 PDF（僅輸出雙語對照）"
    )
    
    translate_group.add_argument(
        "--no-dual",
        action="store_true",
        help="不輸出雙語對照 PDF（僅輸出純翻譯）"
    )
    
    translate_group.add_argument(
        "--dual-mode",
        type=str,
        choices=["alternating", "side-by-side"],
        default="alternating",
        help="雙語對照模式：alternating(交替頁) 或 side-by-side(並排)（預設：alternating）"
    )
    
    translate_group.add_argument(
        "--dual-translate-first",
        action="store_true",
        help="雙語模式中譯文在前（預設：原文在前）"
    )
    
    translate_group.add_argument(
        "--font-path",
        type=str,
        default=None,
        help="自訂字體路徑（用於繪製翻譯文字）"
    )
    
    args = parser.parse_args()
    
    # 驗證輸入
    input_path = Path(args.input)
    if not input_path.exists():
        logging.error(f"輸入路徑不存在: {args.input}")
        print(f"錯誤：輸入路徑不存在: {args.input}")
        sys.exit(1)
    
    # 取得腳本所在目錄和輸入檔案的基本名稱
    script_dir = Path(__file__).parent.resolve()
    if input_path.is_dir():
        base_name = input_path.name
    else:
        base_name = input_path.stem
    
    logging.info(f"=" * 60)
    logging.info(f"開始執行 PaddleOCR 工具")
    logging.info(f"輸入路徑: {input_path}")
    logging.info(f"OCR 模式: {args.mode}")
    
    # 處理 --no-* 選項來覆蓋預設值
    if args.no_searchable:
        args.searchable = False
    if args.no_text_output:
        args.text_output = None
    if args.no_markdown_output:
        args.markdown_output = None
    if args.no_json_output:
        args.json_output = None
    
    # 處理 --all 參數：一次啟用所有輸出格式
    if hasattr(args, 'all') and args.all:
        if args.mode in ['structure', 'vl', 'hybrid']:
            args.markdown_output = args.markdown_output or 'AUTO'
            args.json_output = args.json_output or 'AUTO'
            args.html_output = args.html_output or 'AUTO'
            print(f"[--all] 啟用所有輸出格式：Markdown, JSON, HTML")
    
    # 根據模式設定預設輸出路徑
    if args.mode == "basic":
        # basic 模式：處理 text_output 和 searchable
        if args.text_output == 'AUTO':
            args.text_output = str(script_dir / f"{base_name}_ocr.txt")
        # 忽略其他模式專用的輸出
        args.markdown_output = None
        args.json_output = None
        args.excel_output = None
        args.latex_output = None
    elif args.mode == "formula":
        # formula 模式：處理 latex_output
        if args.latex_output == 'AUTO':
            args.latex_output = str(script_dir / f"{base_name}_formula.tex")
        # 忽略其他模式專用的輸出
        args.searchable = False
        args.text_output = None
        args.markdown_output = None
        args.json_output = None
        args.excel_output = None
    elif args.mode == "hybrid":
        # hybrid 模式：處理 searchable、markdown_output、json_output、html_output
        if args.markdown_output == 'AUTO':
            args.markdown_output = str(script_dir / f"{base_name}_hybrid.md")
        if args.json_output == 'AUTO':
            args.json_output = str(script_dir / f"{base_name}_hybrid.json")
        if args.html_output == 'AUTO':
            args.html_output = str(script_dir / f"{base_name}_hybrid.html")
        # hybrid 模式會自動生成可搜尋 PDF
        args.searchable = True
        args.text_output = None
        args.excel_output = None
        args.latex_output = None
    else:
        # structure/vl 模式：處理 markdown_output、json_output、excel_output 和 html_output
        if args.markdown_output == 'AUTO':
            args.markdown_output = str(script_dir / f"{base_name}_ocr.md")
        if args.json_output == 'AUTO':
            args.json_output = str(script_dir / f"{base_name}_ocr.json")
        if args.excel_output == 'AUTO':
            args.excel_output = str(script_dir / f"{base_name}_tables.xlsx")
        if args.html_output == 'AUTO':
            args.html_output = str(script_dir / f"{base_name}_ocr.html")
        # 忽略 basic 專用的輸出
        args.searchable = False
        args.text_output = None
        args.latex_output = None
    
    # 顯示輸出設定摘要
    print(f"\n[輸入] {input_path}")
    print(f"[模式] {args.mode}")
    if args.mode == "basic":
        print(f"[可搜尋 PDF] {'啟用' if args.searchable else '停用'}")
        print(f"[文字輸出] {args.text_output if args.text_output else '停用'}")
    elif args.mode == "formula":
        print(f"[LaTeX 輸出] {args.latex_output if args.latex_output else '停用'}")
    elif args.mode == "hybrid":
        print(f"[可搜尋 PDF] 啟用（混合模式）")
        print(f"[Markdown 輸出] {args.markdown_output if args.markdown_output else '停用'}")
        print(f"[JSON 輸出] {args.json_output if args.json_output else '停用'}")
        print(f"[HTML 輸出] {args.html_output if args.html_output else '停用'}")
    else:
        print(f"[Markdown 輸出] {args.markdown_output if args.markdown_output else '停用'}")
        print(f"[JSON 輸出] {args.json_output if args.json_output else '停用'}")
        print(f"[Excel 輸出] {args.excel_output if args.excel_output else '停用'}")
        print(f"[HTML 輸出] {args.html_output if args.html_output else '停用'}")
    if not args.no_progress and HAS_TQDM:
        print(f"[進度條] 啟用")
    print()
    
    # 檢查進階模組可用性
    if args.mode == "structure" and not HAS_STRUCTURE:
        print("錯誤：PP-StructureV3 模組不可用")
        print("請確認已安裝最新版 paddleocr: pip install -U paddleocr")
        sys.exit(1)
    
    if args.mode == "vl" and not HAS_VL:
        print("錯誤：PaddleOCR-VL 模組不可用")
        print("請確認已安裝最新版 paddleocr: pip install -U paddleocr")
        sys.exit(1)
    
    if args.mode == "formula" and not HAS_FORMULA:
        print("錯誤：FormulaRecPipeline 模組不可用")
        print("請確認已安裝最新版 paddleocr: pip install -U paddleocr")
        sys.exit(1)
    
    if args.mode == "hybrid" and not HAS_STRUCTURE:
        print("錯誤：Hybrid 模式需要 PP-StructureV3 模組")
        print("請確認已安裝最新版 paddleocr: pip install -U paddleocr")
        sys.exit(1)
    
    # 初始化 OCR 工具
    tool = PaddleOCRTool(
        mode=args.mode,
        use_orientation_classify=args.orientation_classify,
        use_doc_unwarping=args.unwarping,
        use_textline_orientation=args.textline_orientation,
        device=args.device,
        debug_mode=args.debug_text,
        compress_images=not args.no_compress,
        jpeg_quality=args.jpeg_quality
    )
    
    # 顯示壓縮設定
    if not args.no_compress:
        print(f"[壓縮] 啟用（JPEG 品質：{args.jpeg_quality}%）")
    else:
        print(f"[壓縮] 停用（使用 PNG 無損格式）")
    
    # 根據模式處理
    if args.mode == "formula":
        # 公式識別模式
        result = tool.process_formula(
            input_path=str(input_path),
            latex_output=args.latex_output
        )
        
        if result.get("error"):
            print(f"處理過程中發生錯誤: {result['error']}")
        else:
            print(f"\n[OK] 公式識別完成！共識別 {len(result['formulas'])} 個公式")
            if result.get("latex_file"):
                print(f"  LaTeX 檔案: {result['latex_file']}")
    
    elif args.mode in ["structure", "vl"]:
        # 結構化處理模式
        result = tool.process_structured(
            input_path=str(input_path),
            markdown_output=args.markdown_output,
            json_output=args.json_output,
            excel_output=args.excel_output,
            html_output=args.html_output
        )
        
        if result.get("error"):
            print(f"處理過程中發生錯誤: {result['error']}")
        else:
            print(f"\n[OK] 處理完成！共處理 {result['pages_processed']} 頁")
            if result.get("markdown_files"):
                print(f"  Markdown 檔案: {', '.join(result['markdown_files'])}")
            if result.get("json_files"):
                print(f"  JSON 檔案: {', '.join(result['json_files'])}")
            if result.get("excel_files"):
                print(f"  Excel 檔案: {', '.join(result['excel_files'])}")
            if result.get("html_files"):
                print(f"  HTML 檔案: {', '.join(result['html_files'])}")
    
    elif args.mode == "hybrid":
        # 混合模式：版面分析 + 精確 OCR
        show_progress = not args.no_progress
        
        # 檢查是否啟用翻譯功能
        if hasattr(args, 'translate') and args.translate:
            # 翻譯模式
            if not HAS_TRANSLATOR:
                print("錯誤：翻譯模組不可用")
                print("請確認 pdf_translator.py 存在且依賴已安裝")
                sys.exit(1)
            
            print(f"[翻譯功能] 啟用")
            print(f"   來源語言：{args.source_lang}")
            print(f"   目標語言：{args.target_lang}")
            print(f"   Ollama 模型：{args.ollama_model}")
            print(f"   純翻譯 PDF：{'停用' if args.no_mono else '啟用'}")
            print(f"   雙語對照 PDF：{'停用' if args.no_dual else f'啟用 ({args.dual_mode})'}")
            
            result = tool.process_translate(
                input_path=str(input_path),
                output_path=args.output,
                source_lang=args.source_lang,
                target_lang=args.target_lang,
                ollama_model=args.ollama_model,
                ollama_url=args.ollama_url,
                no_mono=args.no_mono,
                no_dual=args.no_dual,
                dual_mode=args.dual_mode,
                dual_translate_first=args.dual_translate_first,
                font_path=args.font_path,
                dpi=args.dpi,
                show_progress=show_progress,
                json_output=args.json_output,
                html_output=args.html_output
            )
            
            if result.get("error"):
                print(f"處理過程中發生錯誤: {result['error']}")
            else:
                print(f"\n[OK] 翻譯處理完成！共處理 {result['pages_processed']} 頁")
                if result.get("searchable_pdf"):
                    print(f"  [可搜尋 PDF] {result['searchable_pdf']}")
                if result.get("markdown_file"):
                    print(f"  [Markdown] {result['markdown_file']}")
                if result.get("json_file"):
                    print(f"  [JSON] {result['json_file']}")
                if result.get("html_file"):
                    print(f"  [HTML] {result['html_file']}")
                if result.get("translated_pdf"):
                    print(f"  [翻譯PDF] {result['translated_pdf']}")
                if result.get("bilingual_pdf"):
                    print(f"  [雙語PDF] {result['bilingual_pdf']}")
        else:
            # 一般 hybrid 模式（無翻譯）
            result = tool.process_hybrid(
                input_path=str(input_path),
                output_path=args.output,
                markdown_output=args.markdown_output,
                json_output=args.json_output,
                html_output=args.html_output,
                dpi=args.dpi,
                show_progress=show_progress
            )
            
            if result.get("error"):
                print(f"處理過程中發生錯誤: {result['error']}")
            else:
                print(f"\n[OK] 混合模式處理完成！共處理 {result['pages_processed']} 頁")
                if result.get("searchable_pdf"):
                    print(f"  可搜尋 PDF: {result['searchable_pdf']}")
                if result.get("markdown_file"):
                    print(f"  Markdown 檔案: {result['markdown_file']}")
    
    else:
        # basic 模式（原有邏輯）
        all_text = []
        show_progress = not args.no_progress
        
        # 處理輸入
        if input_path.is_dir():
            # 目錄處理
            results = tool.process_directory(
                str(input_path),
                output_path=args.output,
                searchable=args.searchable,
                recursive=args.recursive
            )
            
            for file_path, file_results in results.items():
                text = tool.get_text(file_results)
                if text:
                    all_text.append(f"=== {file_path} ===\n{text}")
        
        elif input_path.suffix.lower() == SUPPORTED_PDF_FORMAT:
            # PDF 處理（使用進度條）
            results, output_path = tool.process_pdf(
                str(input_path),
                output_path=args.output,
                searchable=args.searchable,
                dpi=args.dpi,
                show_progress=show_progress
            )
            
            for page_num, page_results in enumerate(results, 1):
                text = tool.get_text(page_results)
                if text:
                    all_text.append(f"=== 第 {page_num} 頁 ===\n{text}")
        
        elif input_path.suffix.lower() in SUPPORTED_IMAGE_FORMATS:
            # 圖片處理
            results = tool.process_image(str(input_path))
            
            if args.searchable:
                output_path = args.output or str(input_path.with_suffix('.pdf'))
                pdf_generator = PDFGenerator(output_path, debug_mode=args.debug_text)
                pdf_generator.add_page(str(input_path), results)
                pdf_generator.save()
            
            text = tool.get_text(results)
            if text:
                all_text.append(text)
        
        else:
            print(f"錯誤：不支援的檔案格式: {input_path.suffix}")
            sys.exit(1)
        
        # 輸出結果
        combined_text = "\n\n".join(all_text)
        
        if args.text_output:
            # 如果輸出路徑不是絕對路徑，則相對於腳本目錄
            text_output_path = Path(args.text_output)
            if not text_output_path.is_absolute():
                text_output_path = script_dir / text_output_path
            
            # 儲存到檔案
            with open(text_output_path, 'w', encoding='utf-8') as f:
                f.write(combined_text)
            print(f"[OK] 文字已儲存：{text_output_path}")
        
        # 如果兩個輸出都停用，則輸出到終端機
        if not args.text_output and not args.searchable and combined_text:
            print("\n" + "=" * 50)
            print("OCR 辨識結果：")
            print("=" * 50)
            print(combined_text)
        
        print("\n[OK] 處理完成！")


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


