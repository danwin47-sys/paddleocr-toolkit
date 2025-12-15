# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - 模式处理器

处理不同 OCR 模式的执行和结果显示。
"""

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from paddle_ocr_tool import PaddleOCRTool

# 需要从 paddle_ocr_tool.py 导入的常量
SUPPORTED_PDF_FORMAT = ".pdf"
SUPPORTED_IMAGE_FORMATS = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp")


class ModeProcessor:
    """处理不同 OCR 模式的执行和结果显示

    封装了 formula、structure、vl、hybrid、basic 五种模式的处理逻辑。
    """

    def __init__(
        self,
        tool: "PaddleOCRTool",
        args: argparse.Namespace,
        input_path: Path,
        script_dir: Path,
    ):
        """初始化模式处理器

        Args:
            tool: PaddleOCRTool 实例
            args: 命令列参数
            input_path: 输入文件路径
            script_dir: 脚本所在目录
        """
        self.tool = tool
        self.args = args
        self.input_path = input_path
        self.script_dir = script_dir
        self.show_progress = not args.no_progress

    def process(self) -> Dict[str, Any]:
        """根据模式执行处理

        Returns:
            Dict[str, Any]: 处理结果
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
        """处理 formula 模式

        Returns:
            Dict[str, Any]: 处理结果
        """
        result = self.tool.process_formula(
            input_path=str(self.input_path), latex_output=self.args.latex_output
        )

        if result.get("error"):
            print(f"处理过程中发生错误: {result['error']}")
        else:
            print(f"\n[OK] 公式识别完成！共识别 {len(result['formulas'])} 个公式")
            if result.get("latex_file"):
                print(f"  LaTeX 文件: {result['latex_file']}")

        return result

    def _process_structured(self) -> Dict[str, Any]:
        """处理 structure/vl 模式

        Returns:
            Dict[str, Any]: 处理结果
        """
        result = self.tool.process_structured(
            input_path=str(self.input_path),
            markdown_output=self.args.markdown_output,
            json_output=self.args.json_output,
            excel_output=self.args.excel_output,
            html_output=self.args.html_output,
        )

        if result.get("error"):
            print(f"处理过程中发生错误: {result['error']}")
        else:
            print(f"\n[OK] 处理完成！共处理 {result['pages_processed']} 页")
            if result.get("markdown_files"):
                print(f"  Markdown 文件: {', '.join(result['markdown_files'])}")
            if result.get("json_files"):
                print(f"  JSON 文件: {', '.join(result['json_files'])}")
            if result.get("excel_files"):
                print(f"  Excel 文件: {', '.join(result['excel_files'])}")
            if result.get("html_files"):
                print(f"  HTML 文件: {', '.join(result['html_files'])}")

        return result

    def _process_hybrid(self) -> Dict[str, Any]:
        """处理 hybrid 模式

        Returns:
            Dict[str, Any]: 处理结果
        """
        # 检查是否启用翻译功能
        if hasattr(self.args, "translate") and self.args.translate:
            return self._process_hybrid_with_translation()
        else:
            return self._process_hybrid_normal()

    def _process_hybrid_with_translation(self) -> Dict[str, Any]:
        """处理 hybrid 模式 + 翻译

        Returns:
            Dict[str, Any]: 处理结果
        """
        # 检查翻译模块
        from paddle_ocr_tool import HAS_TRANSLATOR

        if not HAS_TRANSLATOR:
            print("错误：翻译模块不可用")
            print("请确认 pdf_translator.py 存在且依赖已安装")
            sys.exit(1)

        print(f"[翻译功能] 启用")
        print(f"   来源语言：{self.args.source_lang}")
        print(f"   目标语言：{self.args.target_lang}")
        print(f"   Ollama 模型：{self.args.ollama_model}")
        print(f"   纯翻译 PDF：{'停用' if self.args.no_mono else '启用'}")
        print(
            f"   双语对照 PDF：{'停用' if self.args.no_dual else f'启用 ({self.args.dual_mode})'}"
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
            print(f"处理过程中发生错误: {result['error']}")
        else:
            print(f"\n[OK] 翻译处理完成！共处理 {result['pages_processed']} 页")
            if result.get("searchable_pdf"):
                print(f"  [可搜寻 PDF] {result['searchable_pdf']}")
            if result.get("markdown_file"):
                print(f"  [Markdown] {result['markdown_file']}")
            if result.get("json_file"):
                print(f"  [JSON] {result['json_file']}")
            if result.get("html_file"):
                print(f"  [HTML] {result['html_file']}")
            if result.get("translated_pdf"):
                print(f"  [翻译PDF] {result['translated_pdf']}")
            if result.get("bilingual_pdf"):
                print(f"  [双语PDF] {result['bilingual_pdf']}")

        return result

    def _process_hybrid_normal(self) -> Dict[str, Any]:
        """处理普通 hybrid 模式（无翻译）

        Returns:
            Dict[str, Any]: 处理结果
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
            print(f"处理过程中发生错误: {result['error']}")
        else:
            print(f"\n[OK] 混合模式处理完成！共处理 {result['pages_processed']} 页")
            if result.get("searchable_pdf"):
                print(f"  可搜寻 PDF: {result['searchable_pdf']}")
            if result.get("markdown_file"):
                print(f"  Markdown 文件: {result['markdown_file']}")

        return result

    def _process_basic(self) -> Dict[str, Any]:
        """处理 basic 模式

        Returns:
            Dict[str, Any]: 处理结果
        """
        all_text = []

        # 处理输入
        if self.input_path.is_dir():
            # 目录处理
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
            # PDF 处理
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
                    all_text.append(f"=== 第 {page_num} 页 ===\n{text}")

        elif self.input_path.suffix.lower() in SUPPORTED_IMAGE_FORMATS:
            # 图片处理
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
            print(f"错误：不支持的文件格式: {self.input_path.suffix}")
            sys.exit(1)

        # 输出结果
        combined_text = "\n\n".join(all_text)

        if self.args.text_output:
            # 如果输出路径不是绝对路径，则相对于脚本目录
            text_output_path = Path(self.args.text_output)
            if not text_output_path.is_absolute():
                text_output_path = self.script_dir / text_output_path

            # 保存到文件
            with open(text_output_path, "w", encoding="utf-8") as f:
                f.write(combined_text)
            print(f"[OK] 文字已保存：{text_output_path}")

        # 如果两个输出都停用，则输出到终端
        if not self.args.text_output and not self.args.searchable and combined_text:
            print("\n" + "=" * 50)
            print("OCR 识别结果：")
            print("=" * 50)
            print(combined_text)

        print("\n[OK] 处理完成！")

        return {"status": "success", "text": combined_text}
