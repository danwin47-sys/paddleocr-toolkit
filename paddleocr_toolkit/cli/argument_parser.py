# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - CLI 參數解析器

提供命令列介面的參數定義和解析功能。
"""

import argparse
from typing import Optional


def create_argument_parser() -> argparse.ArgumentParser:
    """建立命令列參數解析器

    Returns:
        argparse.ArgumentParser: 設定好的參數解析器

    Example:
        parser = create_argument_parser()
        args = parser.parse_args()
    """
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
        """,
    )

    # 基本參數
    parser.add_argument("input", help="輸入檔案或目錄路徑")

    # OCR 模式選項
    parser.add_argument(
        "--mode",
        "-m",
        type=str,
        default="basic",
        choices=["basic", "structure", "vl", "formula", "hybrid"],
        help="OCR 模式: basic, structure, vl, formula, hybrid (版面分析+精確OCR)",
    )

    # 文件校正選項
    parser.add_argument(
        "--orientation-classify", action="store_true", help="啟用文件方向自動校正"
    )

    parser.add_argument("--unwarping", action="store_true", help="啟用文件彎曲校正")

    parser.add_argument("--textline-orientation", action="store_true", help="啟用文字行方向偵測")

    # 輸出選項
    parser.add_argument(
        "--searchable",
        "-s",
        action="store_true",
        default=True,
        help="生成可搜尋 PDF（僅 basic 模式，預設：啟用）",
    )

    parser.add_argument("--no-searchable", action="store_true", help="停用可搜尋 PDF 生成")

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="輸出檔案路徑（預設：[原始檔名]_searchable.pdf）",
    )

    parser.add_argument(
        "--text-output",
        "-t",
        type=str,
        nargs="?",
        const="AUTO",
        default="AUTO",
        help="將識別的文字儲存到檔案（basic 模式，預設：[原始檔名]_ocr.txt）",
    )

    parser.add_argument("--no-text-output", action="store_true", help="停用文字輸出")

    parser.add_argument(
        "--markdown-output",
        type=str,
        nargs="?",
        const="AUTO",
        default="AUTO",
        help="輸出 Markdown 格式（structure/vl 模式，預設：[原始檔名]_ocr.md）",
    )

    parser.add_argument(
        "--no-markdown-output", action="store_true", help="停用 Markdown 輸出"
    )

    parser.add_argument(
        "--json-output",
        type=str,
        nargs="?",
        const="AUTO",
        default="AUTO",
        help="輸出 JSON 格式（structure/vl 模式，預設：[原始檔名]_ocr.json）",
    )

    parser.add_argument("--no-json-output", action="store_true", help="停用 JSON 輸出")

    # Excel 輸出（表格識別）
    parser.add_argument(
        "--excel-output",
        type=str,
        nargs="?",
        const="AUTO",
        default=None,
        help="輸出 Excel 格式（structure 模式，僅表格：[原始檔名]_tables.xlsx）",
    )

    # HTML 輸出（structure 模式）
    parser.add_argument(
        "--html-output",
        type=str,
        nargs="?",
        const="AUTO",
        default=None,
        help="輸出 HTML 格式（structure/hybrid 模式：[原始檔名]_page*.html）",
    )

    # 輸出全部格式
    parser.add_argument(
        "--all",
        action="store_true",
        help="一次輸出所有格式（Markdown + JSON + HTML，structure/hybrid 模式）",
    )

    # LaTeX 輸出（公式識別）
    parser.add_argument(
        "--latex-output",
        type=str,
        nargs="?",
        const="AUTO",
        default=None,
        help="輸出 LaTeX 格式（formula 模式，預設：[原始檔名]_formula.tex）",
    )

    # 進度條控制
    parser.add_argument("--no-progress", action="store_true", help="停用進度條顯示")

    # 其他選項
    parser.add_argument(
        "--dpi", type=int, default=150, help="PDF 轉圖片的解析度（預設：150，降低以減少記憶體使用）"
    )

    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        choices=["gpu", "cpu"],
        help="運算設備（預設：cpu，如有 CUDA 可用 --device gpu）",
    )

    parser.add_argument(
        "--recursive", "-r", action="store_true", help="遞迴處理子目錄（僅適用於目錄輸入）"
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="顯示詳細日誌")

    parser.add_argument(
        "--debug-text",
        action="store_true",
        help="DEBUG 模式：將可搜尋 PDF 的隱形文字改為粉紅色可見文字（方便調試文字位置）",
    )

    parser.add_argument(
        "--no-compress", action="store_true", help="停用 PDF 壓縮：使用 PNG 無損格式（檔案較大但品質最佳）"
    )

    parser.add_argument(
        "--jpeg-quality",
        type=int,
        default=85,
        help="JPEG 壓縮品質（0-100，預設 85）。較低值 = 較小檔案但品質較差",
    )

    # ========== 翻譯選項 ==========
    translate_group = parser.add_argument_group("翻譯選項", "使用 Ollama 本地模型翻譯 PDF 內容")

    translate_group.add_argument(
        "--translate", action="store_true", help="啟用翻譯功能（需要 Ollama 服務和 hybrid 模式）"
    )

    translate_group.add_argument(
        "--source-lang",
        type=str,
        default="auto",
        help="來源語言（auto=自動偵測，zh=中文，zh-cn=簡體中文，zh-tw=繁體中文，en=英文，預設：auto）",
    )

    translate_group.add_argument(
        "--target-lang",
        type=str,
        default="en",
        help="目標語言（zh=中文，zh-cn=簡體中文，zh-tw=繁體中文，en=英文，ja=日文，預設：en）",
    )

    translate_group.add_argument(
        "--ollama-model",
        type=str,
        default="qwen2.5:7b",
        help="Ollama 模型名稱（預設：qwen2.5:7b）",
    )

    translate_group.add_argument(
        "--ollama-url",
        type=str,
        default="http://localhost:11434",
        help="Ollama API 地址（預設：http://localhost:11434）",
    )

    translate_group.add_argument(
        "--no-mono", action="store_true", help="不輸出純翻譯 PDF（僅輸出雙語對照）"
    )

    translate_group.add_argument(
        "--no-dual", action="store_true", help="不輸出雙語對照 PDF（僅輸出純翻譯）"
    )

    translate_group.add_argument(
        "--dual-mode",
        type=str,
        choices=["alternating", "side-by-side"],
        default="alternating",
        help="雙語對照模式：alternating(交替頁) 或 side-by-side(並排)（預設：alternating）",
    )

    translate_group.add_argument(
        "--dual-translate-first", action="store_true", help="雙語模式中譯文在前（預設：原文在前）"
    )

    translate_group.add_argument(
        "--font-path", type=str, default=None, help="自訂字體路徑（用於繪製翻譯文字）"
    )

    translate_group.add_argument(
        "--ocr-workaround",
        action="store_true",
        help="使用 OCR 補救模式繪製翻譯文字（適用於掃描件，直接在 PDF 上操作）",
    )

    return parser
