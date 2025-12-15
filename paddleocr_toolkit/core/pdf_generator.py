# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - PDF 生成器

使用 Umi-OCR 邏輯建立雙層可搜尋 PDF。
"""

import logging
from typing import List

try:
    import fitz

    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    from PIL import Image

    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from .models import OCRResult


class PDFGenerator:
    """
    PDF 生成器 - 使用 Umi-OCR 邏輯建立雙層可搜尋 PDF

    透過 PyMuPDF 在原始圖片上疊加透明文字層，
    使 PDF 可搜尋、可選取文字，同時保持原始視覺外觀。
    """

    def __init__(
        self,
        output_path: str,
        debug_mode: bool = False,
        compress_images: bool = False,
        jpeg_quality: int = 85,
    ):
        """
        初始化 PDF 生成器

        Args:
            output_path: 輸出 PDF 的檔案路徑
            debug_mode: 如果為 True，文字會顯示為粉紅色（方便調試）
            compress_images: 如果為 True，使用 JPEG 壓縮圖片以減少檔案大小
            jpeg_quality: JPEG 壓縮品質（0-100，預設 85）
        """
        if not HAS_FITZ:
            raise ImportError("PyMuPDF (fitz) 未安裝，請執行: pip install pymupdf")

        self.output_path = output_path
        self.doc = fitz.open()  # 建立新的空白 PDF
        self.page_count = 0
        self.debug_mode = debug_mode
        self.compress_images = compress_images
        self.jpeg_quality = max(0, min(100, jpeg_quality))

    def add_page(self, image_path: str, ocr_results: List[OCRResult]) -> bool:
        """
        新增一頁到 PDF

        Args:
            image_path: 原始圖片路徑
            ocr_results: OCR 辨識結果列表

        Returns:
            bool: 是否成功新增頁面
        """
        if not HAS_PIL:
            print("警告：Pillow 未安裝")
            return False

        try:
            # 開啟圖片以取得尺寸
            img = Image.open(image_path)
            img_width, img_height = img.size

            # 建立新頁面，尺寸與圖片相同
            page = self.doc.new_page(width=img_width, height=img_height)

            # 插入圖片作為背景
            rect = fitz.Rect(0, 0, img_width, img_height)

            if self.compress_images:
                # 使用 JPEG 壓縮以減少檔案大小
                import io

                # 確保是 RGB 模式
                if img.mode != "RGB":
                    img = img.convert("RGB")
                # 儲存為 JPEG 到記憶體緩衝區
                jpeg_buffer = io.BytesIO()
                img.save(
                    jpeg_buffer, format="JPEG", quality=self.jpeg_quality, optimize=True
                )
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

    def add_page_from_pixmap(self, pixmap, ocr_results: List[OCRResult]) -> bool:
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
            page = self.doc.new_page(width=img_width, height=img_height)

            # 插入 pixmap 作為背景
            rect = fitz.Rect(0, 0, img_width, img_height)

            if self.compress_images:
                # 使用 JPEG 壓縮以減少檔案大小
                import io

                # 將 pixmap 轉換為 PIL Image
                # 注意：這裡假設 pixmap 已經是 RGB 模式 (alpha=False)
                pil_image = Image.frombytes(
                    "RGB", [pixmap.width, pixmap.height], pixmap.samples
                )

                # 儲存為 JPEG 到記憶體緩衝區
                jpeg_buffer = io.BytesIO()
                pil_image.save(
                    jpeg_buffer, format="JPEG", quality=self.jpeg_quality, optimize=True
                )
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

    def _insert_invisible_text(self, page, result: OCRResult) -> None:
        """
        在頁面上插入透明文字

        使用 PDF 渲染模式 3（隱形）來確保文字不可見但可選取/搜尋

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
                    # 先用高度估算初始字體大小
                    initial_size = height * 0.7
                    if initial_size < 4:
                        initial_size = 4
                    if initial_size > 100:
                        initial_size = 100

                    # 計算文字在此字體大小下的寬度
                    text_width = fitz.get_text_length(
                        text, fontname=fontname, fontsize=initial_size
                    )

                    if text_width > 0 and width > 0:
                        # 計算寬度比例並調整字體大小
                        width_ratio = width / text_width
                        adjusted_size = initial_size * width_ratio

                        # 限制不能超過高度的 90%
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
                        break
                    else:
                        best_font = fontname
                        best_font_size = initial_size
                        break

                except Exception:
                    continue

            # 計算文字基線位置
            baseline_offset = best_font_size * 0.2
            baseline_y = y + height - baseline_offset

            if baseline_y < y + best_font_size * 0.8:
                baseline_y = y + best_font_size * 0.8
            if baseline_y > y + height:
                baseline_y = y + height

            # 根據 debug_mode 設定文字樣式
            if self.debug_mode:
                render_mode = 0  # 可見模式
                text_color = (1, 0.4, 0.6)  # 粉紅色
            else:
                render_mode = 3  # 隱形模式
                text_color = (0, 0, 0)

            # 插入文字
            try:
                page.insert_text(
                    fitz.Point(x, baseline_y),
                    text,
                    fontsize=best_font_size,
                    fontname=best_font,
                    render_mode=render_mode,
                    color=text_color,
                )
            except Exception as e:
                # 嘗試其他字體
                for fontname in fonts_to_try:
                    if fontname != best_font:
                        try:
                            page.insert_text(
                                fitz.Point(x, baseline_y),
                                text,
                                fontsize=best_font_size,
                                fontname=fontname,
                                render_mode=render_mode,
                                color=text_color,
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
