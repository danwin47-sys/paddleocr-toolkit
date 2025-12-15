#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit CLI主入口
v1.2.0 - 完整的CLI命令系统
"""

import io
import sys

# Windows UTF-8修复
if sys.platform == "win32":
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
    """主入口函数"""
    parser = argparse.ArgumentParser(
        prog="paddleocr",
        description="PaddleOCR Toolkit - 专业级OCR文件处理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  paddleocr init myproject          # 初始化项目
  paddleocr config                  # 配置向导
  paddleocr process file.pdf        # 处理文件
  paddleocr benchmark test.pdf      # 性能测试
  paddleocr validate ocr.json gt.txt  # 验证结果

更多信息: https://github.com/danwin47-sys/paddleocr-toolkit
        """,
    )

    # 版本
    parser.add_argument("--version", action="version", version="%(prog)s 1.2.0")

    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # init命令
    init_parser = subparsers.add_parser("init", help="初始化项目")
    init_parser.add_argument("directory", nargs="?", default=".", help="项目目录")

    # config命令
    config_parser = subparsers.add_parser("config", help="配置向导")
    config_parser.add_argument("--show", help="显示配置文件")

    # process命令
    process_parser = subparsers.add_parser("process", help="处理文件")
    process_parser.add_argument("input", help="输入文件或目录")
    process_parser.add_argument(
        "--mode",
        default="hybrid",
        choices=["basic", "hybrid", "structure"],
        help="OCR模式",
    )
    process_parser.add_argument("--output", help="输出目录")
    process_parser.add_argument("--format", default="md", help="输出格式")

    # benchmark命令
    benchmark_parser = subparsers.add_parser("benchmark", help="性能测试")
    benchmark_parser.add_argument("pdf", help="PDF文件")
    benchmark_parser.add_argument("--output", help="报告输出路径")

    # validate命令
    validate_parser = subparsers.add_parser("validate", help="验证OCR结果")
    validate_parser.add_argument("ocr_results", help="OCR结果JSON文件")
    validate_parser.add_argument("ground_truth", help="真实文本文件")

    # 解析参数
    args = parser.parse_args()

    # 如果没有命令，显示帮助
    if not args.command:
        parser.print_help()
        return 0

    # 执行命令
    try:
        if args.command == "init":
            from paddleocr_toolkit.cli.commands.init import init_command

            init_command(args.directory)

        elif args.command == "config":
            from paddleocr_toolkit.cli.commands.config import (config_wizard,
                                                               show_config)

            if args.show:
                show_config(args.show)
            else:
                config_wizard()

        elif args.command == "process":
            print(f"处理文件: {args.input}")
            print(f"模式: {args.mode}")
            # 这里应该调用实际的处理逻辑

        elif args.command == "benchmark":
            from paddleocr_toolkit.cli.commands.benchmark import run_benchmark

            run_benchmark(args.pdf, args.output)

        elif args.command == "validate":
            from paddleocr_toolkit.cli.commands.validate import \
                validate_ocr_results

            validate_ocr_results(args.ocr_results, args.ground_truth)

        return 0

    except KeyboardInterrupt:
        print("\n\n操作已取消")
        return 1
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
