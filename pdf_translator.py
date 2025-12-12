#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 翻譯模組

使用 Ollama 本地大語言模型進行 PDF 翻譯，支援：
- 純翻譯 PDF 輸出
- 雙語對照 PDF 輸出（交替頁/並排模式）

依賴：requests, opencv-python, Pillow, PyMuPDF
"""

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    logging.warning("OpenCV 未安裝，文字擦除功能不可用")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    logging.warning("requests 未安裝，翻譯功能不可用")

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False
    logging.warning("PyMuPDF 未安裝，PDF 生成功能不可用")


@dataclass
class TranslatedBlock:
    """翻譯區塊，包含原文、譯文和位置資訊"""
    original_text: str
    translated_text: str
    bbox: List[List[float]]  # [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
    
    @property
    def x(self) -> float:
        return min(p[0] for p in self.bbox)
    
    @property
    def y(self) -> float:
        return min(p[1] for p in self.bbox)
    
    @property
    def width(self) -> float:
        return max(p[0] for p in self.bbox) - self.x
    
    @property
    def height(self) -> float:
        return max(p[1] for p in self.bbox) - self.y


class TranslationEngine(ABC):
    """翻譯引擎抽象基類"""
    
    @abstractmethod
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """翻譯單一文字"""
        pass
    
    def translate_batch(
        self, 
        texts: List[str], 
        source_lang: str, 
        target_lang: str,
        show_progress: bool = True
    ) -> List[str]:
        """批次翻譯多個文字"""
        results = []
        for text in texts:
            try:
                result = self.translate(text, source_lang, target_lang)
                results.append(result)
            except Exception as e:
                logging.warning(f"翻譯失敗: {e}")
                results.append(text)  # 翻譯失敗時保留原文
        return results


class OllamaTranslator(TranslationEngine):
    """使用 Ollama 本地模型進行翻譯
    
    支援外部術語表 (glossary.csv) 來保護專業術語不被誤翻。
    術語表格式：英文術語,中文翻譯,類別,保留原文(Y/N)
    """
    
    # 內建術語保留列表（作為後備）
    DEFAULT_PRESERVE_TERMS = {
        "MEMS", "CMOS", "MUMPs", "PolyMUMPs", "SOIMUMPs", "MetalMUMPs",
        "VLSI", "ASIC", "FPGA", "SoC", "IC", "PCB", "RF", "RFID",
        "CVD", "PVD", "RIE", "DRIE", "CMP", "LPCVD", "PECVD",
        "SOI", "API", "SDK", "CPU", "GPU", "RAM", "ROM",
        "TSMC", "Intel", "Samsung", "Cronos", "MEMScAP",
    }
    
    def __init__(
        self, 
        model: str = "qwen2.5:7b",
        base_url: str = "http://localhost:11434",
        glossary_path: Optional[str] = None
    ):
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api/generate"
        
        # 載入術語表
        self.preserve_terms = set()  # 保留原文的術語
        self.translation_dict = {}    # 指定翻譯的術語
        
        if glossary_path:
            self._load_glossary(glossary_path)
        else:
            # 嘗試載入預設路徑的術語表
            default_glossary = Path(__file__).parent / "glossary.csv"
            if default_glossary.exists():
                self._load_glossary(str(default_glossary))
            else:
                self.preserve_terms = self.DEFAULT_PRESERVE_TERMS.copy()
    
    def _load_glossary(self, glossary_path: str):
        """載入外部術語表"""
        try:
            with open(glossary_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split(',')
                    if len(parts) >= 4:
                        term = parts[0].strip()
                        translation = parts[1].strip()
                        # category = parts[2].strip()  # 可用於篩選
                        preserve = parts[3].strip().upper() == 'Y'
                        
                        if preserve:
                            self.preserve_terms.add(term)
                        elif translation:
                            self.translation_dict[term] = translation
                    elif len(parts) >= 1:
                        # 簡單格式：只有術語
                        self.preserve_terms.add(parts[0].strip())
            
            logging.info(f"載入術語表：{len(self.preserve_terms)} 個保留術語，{len(self.translation_dict)} 個翻譯術語")
        except Exception as e:
            logging.warning(f"載入術語表失敗：{e}，使用內建術語表")
            self.preserve_terms = self.DEFAULT_PRESERVE_TERMS.copy()
        
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """使用 Ollama 翻譯文字"""
        if not HAS_REQUESTS:
            raise ImportError("requests 未安裝")
        
        if not text or not text.strip():
            return text
        
        # 找出文本中存在的專業術語（用於提示詞注入）
        found_preserve_terms = []
        found_translations = {}
        
        for term in self.preserve_terms:
            if term in text:
                found_preserve_terms.append(term)
        
        for term, translation in self.translation_dict.items():
            if term in text:
                found_translations[term] = translation
            
        # 語言代碼轉換為自然語言描述
        lang_names = {
            "auto": "自動偵測",
            "zh": "中文",
            "zh-cn": "簡體中文",
            "zh-tw": "繁體中文",
            "en": "英文",
            "ja": "日文",
            "ko": "韓文",
        }
        
        source_name = lang_names.get(source_lang, source_lang)
        target_name = lang_names.get(target_lang, target_lang)
        
        # 建立術語提示（如果有找到術語）
        term_hint = ""
        if found_preserve_terms or found_translations:
            hints = []
            if found_preserve_terms:
                hints.append(f"保留原文不翻譯：{', '.join(found_preserve_terms[:10])}")  # 限制數量避免提示詞過長
            if found_translations:
                trans_hints = [f"{k}→{v}" for k, v in list(found_translations.items())[:10]]
                hints.append(f"指定翻譯：{', '.join(trans_hints)}")
            term_hint = "\n【術語規則】\n" + "\n".join(hints) + "\n"
        
        # 建立翻譯提示
        # 針對簡繁轉換使用特殊提示
        is_chinese_conversion = (
            (source_lang in ["zh", "zh-cn"] and target_lang == "zh-tw") or
            (source_lang in ["zh", "zh-tw"] and target_lang == "zh-cn")
        )
        
        if is_chinese_conversion:
            # 簡繁轉換專用提示 - 強化版
            if target_lang == "zh-tw":
                prompt = f"""你是一個簡繁轉換專家。請將以下簡體中文轉換成繁體中文。

【嚴格規則】
1. 只進行簡體字→繁體字的轉換
2. 絕對不要翻譯成英文或其他語言
3. 如果某個字簡繁相同（如「今晚」「已經」），直接保留原字
4. 只輸出轉換結果，不要任何解釋

簡體中文：{text}

繁體中文："""
            else:
                prompt = f"""你是一個繁簡轉換專家。請將以下繁體中文轉換成簡體中文。

【嚴格規則】
1. 只進行繁體字→簡體字的轉換
2. 絕對不要翻譯成英文或其他語言
3. 如果某個字繁簡相同，直接保留原字
4. 只輸出轉換結果，不要任何解釋

繁體中文：{text}

簡體中文："""
        elif source_lang == "auto":
            prompt = f"""請將以下文字翻譯成{target_name}。
{term_hint}只輸出{target_name}譯文，不要解釋。

原文：{text}

譯文："""
        else:
            prompt = f"""將以下{source_name}翻譯成{target_name}。
{term_hint}只輸出譯文，不要解釋。

原文：{text}

譯文："""
        
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # 降低隨機性
                        "top_p": 0.8,
                        "repeat_penalty": 1.1,
                    }
                },
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            translated = result.get("response", "").strip()
            
            # 清理可能的多餘標記和提示詞洩漏
            prefixes_to_remove = [
                "翻譯：", "翻譯:", 
                "繁體中文：", "繁體中文:", 
                "簡體中文：", "簡體中文:",
                "英文翻譯：", "英文翻譯:",
                "Translation:", "Translation：",
            ]
            for prefix in prefixes_to_remove:
                if translated.startswith(prefix):
                    translated = translated[len(prefix):].strip()
            
            # 移除可能洩漏的提示詞片段
            prompt_leaks = [
                "重要：", "重要:", 
                "【嚴格規則】", "【規則】",
                "只輸出", "不要輸出", "不要添加",
                "絕對不要", "直接保留",
            ]
            for leak in prompt_leaks:
                if leak in translated:
                    # 找到洩漏點並截斷
                    leak_pos = translated.find(leak)
                    if leak_pos > 0:
                        translated = translated[:leak_pos].strip()
                    else:
                        # 如果在開頭，嘗試找下一個換行後的內容
                        parts = translated.split('\n')
                        for i, part in enumerate(parts):
                            if any(l in part for l in prompt_leaks):
                                continue
                            else:
                                translated = '\n'.join(parts[i:])
                                break
            
            # 如果是簡繁轉換，檢測是否誤翻成英文
            if is_chinese_conversion and translated:
                chinese_ratio = self._calculate_chinese_ratio(translated)
                original_chinese_ratio = self._calculate_chinese_ratio(text)
                
                # 如果原文是中文但翻譯結果中文比例太低，返回原文
                if original_chinese_ratio > 0.5 and chinese_ratio < 0.3:
                    logging.warning(f"簡繁轉換誤翻成其他語言，返回原文: {translated[:30]}...")
                    return text
            
            return translated if translated else text
            
        except Exception as e:
            logging.error(f"Ollama 翻譯失敗: {e}")
            return text
    
    def _calculate_chinese_ratio(self, text: str) -> float:
        """計算文字中的中文字元比例"""
        if not text:
            return 0.0
        
        chinese_count = 0
        total_chars = 0
        
        for char in text:
            if char.isspace():
                continue
            total_chars += 1
            # 檢測 CJK 統一漢字
            if '\u4e00' <= char <= '\u9fff':
                chinese_count += 1
            # 擴展 CJK
            elif '\u3400' <= char <= '\u4dbf':
                chinese_count += 1
            elif '\u20000' <= char <= '\u2a6df':
                chinese_count += 1
        
        return chinese_count / total_chars if total_chars > 0 else 0.0


class TextInpainter:
    """文字區域擦除器，使用 OpenCV inpaint 或簡單填充"""
    
    def __init__(self):
        if not HAS_OPENCV:
            logging.warning("OpenCV 未安裝，將使用簡單填充模式")
    
    def erase_region(
        self, 
        image: np.ndarray, 
        bbox: List[List[float]],
        fill_color: Tuple[int, int, int] = (255, 255, 255)
    ) -> np.ndarray:
        """擦除單一區域"""
        result = image.copy()
        
        # 計算矩形邊界
        x1 = int(min(p[0] for p in bbox))
        y1 = int(min(p[1] for p in bbox))
        x2 = int(max(p[0] for p in bbox))
        y2 = int(max(p[1] for p in bbox))
        
        # 簡單填充
        result[y1:y2, x1:x2] = fill_color
        
        return result
    
    def erase_multiple_regions(
        self, 
        image: np.ndarray, 
        bboxes: List[List[List[float]]],
        fill_color: Tuple[int, int, int] = (255, 255, 255)
    ) -> np.ndarray:
        """擦除多個區域"""
        result = image.copy()
        
        for bbox in bboxes:
            result = self.erase_region(result, bbox, fill_color)
        
        return result


class TextRenderer:
    """文字繪製器，使用 Pillow 繪製翻譯後的文字"""
    
    def __init__(self, font_path: Optional[str] = None):
        self.font_path = font_path
        self._font_cache = {}
        
    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """獲取字體，支援快取"""
        if size in self._font_cache:
            return self._font_cache[size]
        
        font = None
        
        # 嘗試自訂字體
        if self.font_path and os.path.exists(self.font_path):
            try:
                font = ImageFont.truetype(self.font_path, size)
            except Exception as e:
                logging.warning(f"載入自訂字體失敗: {e}")
        
        # 嘗試系統中文字體
        if font is None:
            chinese_fonts = [
                # Windows
                "C:/Windows/Fonts/msyh.ttc",      # 微軟雅黑
                "C:/Windows/Fonts/msjh.ttc",      # 微軟正黑
                "C:/Windows/Fonts/simsun.ttc",    # 宋體
                "C:/Windows/Fonts/simhei.ttf",    # 黑體
                # macOS
                "/System/Library/Fonts/PingFang.ttc",
                "/Library/Fonts/Arial Unicode.ttf",
                # Linux
                "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            ]
            
            for font_file in chinese_fonts:
                if os.path.exists(font_file):
                    try:
                        font = ImageFont.truetype(font_file, size)
                        break
                    except Exception:
                        continue
        
        # 使用預設字體
        if font is None:
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None
        
        if font:
            self._font_cache[size] = font
        
        return font
    
    def render_text(
        self, 
        image: np.ndarray, 
        block: TranslatedBlock,
        text_color: Tuple[int, int, int] = (0, 0, 0)
    ) -> np.ndarray:
        """在圖片上繪製翻譯後的文字"""
        pil_image = Image.fromarray(image)
        draw = ImageDraw.Draw(pil_image)
        
        # 根據區域高度計算字體大小
        font_size = max(12, int(block.height * 0.8))
        font = self._get_font(font_size)
        
        # 繪製文字
        x = int(block.x)
        y = int(block.y)
        
        if font:
            # 自動換行
            text = block.translated_text
            max_width = int(block.width)
            
            # 簡單的換行處理
            lines = self._wrap_text(text, font, max_width, draw)
            
            for i, line in enumerate(lines):
                line_y = y + i * font_size
                if line_y + font_size <= block.y + block.height:
                    draw.text((x, line_y), line, font=font, fill=text_color)
        else:
            draw.text((x, y), block.translated_text, fill=text_color)
        
        return np.array(pil_image)
    
    def _wrap_text(
        self, 
        text: str, 
        font: ImageFont.FreeTypeFont, 
        max_width: int,
        draw: ImageDraw.ImageDraw
    ) -> List[str]:
        """將文字換行以適應指定寬度"""
        lines = []
        current_line = ""
        
        for char in text:
            test_line = current_line + char
            try:
                bbox = draw.textbbox((0, 0), test_line, font=font)
                width = bbox[2] - bbox[0]
            except Exception:
                width = len(test_line) * 20
            
            if width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = char
        
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [text]
    
    def render_multiple_texts(
        self, 
        image: np.ndarray, 
        blocks: List[TranslatedBlock],
        text_color: Tuple[int, int, int] = (0, 0, 0)
    ) -> np.ndarray:
        """在圖片上繪製多個翻譯區塊"""
        result = image.copy()
        
        for block in blocks:
            result = self.render_text(result, block, text_color)
        
        return result


class MonolingualPDFGenerator:
    """純翻譯 PDF 生成器"""
    
    def __init__(self):
        if not HAS_FITZ:
            raise ImportError("PyMuPDF 未安裝")
        self.doc = fitz.open()
        self.pages = []
    
    def add_page(self, image: np.ndarray):
        """添加一頁"""
        self.pages.append(image.copy())
    
    def save(self, output_path: str) -> bool:
        """儲存 PDF"""
        try:
            for image in self.pages:
                # 轉換為 PIL Image
                pil_image = Image.fromarray(image)
                
                # 儲存到臨時 bytes
                import io
                img_bytes = io.BytesIO()
                pil_image.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                
                # 創建頁面
                img_rect = fitz.Rect(0, 0, pil_image.width, pil_image.height)
                page = self.doc.new_page(width=img_rect.width, height=img_rect.height)
                page.insert_image(img_rect, stream=img_bytes.read())
            
            self.doc.save(output_path)
            logging.info(f"純翻譯 PDF 已儲存：{output_path}")
            return True
            
        except Exception as e:
            logging.error(f"儲存純翻譯 PDF 失敗：{e}")
            return False
    
    def close(self):
        """關閉文件"""
        if self.doc:
            self.doc.close()


class BilingualPDFGenerator:
    """雙語對照 PDF 生成器"""
    
    def __init__(self, mode: str = "alternating", translate_first: bool = False):
        """
        Args:
            mode: "alternating" (交替頁) 或 "side-by-side" (並排)
            translate_first: True 則譯文在前，False 則原文在前
        """
        if not HAS_FITZ:
            raise ImportError("PyMuPDF 未安裝")
        self.doc = fitz.open()
        self.mode = mode
        self.translate_first = translate_first
        self.page_pairs = []  # [(original, translated), ...]
    
    def add_bilingual_page(self, original: np.ndarray, translated: np.ndarray):
        """添加一對原文/譯文頁面"""
        self.page_pairs.append((original.copy(), translated.copy()))
    
    def save(self, output_path: str) -> bool:
        """儲存雙語 PDF"""
        try:
            import io
            
            for original, translated in self.page_pairs:
                if self.mode == "alternating":
                    # 交替模式：原文頁、譯文頁交替
                    pages = [original, translated]
                    if self.translate_first:
                        pages = [translated, original]
                    
                    for image in pages:
                        pil_image = Image.fromarray(image)
                        img_bytes = io.BytesIO()
                        pil_image.save(img_bytes, format='PNG')
                        img_bytes.seek(0)
                        
                        img_rect = fitz.Rect(0, 0, pil_image.width, pil_image.height)
                        page = self.doc.new_page(width=img_rect.width, height=img_rect.height)
                        page.insert_image(img_rect, stream=img_bytes.read())
                
                else:  # side-by-side
                    # 並排模式：左右並排
                    pil_orig = Image.fromarray(original)
                    pil_trans = Image.fromarray(translated)
                    
                    # 確保高度一致
                    max_height = max(pil_orig.height, pil_trans.height)
                    total_width = pil_orig.width + pil_trans.width
                    
                    combined = Image.new('RGB', (total_width, max_height), (255, 255, 255))
                    
                    if self.translate_first:
                        combined.paste(pil_trans, (0, 0))
                        combined.paste(pil_orig, (pil_trans.width, 0))
                    else:
                        combined.paste(pil_orig, (0, 0))
                        combined.paste(pil_trans, (pil_orig.width, 0))
                    
                    img_bytes = io.BytesIO()
                    combined.save(img_bytes, format='PNG')
                    img_bytes.seek(0)
                    
                    img_rect = fitz.Rect(0, 0, combined.width, combined.height)
                    page = self.doc.new_page(width=img_rect.width, height=img_rect.height)
                    page.insert_image(img_rect, stream=img_bytes.read())
            
            self.doc.save(output_path)
            logging.info(f"雙語對照 PDF 已儲存：{output_path}")
            return True
            
        except Exception as e:
            logging.error(f"儲存雙語 PDF 失敗：{e}")
            return False
    
    def close(self):
        """關閉文件"""
        if self.doc:
            self.doc.close()
