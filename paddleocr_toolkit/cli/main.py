#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit CLI主入口
v1.2.0 - 完整的CLI命令系統
"""

import argparse
import sys


def main():
    """主入口函式"""
    parser = argparse.ArgumentParser(
        prog="paddleocr",
        description="PaddleOCR Toolkit - 專業級OCR檔案處理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  paddleocr init myproject          # 初始化專案
  paddleocr config                  # 配置嚮導
  paddleocr process file.pdf        # 處理檔案
  paddleocr benchmark test.pdf      # 效能測試
  paddleocr validate ocr.json gt.txt  # 驗證結果

更多資訊: https://github.com/danwin47-sys/paddleocr-toolkit
        """,
    )

    # 版本
    parser.add_argument("--version", action="version", version="%(prog)s 1.2.0")

    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # init命令
    init_parser = subparsers.add_parser("init", help="初始化專案")
    init_parser.add_argument("directory", nargs="?", default=".", help="專案目錄")

    # config命令
    config_parser = subparsers.add_parser("config", help="配置嚮導")
    config_parser.add_argument("--show", help="顯示配置檔案")

    # process命令
    process_parser = subparsers.add_parser("process", help="處理檔案")
    process_parser.add_argument("input", help="輸入檔案或目錄")
    process_parser.add_argument(
        "--mode",
        default="hybrid",
        choices=["basic", "hybrid", "structure"],
        help="OCR模式",
    )
    process_parser.add_argument("--output", help="輸出目錄")
    process_parser.add_argument("--format", default="md", help="輸出格式")

    # benchmark命令
    benchmark_parser = subparsers.add_parser("benchmark", help="效能測試")
    benchmark_parser.add_argument("pdf", help="PDF檔案")
    benchmark_parser.add_argument("--output", help="報告輸出路徑")

    # validate命令
    validate_parser = subparsers.add_parser("validate", help="驗證OCR結果")
    validate_parser.add_argument("ocr_results", help="OCR結果JSON檔案")
    validate_parser.add_argument("ground_truth", help="真實文字檔案")

    # 解析引數
    args = parser.parse_args()

    # 如果沒有命令，顯示幫助
    if not args.command:
        parser.print_help()
        return 0

    # 執行命令
    try:
        if args.command == "init":
            from paddleocr_toolkit.cli.commands.init import init_command

            init_command(args.directory)

        elif args.command == "config":
            from paddleocr_toolkit.cli.commands.config import config_wizard, show_config

            if args.show:
                show_config(args.show)
            else:
                config_wizard()

        elif args.command == "process":
            print(f"處理檔案: {args.input}")
            print(f"模式: {args.mode}")
            # 這裡是實際的處理邏輯

        elif args.command == "benchmark":
            from paddleocr_toolkit.cli.commands.benchmark import run_benchmark

            run_benchmark(args.pdf, args.output)

        elif args.command == "validate":
            from paddleocr_toolkit.cli.commands.validate import validate_ocr_results

            validate_ocr_results(args.ocr_results, args.ground_truth)

        return 0

    except KeyboardInterrupt:
        print("\n\n操作已取消")
        return 1
    except Exception as e:
        print(f"\n錯誤: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
