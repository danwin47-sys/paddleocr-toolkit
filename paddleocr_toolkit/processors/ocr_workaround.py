# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - OCR 補救模式

針對掃描件的特殊處理：用白色遮罩覆蓋原文，在上方顯示翻譯。
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

try:
    import fitz

    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


@dataclass
class TextBlock:
    """文字區塊"""

    text: str
    x: float
    y: float
    width: float
    height: float
    color: Tuple[float, float, float] = (0, 0, 0)  # 黑色


class OCRWorkaround:
    """
    OCR 補救模式

    適用於掃描件（黑字白底）的特殊處理：
    1. 在原文位置加入白色矩形遮罩
    2. 在遮罩上方添加翻譯文字（強制黑色）

    注意：僅適用於黑字白底的文件
    """

    def __init__(
        self,
        margin: float = 2.0,
        force_black: bool = True,
        mask_color: Tuple[float, float, float] = (1, 1, 1),  # 白色
    ):
        """
        初始化 OCR 補救模式

        Args:
            margin: 遮罩邊距（像素）
            force_black: 是否強制文字為黑色
            mask_color: 遮罩顏色（預設白色）
        """
        if not HAS_FITZ:
            raise ImportError("PyMuPDF (fitz) 未安裝")

        self.margin = margin
        self.force_black = force_black
        self.mask_color = mask_color

    def add_text_with_mask(
        self,
        page: "fitz.Page",
        original_block: TextBlock,
        translated_text: str,
        font_size: Optional[float] = None,
    ) -> bool:
        """
        在頁面上加入帶遮罩的翻譯文字

        Args:
            page: PyMuPDF 頁面
            original_block: 原文區塊資訊
            translated_text: 翻譯後的文字
            font_size: 字體大小（預設自動計算）

        Returns:
            bool: 是否成功
        """
        try:
            # 計算遮罩區域（比原文區塊稍大）
            mask_rect = fitz.Rect(
                original_block.x - self.margin,
                original_block.y - self.margin,
                original_block.x + original_block.width + self.margin,
                original_block.y + original_block.height + self.margin,
            )

            # 1. 繪製白色遮罩
            shape = page.new_shape()
            shape.draw_rect(mask_rect)
            shape.finish(color=self.mask_color, fill=self.mask_color, width=0)
            shape.commit()

            # 2. 計算字體大小
            if font_size is None:
                font_size = original_block.height * 0.7
                if font_size < 6:
                    font_size = 6
                if font_size > 50:
                    font_size = 50

            # 3. 計算文字位置（基線）
            text_x = original_block.x
            text_y = original_block.y + original_block.height - font_size * 0.2

            # 4. 插入翻譯文字
            text_color = (0, 0, 0) if self.force_black else original_block.color

            page.insert_text(
                fitz.Point(text_x, text_y),
                translated_text,
                fontsize=font_size,
                fontname="helv",
                color=text_color,
            )

            return True

        except Exception as e:
            logging.warning(f"OCR 補救模式失敗: {e}")
            return False

    def process_page(
        self, page: "fitz.Page", text_blocks: List[Tuple[TextBlock, str]]
    ) -> int:
        """
        處理整頁的 OCR 補救

        Args:
            page: PyMuPDF 頁面
            text_blocks: List[(原文區塊, 翻譯文字)]

        Returns:
            成功處理的區塊數
        """
        success_count = 0

        for original, translated in text_blocks:
            if self.add_text_with_mask(page, original, translated):
                success_count += 1

        return success_count


def detect_scanned_document(pdf_path: str, threshold: float = 0.3) -> bool:
    """
    偵測是否為掃描文件

    判斷標準：
    - 可提取的文字量少
    - 圖片數量多

    Args:
        pdf_path: PDF 路徑
        threshold: 文字/圖片比例閾值

    Returns:
        True 表示可能是掃描件
    """
    if not HAS_FITZ:
        return False

    try:
        doc = fitz.open(pdf_path)

        if len(doc) == 0:
            doc.close()
            return False

        # 檢查前 3 頁
        pages_to_check = min(3, len(doc))
        total_text_chars = 0
        total_images = 0

        for i in range(pages_to_check):
            page = doc[i]
            text = page.get_text("text")
            total_text_chars += len(text.strip())
            total_images += len(page.get_images())

        doc.close()

        avg_chars = total_text_chars / pages_to_check
        avg_images = total_images / pages_to_check

        # 如果每頁平均字數少於 100 且有圖片，判斷為掃描件
        is_scanned = avg_chars < 100 and avg_images >= 1

        if is_scanned:
            logging.info(f"偵測為掃描件（平均 {avg_chars:.0f} 字/頁，{avg_images:.1f} 圖/頁）")

        return is_scanned

    except Exception as e:
        logging.warning(f"掃描件偵測失敗: {e}")
        return False


def should_use_ocr_workaround(pdf_path: str, auto_enable: bool = False) -> bool:
    """
    判斷是否應該使用 OCR 補救模式

    Args:
        pdf_path: PDF 路徑
        auto_enable: 是否自動啟用

    Returns:
        是否應該使用 OCR 補救模式
    """
    if not auto_enable:
        return False

    return detect_scanned_document(pdf_path)
