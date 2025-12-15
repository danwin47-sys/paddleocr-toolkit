#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paddleocr config - 配置向导命令
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
    except Exception:
        pass

from pathlib import Path

import yaml


def prompt(question: str, default: str = None, options: list = None) -> str:
    """
    交互式提示

    Args:
        question: 问题文本
        default: 默认值
        options: 可选项列表
    """
    if options:
        print(f"\n{question}")
        for i, option in enumerate(options, 1):
            marker = " (默认)" if option == default else ""
            print(f"  {i}. {option}{marker}")

        while True:
            try:
                choice = input(f"请选择 [1-{len(options)}]: ").strip()
                if not choice and default:
                    return default
                idx = int(choice) - 1
                if 0 <= idx < len(options):
                    return options[idx]
                print(f"请输入 1-{len(options)} 之间的数字")
            except (ValueError, IndexError):
                print("无效输入，请重试")
    else:
        prompt_text = f"{question}"
        if default:
            prompt_text += f" [{default}]"
        prompt_text += ": "

        result = input(prompt_text).strip()
        return result if result else default


def config_wizard():
    """交互式配置向导"""
    print("\n" + "=" * 60)
    print(" PaddleOCR Toolkit 配置向导")
    print("=" * 60)
    print("\n这将帮助您创建自定义配置文件")
    print("(直接按Enter使用默认值)\n")

    config = {}

    # OCR设置
    print("\n━━━ OCR 设置 ━━━")

    config["ocr"] = {}
    config["ocr"]["mode"] = prompt(
        "选择OCR模式",
        default="hybrid",
        options=["basic", "structure", "hybrid", "vl", "formula"],
    )

    config["ocr"]["device"] = prompt("选择计算设备", default="gpu", options=["gpu", "cpu"])

    config["ocr"]["dpi"] = int(prompt("PDF转换DPI (建议: 150-300)", default="200"))

    config["ocr"]["lang"] = prompt(
        "识别语言", default="ch", options=["ch", "en", "korean", "japan", "chinese_cht"]
    )

    # 输出设置
    print("\n━━━ 输出设置 ━━━")

    config["output"] = {}

    # 可以多选
    print("\n选择输出格式 (用逗号分隔，如: md,json)")
    print("  可选: md, json, html, txt")
    formats = input(f"格式 [md]: ").strip()
    config["output"]["format"] = formats if formats else "md"

    config["output"]["directory"] = prompt("输出目录", default="./output")

    # 性能设置
    print("\n━━━ 性能设置 ━━━")

    config["performance"] = {}
    config["performance"]["batch_size"] = int(prompt("批次大小 (建议: 4-16)", default="8"))

    config["performance"]["max_workers"] = int(prompt("最大工作线程 (建议: 2-8)", default="4"))

    enable_cache = prompt("启用缓存?", default="yes", options=["yes", "no"])
    config["performance"]["enable_cache"] = enable_cache == "yes"

    # 日志设置
    print("\n━━━ 日志设置 ━━━")

    config["logging"] = {}
    config["logging"]["level"] = prompt(
        "日志级别", default="INFO", options=["DEBUG", "INFO", "WARNING", "ERROR"]
    )

    config["logging"]["file"] = prompt("日志文件路径", default="./logs/paddleocr.log")

    # 保存配置
    print("\n━━━ 保存配置 ━━━")

    config_name = prompt("配置文件名称", default="custom")

    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)

    config_path = config_dir / f"{config_name}.yaml"

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

    print(f"\n✓ 配置已保存到: {config_path}")
    print(f"\n使用方法:")
    print(f"  python -m paddleocr_toolkit input.pdf --config {config_path}")
    print()


def show_config(config_file: str):
    """显示配置文件内容"""
    config_path = Path(config_file)

    if not config_path.exists():
        print(f"错误: 配置文件不存在: {config_file}")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    print(f"\n配置文件: {config_file}")
    print("=" * 60)
    print(yaml.dump(config, default_flow_style=False, allow_unicode=True))


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "show":
        show_config(sys.argv[2] if len(sys.argv) > 2 else "config/default.yaml")
    else:
        config_wizard()
