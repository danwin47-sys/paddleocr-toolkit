# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - 模式處理器

處理不同 OCR 模式的執行和結果顯示。
"""

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from paddle_ocr_tool import PaddleOCRTool

# 需要從 paddle_ocr_tool.py 匯入的常量
SUPPORTED_PDF_FORMAT = ".pdf"
SUPPORTED_IMAGE_FORMATS = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp")


class ModeProcessor:
    """處理不同 OCR 模式的執行和結果顯示

    封裝了 formula、structure、vl、hybrid、basic 五種模式的處理邏輯。
    """

    def __init__(
        self,
        tool: "PaddleOCRTool",
        args: argparse.Namespace,
        input_path: Path,
        script_dir: Path,
    ):
        """初始化模式處理器

        Args:
            tool: PaddleOCRTool 例項
            args: 命令列引數
            input_path: 輸入檔案路徑
            script_dir: 指令碼所在目錄
        """
        self.tool = tool
        self.args = args
        self.input_path = input_path
        self.script_dir = script_dir
        self.show_progress = not args.no_progress

    def process(self) -> Dict[str, Any]:
        """根據模式執行處理

        Returns:
            Dict[str, Any]: 處理結果
        """
        if self.args.mode == "formula":
            return self._process_formula()
        elif self.args.mode in ["structure", "vl"]:
            return self._process_structured()
        elif self.args.mode == "hybrid":
            return self._process_hybrid()
        else:  # basic
            return self._process_basic()

    def _process_formula(self) -> Dict[str, Any]:
        """處理 formula 模式

        Returns:
            Dict[str, Any]: 處理結果
        """處理 formula 模式

        Returns:
            Dict[str, Any]: 處理結果
        """
        result = self.tool.process_formula(
            input_path=str(self.input_path), latex_output=self.args.latex_output
        )

        if result.get("error"):
            print(f"處理過程中發生錯誤: {result['error']}")
            return result # Keep original return behavior for error case
        print(f"\n[OK] 公式識別完成！共識別 {len(result['formulas'])} 個公式")
        if result.get("latex_file"):
            print(f"  LaTeX 檔案: {result['latex_file']}")

        return result

    def _process_structured(self) -> Dict[str, Any]:
        """處理 structure/vl 模式

        Returns:
            Dict[str, Any]: 處理結果
        """
        result = self.tool.process_structured(
            input_path=str(self.input_path),
            markdown_output=self.args.markdown_output,
            json_output=self.args.json_output,
            excel_output=self.args.excel_output,
            html_output=self.args.html_output,
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

        return result

    def _process_hybrid(self) -> Dict[str, Any]:
        """處理 hybrid 模式

        Returns:
            Dict[str, Any]: 處理結果
        """
        # 檢查是否啟用翻譯功能
        if hasattr(self.args, "translate") and self.args.translate:
            return self._process_hybrid_with_translation()
        else:
            return self._process_hybrid_normal()

    def _process_hybrid_with_translation(self) -> Dict[str, Any]:
        """處理 hybrid 模式 + 翻譯

        Returns:
            Dict[str, Any]: 處理結果
        """
        # 檢查翻譯模組
        from paddle_ocr_tool import HAS_TRANSLATOR

        if not HAS_TRANSLATOR:
            print("錯誤：翻譯模組不可用")
            print("請確認 pdf_translator.py 存在且依賴已安裝")
            sys.exit(1)

        print(f"[翻譯功能] 啟用")
        print(f"   來源語言：{self.args.source_lang}")
        print(f"   目標語言：{self.args.target_lang}")
        print(f"   使用翻譯引擎：{self.args.trans_tool}")
        print(f"   Ollama 模型：{self.args.ollama_model}")
        print(f"   純翻譯 PDF：{'停用' if self.args.no_mono else '啟用'}")
        print(
            f"   雙語對照 PDF：{'停用' if self.args.no_dual else f'啟用 ({self.args.dual_mode})'}"
        )

        result = self.tool.process_translate(
            input_path=str(self.input_path),
            output_path=self.args.output,
            source_lang=self.args.source_lang,
            target_lang=self.args.target_lang,
            ollama_model=self.args.ollama_model,
            ollama_url=self.args.ollama_url,
            no_mono=self.args.no_mono,
            no_dual=self.args.no_dual,
            dual_mode=self.args.dual_mode,
            dual_translate_first=self.args.dual_translate_first,
            font_path=self.args.font_path,
            dpi=self.args.dpi,
            show_progress=self.show_progress,
            json_output=self.args.json_output,
            html_output=self.args.html_output,
            ocr_workaround=self.args.ocr_workaround,
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

        return result

    def _process_hybrid_normal(self) -> Dict[str, Any]:
        """處理普通 hybrid 模式（無翻譯）

        Returns:
            Dict[str, Any]: 處理結果
        """
        result = self.tool.process_hybrid(
            input_path=str(self.input_path),
            output_path=self.args.output,
            markdown_output=self.args.markdown_output,
            json_output=self.args.json_output,
            html_output=self.args.html_output,
            dpi=self.args.dpi,
            show_progress=self.show_progress,
        )

        if result.get("error"):
            print(f"處理過程中發生錯誤: {result['error']}")
        else:
            print(f"\n[OK] 混合模式處理完成！共處理 {result['pages_processed']} 頁")
            if result.get("searchable_pdf"):
                print(f"  可搜尋 PDF: {result['searchable_pdf']}")
            if result.get("markdown_file"):
                print(f"  Markdown 檔案: {result['markdown_file']}")

        return result

    def _process_basic(self) -> Dict[str, Any]:
        """處理 basic 模式

        Returns:
            Dict[str, Any]: 處理結果
        """
        all_text = []

        # 處理輸入
        if self.input_path.is_dir():
            # 目錄處理
            results = self.tool.process_directory(
                str(self.input_path),
                output_path=self.args.output,
                searchable=self.args.searchable,
                recursive=self.args.recursive,
            )

            for file_path, file_results in results.items():
                text = self.tool.get_text(file_results)
                if text:
                    all_text.append(f"=== {file_path} ===\n{text}")

        elif self.input_path.suffix.lower() == SUPPORTED_PDF_FORMAT:
            # PDF 處理
            results, output_path = self.tool.process_pdf(
                str(self.input_path),
                output_path=self.args.output,
                searchable=self.args.searchable,
                dpi=self.args.dpi,
                show_progress=self.show_progress,
            )

            for page_num, page_results in enumerate(results, 1):
                text = self.tool.get_text(page_results)
                if text:
                    all_text.append(f"=== 第 {page_num} 頁 ===\n{text}")

        elif self.input_path.suffix.lower() in SUPPORTED_IMAGE_FORMATS:
            # 圖片處理
            from paddleocr_toolkit.core import PDFGenerator

            results = self.tool.process_image(str(self.input_path))

            if self.args.searchable:
                output_path = self.args.output or str(
                    self.input_path.with_suffix(".pdf")
                )
                pdf_generator = PDFGenerator(
                    output_path, debug_mode=self.args.debug_text
                )
                pdf_generator.add_page(str(self.input_path), results)
                pdf_generator.save()

            text = self.tool.get_text(results)
            if text:
                all_text.append(text)

        else:
            print(f"錯誤：不支援的檔案格式: {self.input_path.suffix}")
            sys.exit(1)

        # 輸出結果
        combined_text = "\n\n".join(all_text)

        if self.args.text_output:
            # 如果輸出路徑不是絕對路徑，則相對於指令碼目錄
            text_output_path = Path(self.args.text_output)
            if not text_output_path.is_absolute():
                text_output_path = self.script_dir / text_output_path

            # 儲存到檔案
            with open(text_output_path, "w", encoding="utf-8") as f:
                f.write(combined_text) # Changed all_text to combined_text for correct output
            print(f"[OK] 文字已儲存：{text_output_path}")

        # 如果兩個輸出都停用，則輸出到終端
        if not self.args.text_output and not self.args.searchable and combined_text:
            print("\n" + "=" * 50)
            print("OCR 辨識結果：")
            print("=" * 50)
            print(combined_text)

        print("\n[OK] 處理完成！")

        return {"status": "success", "text": combined_text}
