#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit CLI主入口
v1.2.0 - 完整的CLI命令系?
"""

import io
import sys

# Windows UTF-8修复
if sys.platform == "win32" and "pytest" not in sys.modules:
    try:
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True
        )
    except:
        pass

import argparse
from pathlib import Path


def main():
    """主入口函?"""
    parser = argparse.ArgumentParser(
        prog="paddleocr",
        description="PaddleOCR Toolkit - ???OCR文件?理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  paddleocr init myproject          # 初始化?目
  paddleocr config                  # 配置向?
  paddleocr process file.pdf        # ?理文件
  paddleocr benchmark test.pdf      # 性能??
  paddleocr validate ocr.json gt.txt  # ???果

更多信息: https://github.com/danwin47-sys/paddleocr-toolkit
        """,
    )

    # 版本
    parser.add_argument("--version", action="version", version="%(prog)s 1.2.0")

    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # init命令
    init_parser = subparsers.add_parser("init", help="初始化?目")
    init_parser.add_argument("directory", nargs="?", default=".", help="?目目?")

    # config命令
    config_parser = subparsers.add_parser("config", help="配置向?")
    config_parser.add_argument("--show", help="?示配置文件")

    # process命令
    process_parser = subparsers.add_parser("process", help="?理文件")
    process_parser.add_argument("input", help="?入文件或目?")
    process_parser.add_argument(
        "--mode",
        default="hybrid",
        choices=["basic", "hybrid", "structure"],
        help="OCR模式",
    )
    process_parser.add_argument("--output", help="?出目?")
    process_parser.add_argument("--format", default="md", help="?出格式")

    # benchmark命令
    benchmark_parser = subparsers.add_parser("benchmark", help="性能??")
    benchmark_parser.add_argument("pdf", help="PDF文件")
    benchmark_parser.add_argument("--output", help="?告?出路?")

    # validate命令
    validate_parser = subparsers.add_parser("validate", help="??OCR?果")
    validate_parser.add_argument("ocr_results", help="OCR?果JSON文件")
    validate_parser.add_argument("ground_truth", help="真?文本文件")

    # 解析??
    args = parser.parse_args()

    # 如果?有命令，?示?助
    if not args.command:
        parser.print_help()
        return 0

    # ?行命令
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
            print(f"?理文件: {args.input}")
            print(f"模式: {args.mode}")
            # ?里???用??的?理??

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
        print(f"\n??: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
