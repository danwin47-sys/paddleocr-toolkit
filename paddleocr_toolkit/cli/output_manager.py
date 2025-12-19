# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - 輸出路徑管理器

管理各種輸出檔案的路徑生成。
"""

import argparse
from pathlib import Path
from typing import Optional


class OutputPathManager:
    """輸出路徑管理器

    負責根據輸入檔案和模式產生各種輸出檔案的路徑。
    """

    def __init__(self, input_path: str, mode: str = "basic"):
        """初始化輸出路徑管理器

        Args:
            input_path: 輸入檔案路徑
            mode: OCR 模式
        """
        self.input_path = Path(input_path)
        self.mode = mode
        self.base_name = self.input_path.stem
        self.parent_dir = self.input_path.parent

    def get_searchable_pdf_path(self, custom_output: Optional[str] = None) -> str:
        """取得可搜尋 PDF 路徑

        Args:
            custom_output: 自訂輸出路徑（可選）

        Returns:
            str: 輸出檔案路徑
        """
        if custom_output:
            return custom_output
        return str(self.parent_dir / f"{self.base_name}_searchable.pdf")

    def get_text_output_path(
        self, custom_output: Optional[str] = None
    ) -> Optional[str]:
        """取得文字輸出路徑

        Args:
            custom_output: 自訂輸出路徑（'AUTO' 或實際路徑）

        Returns:
            str or None: 輸出檔案路徑，'AUTO' 時返回預設路徑，None 表示不輸出
        """
        if custom_output == "AUTO":
            return str(self.parent_dir / f"{self.base_name}_ocr.txt")
        return custom_output

    def get_markdown_output_path(
        self, custom_output: Optional[str] = None
    ) -> Optional[str]:
        """取得 Markdown 輸出路徑

        Args:
            custom_output: 自訂輸出路徑（'AUTO' 或實際路徑）

        Returns:
            Optional[str]: 輸出檔案路徑，'AUTO' 時返回預設路徑
        """
        if custom_output == "AUTO":
            return str(self.parent_dir / f"{self.base_name}_{self.mode}.md")
        return custom_output

    def get_json_output_path(
        self, custom_output: Optional[str] = None
    ) -> Optional[str]:
        """取得 JSON 輸出路徑

        Args:
            custom_output: 自訂輸出路徑（'AUTO' 或實際路徑）

        Returns:
            Optional[str]: 輸出檔案路徑，'AUTO' 時返回預設路徑
        """
        if custom_output == "AUTO":
            return str(self.parent_dir / f"{self.base_name}_{self.mode}.json")
        return custom_output

    def get_html_output_path(
        self, custom_output: Optional[str] = None
    ) -> Optional[str]:
        """取得 HTML 輸出路徑

        Args:
            custom_output: 自訂輸出路徑（'AUTO' 或實際路徑）

        Returns:
            Optional[str]: 輸出檔案路徑，'AUTO' 時返回預設路徑
        """
        if custom_output == "AUTO":
            return str(self.parent_dir / f"{self.base_name}_{self.mode}.html")
        return custom_output

    def get_excel_output_path(
        self, custom_output: Optional[str] = None
    ) -> Optional[str]:
        """取得 Excel 輸出路徑

        Args:
            custom_output: 自訂輸出路徑（'AUTO' 或實際路徑）

        Returns:
            Optional[str]: 輸出檔案路徑，'AUTO' 時返回預設路徑
        """
        if custom_output == "AUTO":
            return str(self.parent_dir / f"{self.base_name}_tables.xlsx")
        return custom_output

    def get_latex_output_path(
        self, custom_output: Optional[str] = None
    ) -> Optional[str]:
        """取得 LaTeX 輸出路徑

        Args:
            custom_output: 自訂輸出路徑（'AUTO' 或實際路徑）

        Returns:
            Optional[str]: 輸出檔案路徑，'AUTO' 時返回預設路徑
        """
        if custom_output == "AUTO":
            return str(self.parent_dir / f"{self.base_name}_formula.tex")
        return custom_output

    def process_mode_outputs(
        self, args: argparse.Namespace, script_dir: Path
    ) -> argparse.Namespace:
        """根據 OCR 模式處理所有輸出路徑設定

        Args:
            args: 命令列引數
            script_dir: 指令碼所在目錄

        Returns:
            argparse.Namespace: 更新後的引數
        """
        # 根據模式設定預設輸出路徑
        if self.mode == "basic":
            args = self._process_basic_mode_outputs(args, script_dir)
        elif self.mode == "formula":
            args = self._process_formula_mode_outputs(args, script_dir)
        elif self.mode == "hybrid":
            args = self._process_hybrid_mode_outputs(args, script_dir)
        else:  # structure/vl
            args = self._process_structure_mode_outputs(args, script_dir)

        return args

    def _process_basic_mode_outputs(
        self, args: argparse.Namespace, script_dir: Path
    ) -> argparse.Namespace:
        """處理 basic 模式的輸出設定"""
        # basic 模式：處理 text_output 和 searchable
        if args.text_output == "AUTO":
            args.text_output = str(script_dir / f"{self.base_name}_ocr.txt")

        # 忽略其他模式專用的輸出
        args.markdown_output = None
        args.json_output = None
        args.excel_output = None
        args.latex_output = None

        return args

    def _process_formula_mode_outputs(
        self, args: argparse.Namespace, script_dir: Path
    ) -> argparse.Namespace:
        """處理 formula 模式的輸出設定"""
        # formula 模式：處理 latex_output
        if args.latex_output == "AUTO":
            args.latex_output = str(script_dir / f"{self.base_name}_formula.tex")

        # 忽略其他模式專用的輸出
        args.searchable = False
        args.text_output = None
        args.markdown_output = None
        args.json_output = None
        args.excel_output = None

        return args

    def _process_hybrid_mode_outputs(
        self, args: argparse.Namespace, script_dir: Path
    ) -> argparse.Namespace:
        """處理 hybrid 模式的輸出設定"""
        # hybrid 模式：處理 searchable、markdown_output、json_output、html_output
        if args.markdown_output == "AUTO":
            args.markdown_output = str(script_dir / f"{self.base_name}_hybrid.md")
        if args.json_output == "AUTO":
            args.json_output = str(script_dir / f"{self.base_name}_hybrid.json")
        if args.html_output == "AUTO":
            args.html_output = str(script_dir / f"{self.base_name}_hybrid.html")

        # hybrid 模式會自動生成可搜尋 PDF
        args.searchable = True
        args.text_output = None
        args.excel_output = None
        args.latex_output = None

        return args

    def _process_structure_mode_outputs(
        self, args: argparse.Namespace, script_dir: Path
    ) -> argparse.Namespace:
        """處理 structure/vl 模式的輸出設定"""
        # structure/vl 模式：處理 markdown_output、json_output、excel_output 和 html_output
        if args.markdown_output == "AUTO":
            args.markdown_output = str(script_dir / f"{self.base_name}_ocr.md")
        if args.json_output == "AUTO":
            args.json_output = str(script_dir / f"{self.base_name}_ocr.json")
        if args.excel_output == "AUTO":
            args.excel_output = str(script_dir / f"{self.base_name}_tables.xlsx")
        if args.html_output == "AUTO":
            args.html_output = str(script_dir / f"{self.base_name}_ocr.html")

        # 忽略 basic 專用的輸出
        args.searchable = False
        args.text_output = None
        args.latex_output = None

        return args

    def print_output_summary(self, args: argparse.Namespace) -> None:
        """顯示輸出設定摘要

        Args:
            args: 命令列引數
        """
        print(f"\n[輸入] {self.input_path}")
        print(f"[模式] {self.mode}")

        if self.mode == "basic":
            self._print_basic_mode_summary(args)
        elif self.mode == "formula":
            self._print_formula_mode_summary(args)
        elif self.mode == "hybrid":
            self._print_hybrid_mode_summary(args)
        else:
            self._print_structure_mode_summary(args)

    def _print_basic_mode_summary(self, args: argparse.Namespace) -> None:
        """顯示 basic 模式的輸出摘要"""
        print(f"[可搜尋 PDF] {'啟用' if args.searchable else '停用'}")
        print(f"[文字輸出] {args.text_output if args.text_output else '停用'}")

    def _print_formula_mode_summary(self, args: argparse.Namespace) -> None:
        """顯示 formula 模式的輸出摘要"""
        print(f"[LaTeX 輸出] {args.latex_output if args.latex_output else '停用'}")

    def _print_hybrid_mode_summary(self, args: argparse.Namespace) -> None:
        """顯示 hybrid 模式的輸出摘要"""
        print(f"[可搜尋 PDF] 啟用（混合模式）")
        print(f"[Markdown 輸出] {args.markdown_output if args.markdown_output else '停用'}")
        print(f"[JSON 輸出] {args.json_output if args.json_output else '停用'}")
        print(f"[HTML 輸出] {args.html_output if args.html_output else '停用'}")

    def _print_structure_mode_summary(self, args: argparse.Namespace) -> None:
        """顯示 structure/vl 模式的輸出摘要"""
        print(f"[Markdown 輸出] {args.markdown_output if args.markdown_output else '停用'}")
        print(f"[JSON 輸出] {args.json_output if args.json_output else '停用'}")
        print(f"[Excel 輸出] {args.excel_output if args.excel_output else '停用'}")
        print(f"[HTML 輸出] {args.html_output if args.html_output else '停用'}")
