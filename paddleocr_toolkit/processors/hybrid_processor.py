# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - 混合模式 PDF 處理器

本模組實作混合模式的核心邏輯：
- 使用 PP-StructureV3 進行版面分析
- 使用 PP-OCRv5 取得精確文字座標
- 生成閱讀順序正確的可搜尋 PDF
"""

import logging
import shutil
import tempfile
import traceback
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import fitz  # PyMuPDF
import numpy as np

from paddleocr_toolkit.utils.logger import logger

if TYPE_CHECKING:
    from paddleocr_toolkit.core import OCREngineManager

try:
    from tqdm import tqdm

    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

from paddleocr_toolkit.core import OCRResult, PDFGenerator
from paddleocr_toolkit.core.pdf_utils import pixmap_to_numpy
from paddleocr_toolkit.core.result_parser import OCRResultParser
from paddleocr_toolkit.processors.pdf_quality import detect_pdf_quality
from paddleocr_toolkit.processors.stats_collector import StatsCollector

# 條件匯入翻譯相關模組
try:
    from pdf_translator import TextInpainter

    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False
    TextInpainter = None


class HybridPDFProcessor:
    """
    混合模式 PDF 處理器

    結合 PP-StructureV3 版面分析與 PP-OCRv5 精確座標，
    生成閱讀順序正確的可搜尋 PDF。

    Attributes:
        engine_manager: OCR 引擎管理器
        result_parser: 結果解析器
        debug_mode: 除錯模式（粉紅色文字層）
        compress_images: 是否壓縮圖片
        jpeg_quality: JPEG 壓縮品質

    Example:
        >>> from paddleocr_toolkit.core import OCREngineManager
        >>> from paddleocr_toolkit.processors import HybridPDFProcessor
        >>>
        >>> engine = OCREngineManager(mode="hybrid")
        >>> engine.init_engine()
        >>> processor = HybridPDFProcessor(engine)
        >>> result = processor.process_pdf("input.pdf", "output.pdf")
    """

    def __init__(
        self,
        engine_manager: "OCREngineManager",
        debug_mode: bool = False,
        compress_images: bool = True,
        jpeg_quality: int = 85,
    ):
        """
        初始化混合模式處理器

        Args:
            engine_manager: OCR 引擎管理器（必須為 hybrid 模式）
            debug_mode: 是否啟用除錯模式（顯示粉紅色文字層）
            compress_images: 是否啟用圖片壓縮
            jpeg_quality: JPEG 壓縮品質 (0-100)

        Raises:
            ValueError: 當引擎不是 hybrid 模式時
        """
        if engine_manager.get_mode().value != "hybrid":
            raise ValueError(
                f"HybridPDFProcessor 需要 hybrid 模式引擎，當前: {engine_manager.get_mode().value}"
            )

        self.engine_manager = engine_manager
        self.result_parser = OCRResultParser()
        self.debug_mode = debug_mode
        self.compress_images = compress_images
        self.jpeg_quality = jpeg_quality

    def process_pdf(
        self,
        pdf_path: str,
        output_path: Optional[str] = None,
        markdown_output: Optional[str] = None,
        json_output: Optional[str] = None,
        html_output: Optional[str] = None,
        dpi: int = 150,
        show_progress: bool = True,
        translate_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        處理 PDF 的混合模式

        同時生成：
        1. *_hybrid.pdf（原文可搜尋）
        2. *_erased.pdf（擦除版 + 文字層）
        3. *_hybrid.md（Markdown）
        4. *_hybrid.json（JSON，可選）
        5. *_hybrid.html（HTML，可選）

        Args:
            pdf_path: 輸入 PDF 路徑
            output_path: 可搜尋 PDF 輸出路徑（可選）
            markdown_output: Markdown 輸出路徑（可選）
            json_output: JSON 輸出路徑（可選）
            html_output: HTML 輸出路徑（可選）
            dpi: PDF 轉圖片解析度
            show_progress: 是否顯示進度條
            translate_config: 翻譯配置（可選）

        Returns:
            Dict[str, Any]: 處理結果摘要
        """
        result_summary = {
            "input": pdf_path,
            "mode": "hybrid",
            "pages_processed": 0,
            "searchable_pdf": None,
            "markdown_file": None,
            "text_content": [],
            "error": None,
        }

        input_path_obj = Path(pdf_path)

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

            logger.info("Processing (hybrid mode): %s", pdf_path)
            logging.info(f"開始混合模式處理: {pdf_path}")

            # 自動偵測 PDF 品質並調整 DPI
            quality = detect_pdf_quality(pdf_path)
            logger.info("[Detection] %s", quality['reason'])
            if quality["is_scanned"] or quality["is_blurry"]:
                if quality["recommended_dpi"] > dpi:
                    dpi = quality["recommended_dpi"]
            logger.info("Using DPI: %d", dpi)

            return self._process_pdf_internal(
                pdf_path,
                output_path,
                markdown_output,
                json_output,
                html_output,
                dpi,
                show_progress,
                result_summary,
                translate_config=translate_config,
            )

        except Exception as e:
            error_msg = f"混合模式處理失敗: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            print(f"錯誤：{error_msg}")
            result_summary["error"] = str(e)
            return result_summary

    def _process_pdf_internal(
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
        """內部 PDF 處理邏輯"""

        # === 1. 初始化 ===
        pdf_doc = fitz.open(pdf_path)
        total_pages = len(pdf_doc)

        logger.info("PDF: %d pages", total_pages)
        logging.info(f"PDF 共 {total_pages} 頁")

        # 設定生成器
        pdf_gen, erased_gen, inpainter, erased_path = self._setup_generators(
            output_path
        )

        # 初始化收集器
        all_markdown = []
        all_text = []
        all_ocr_results = []  # 收集每頁 OCR 結果，用於翻譯

        # 初始化統計收集器
        stats_collector = StatsCollector(
            input_file=pdf_path, mode="hybrid", total_pages=total_pages
        )

        # === 2. 處理所有頁面 ===
        page_iterator = range(total_pages)
        if show_progress and HAS_TQDM:
            page_iterator = tqdm(page_iterator, desc="混合模式處理中", unit="頁", ncols=80)

        for page_num in page_iterator:
            try:
                stats_collector.start_page(page_num)
                page = pdf_doc[page_num]

                # 處理單頁
                page_md, page_txt, ocr_res = self._process_single_page(
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
            logger.info("[OK] Searchable PDF saved: %s", output_path)

        if erased_gen.save():
            result_summary["erased_pdf"] = erased_path
            logger.info("[OK] Erased PDF saved: %s", erased_path)

        # === 4. 儲存其他輸出 ===
        self._save_outputs(
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
        # 注意：翻譯功能需要 pdf_translator 套件
        # 如需使用，請安裝： pip install pdf-translator
        if translate_config and HAS_TRANSLATOR:
            if self.debug_mode:
                logging.info("偵錯模式已啟用，跳過翻譯處理")
            else:
                logging.info("翻譯功能已配置，但需手動整合 TranslationProcessor")

        # === 6. 完成統計 ===
        logger.info("[OK] Hybrid mode processing complete: %d pages", result_summary['pages_processed'])

        final_stats = stats_collector.finish()
        final_stats.print_summary()
        result_summary["stats"] = final_stats.to_dict()

        return result_summary

    def _setup_generators(
        self, output_path: str
    ) -> Tuple[PDFGenerator, PDFGenerator, Optional[Any], str]:
        """設定混合模式所需的生成器"""
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
            f"[DEBUG] PDFGenerator compress_images={pdf_generator.compress_images}, "
            f"jpeg_quality={pdf_generator.jpeg_quality}"
        )

        return pdf_generator, erased_generator, inpainter, erased_output_path

    def _process_single_page(
        self,
        page,
        page_num: int,
        dpi: int,
        pdf_generator: PDFGenerator,
        erased_generator: PDFGenerator,
        inpainter: Optional[Any],
    ) -> Tuple[str, str, List[OCRResult]]:
        """
        處理單一頁面（混合模式）

        Args:
            page: PyMuPDF 頁面物件
            page_num: 頁碼（0-based）
            dpi: 解析度
            pdf_generator: PDF 生成器
            erased_generator: 擦除版生成器
            inpainter: 文字擦除器

        Returns:
            Tuple[str, str, List[OCRResult]]: (Markdown, 純文字, OCR結果)
        """
        # 1. 轉換頁面為圖片
        pixmap = page.get_pixmap(dpi=dpi)
        img_array = pixmap_to_numpy(pixmap)

        # 2. 執行 OCR（混合模式使用 structure 引擎）
        structure_output = self.engine_manager.predict(img_array)

        # 3. 提取並合併結果
        ocr_results, page_markdown = self._extract_and_merge_results(
            structure_output, page_num
        )

        # 4. 生成雙 PDF（原文 + 擦除版）
        self._generate_dual_pdfs(
            pixmap, img_array, ocr_results, pdf_generator, erased_generator, inpainter
        )

        # 5. 提取純文字
        page_text = "\n".join([r.text for r in ocr_results])

        return page_markdown, page_text, ocr_results

    def _extract_and_merge_results(
        self, structure_output, page_num: int
    ) -> Tuple[List[OCRResult], str]:
        """
        從 PP-StructureV3 輸出提取並合併結果

        Args:
            structure_output: Structure 引擎輸出
            page_num: 頁碼（0-based）

        Returns:
            Tuple[List[OCRResult], str]: OCR 結果與 Markdown
        """
        # 使用 ResultParser 解析結果
        ocr_results = self.result_parser.parse_structure_result(structure_output)

        # 提取 Markdown
        markdown_parts = []
        try:
            for res in structure_output:
                md_content = self._extract_markdown_from_result(res)
                if md_content:
                    markdown_parts.append(md_content)
        except Exception as e:
            logging.warning(f"提取 Markdown 時發生錯誤: {e}")

        # 組合 Markdown
        if markdown_parts:
            page_markdown = f"## 第 {page_num + 1} 頁\n\n" + "\n\n".join(markdown_parts)
        else:
            # 使用 OCR 文字生成 Markdown
            page_markdown = f"## 第 {page_num + 1} 頁\n\n" + "\n\n".join(
                [r.text for r in ocr_results]
            )

        return ocr_results, page_markdown

    def _extract_markdown_from_result(self, res) -> Optional[str]:
        """從單個 Structure 結果提取 Markdown"""
        # 方法 1: 使用 save_to_markdown
        temp_md_dir = tempfile.mkdtemp()
        try:
            if hasattr(res, "save_to_markdown"):
                res.save_to_markdown(save_path=temp_md_dir)
                for md_file in Path(temp_md_dir).glob("*.md"):
                    with open(md_file, "r", encoding="utf-8") as f:
                        return f.read()
        except Exception:
            pass
        finally:
            shutil.rmtree(temp_md_dir, ignore_errors=True)

        # 方法 2: 使用 markdown 屬性
        if hasattr(res, "markdown") and isinstance(res.markdown, str):
            return res.markdown

        return None

    def _generate_dual_pdfs(
        self,
        pixmap,
        img_array: np.ndarray,
        ocr_results: List[OCRResult],
        pdf_generator: PDFGenerator,
        erased_generator: PDFGenerator,
        inpainter: Optional[Any],
    ) -> None:
        """生成原文 PDF 和擦除版 PDF"""
        # 1. 生成原文可搜尋 PDF
        pdf_generator.add_page_from_pixmap(pixmap, ocr_results)

        # 2. 生成擦除版 PDF（如果有 inpainter）
        if inpainter and HAS_TRANSLATOR:
            try:
                erased_image = inpainter.inpaint_text_regions(
                    img_array, [r.bbox for r in ocr_results]
                )
                erased_generator.add_page_from_array(erased_image, ocr_results)
            except Exception as e:
                logging.warning(f"文字擦除失敗: {e}")
                erased_generator.add_page_from_pixmap(pixmap, ocr_results)
        else:
            erased_generator.add_page_from_pixmap(pixmap, ocr_results)

    def _save_outputs(
        self,
        all_markdown: List[str],
        all_ocr_results: List[List[OCRResult]],
        markdown_output: Optional[str],
        json_output: Optional[str],
        html_output: Optional[str],
        pdf_path: str,
        result_summary: Dict[str, Any],
    ) -> None:
        """儲存 Markdown、JSON、HTML 輸出"""
        # 儲存 Markdown
        if markdown_output:
            combined_markdown = "\n\n".join(all_markdown)
            with open(markdown_output, "w", encoding="utf-8") as f:
                f.write(combined_markdown)
            result_summary["markdown_file"] = markdown_output
            logger.info("[OK] Markdown saved: %s", markdown_output)

        # 儲存 JSON
        if json_output:
            import json
            try:
                # 將 OCR 結果轉換為可序列化格式
                json_data = {
                    "source": pdf_path,
                    "total_pages": len(all_ocr_results),
                    "pages": [
                        {
                            "page_num": i + 1,
                            "text_blocks": [
                                {
                                    "text": result.text,
                                    "bbox": result.bbox,
                                    "confidence": getattr(result, 'confidence', 1.0)
                                }
                                for result in page_results
                            ]
                        }
                        for i, page_results in enumerate(all_ocr_results)
                    ]
                }
                
                with open(json_output, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                result_summary["json_file"] = json_output
                logger.info("[OK] JSON saved: %s", json_output)
            except Exception as e:
                logging.error(f"JSON 輸出失敗: {e}")

        # 儲存 HTML
        if html_output:
            try:
                # 建立簡單的 HTML 輸出
                html_content = [
                    "<!DOCTYPE html>",
                    '<html lang="zh-TW">',
                    "<head>",
                    '    <meta charset="UTF-8">',
                    '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
                    f"    <title>OCR 結果 - {Path(pdf_path).name}</title>",
                    "    <style>",
                    "        body { font-family: 'Microsoft JhengHei', sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; line-height: 1.8; }",
                    "        h1 { color: #333; border-bottom: 3px solid #4f46e5; padding-bottom: 10px; }",
                    "        h2 { color: #4f46e5; margin-top: 40px; border-left: 4px solid #4f46e5; padding-left: 15px; }",
                    "        .page { margin-bottom: 40px; padding: 20px; background: #f9fafb; border-radius: 8px; }",
                    "        .text-block { margin: 10px 0; padding: 10px; background: white; border-radius: 4px; }",
                    "    </style>",
                    "</head>",
                    "<body>",
                    f"    <h1>OCR 識別結果: {Path(pdf_path).name}</h1>",
                ]
                
                # 加入每頁內容
                for i, markdown in enumerate(all_markdown):
                    html_content.append(f'    <div class="page">')
                    html_content.append(f"        <h2>第 {i + 1} 頁</h2>")
                    
                    # 將 Markdown 轉換為 HTML (簡單處理)
                    lines = markdown.split(

"\n")
                    for line in lines:
                        if line.strip():
                            html_content.append(f'        <div class="text-block">{line}</div>')
                    
                    html_content.append("    </div>")
                
                html_content.extend([
                    "</body>",
                    "</html>"
                ])
                
                with open(html_output, "w", encoding="utf-8") as f:
                    f.write("\n".join(html_content))
                result_summary["html_file"] = html_output
                logger.info("[OK] HTML saved: %s", html_output)
            except Exception as e:
                logging.error(f"HTML 輸出失敗: {e}")
