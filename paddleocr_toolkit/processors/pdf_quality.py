# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - PDF 品質偵測

自動判斷 PDF 是否為掃描件並建議適合的 DPI。
"""

import logging

try:
    import fitz

    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False


def detect_pdf_quality(pdf_path: str) -> dict:
    """
    偵測 PDF 品質，判斷是否為掃描件或模糊檔案

    Args:
        pdf_path: PDF 檔案路徑

    Returns:
        dict: {
            'is_scanned': bool,      # 是否為掃描件
            'is_blurry': bool,       # 是否模糊
            'has_text': bool,        # 是否有可提取的文字
            'recommended_dpi': int,  # 建議的 DPI
            'reason': str            # 判斷原因
        }
    """
    if not HAS_FITZ:
        return {
            "is_scanned": False,
            "is_blurry": False,
            "has_text": False,
            "recommended_dpi": 150,
            "reason": "PyMuPDF 未安裝",
        }

    try:
        result = {
            "is_scanned": False,
            "is_blurry": False,
            "has_text": False,
            "recommended_dpi": 150,
            "reason": "",
        }

        pdf_doc = fitz.open(pdf_path)

        if len(pdf_doc) == 0:
            result["reason"] = "PDF 無頁面"
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
            result["is_scanned"] = True
            result["recommended_dpi"] = 300
            result[
                "reason"
            ] = f"偵測為掃描件（平均每頁 {avg_text_per_page:.0f} 字元，{avg_images_per_page:.1f} 張圖片）"

        # 如果有少量文字，可能是部分掃描
        elif avg_text_per_page < 200 and avg_images_per_page >= 1:
            result["is_scanned"] = True
            result["is_blurry"] = True
            result["recommended_dpi"] = 200
            result["reason"] = f"偵測為部分掃描檔案（平均每頁 {avg_text_per_page:.0f} 字元）"

        # 有足夠文字，是一般 PDF
        else:
            result["has_text"] = True
            result["recommended_dpi"] = 150
            result["reason"] = f"偵測為一般 PDF（平均每頁 {avg_text_per_page:.0f} 字元）"

        return result

    except Exception as e:
        logging.warning(f"PDF 品質偵測失敗: {e}")
        return {
            "is_scanned": False,
            "is_blurry": False,
            "has_text": False,
            "recommended_dpi": 150,
            "reason": f"偵測失敗: {e}",
        }
