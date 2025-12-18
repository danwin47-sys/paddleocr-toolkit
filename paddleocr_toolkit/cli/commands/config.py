#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paddleocr config - 配置向?命令
"""

from pathlib import Path
from typing import Any, List, Optional

import yaml


def prompt(
    question: str, default: Optional[str] = None, options: Optional[List[Any]] = None
) -> str:
    """
    交互式提示

    Args:
        question: ??文本
        default: 默?值
        options: 可??列表
    """
    if options:
        print(f"\n{question}")
        for i, option in enumerate(options, 1):
            marker = " (默?)" if option == default else ""
            print(f"  {i}. {option}{marker}")

        while True:
            try:
                choice = input(f"??? [1-{len(options)}]: ").strip()
                if not choice and default:
                    return default
                idx = int(choice) - 1
                if 0 <= idx < len(options):
                    return options[idx]
                print(f"??入 1-{len(options)} 之?的?字")
            except (ValueError, IndexError):
                print("?效?入，?重?")
    else:
        prompt_text = f"{question}"
        if default:
            prompt_text += f" [{default}]"
        prompt_text += ": "

        result = input(prompt_text).strip()
        return result if result else default


def config_wizard():
    """交互式配置向?"""
    print("\n" + "=" * 60)
    print(" PaddleOCR Toolkit 配置向?")
    print("=" * 60)
    print("\n???助您?建自定?配置文件")
    print("(直接按Enter使用默?值)\n")

    config = {}

    # OCR?置
    print("\n??? OCR ?置 ???")

    config["ocr"] = {}
    config["ocr"]["mode"] = prompt(
        "??OCR模式",
        default="hybrid",
        options=["basic", "structure", "hybrid", "vl", "formula"],
    )

    config["ocr"]["device"] = prompt("???算??", default="gpu", options=["gpu", "cpu"])

    config["ocr"]["dpi"] = int(prompt("PDF??DPI (建?: 150-300)", default="200"))

    config["ocr"]["lang"] = prompt(
        "???言", default="ch", options=["ch", "en", "korean", "japan", "chinese_cht"]
    )

    # ?出?置
    print("\n??? ?出?置 ???")

    config["output"] = {}

    # 可以多?
    print("\n???出格式 (用逗?分隔，如: md,json)")
    print("  可?: md, json, html, txt")
    formats = input(f"格式 [md]: ").strip()
    config["output"]["format"] = formats if formats else "md"

    config["output"]["directory"] = prompt("?出目?", default="./output")

    # 性能?置
    print("\n??? 性能?置 ???")

    config["performance"] = {}
    config["performance"]["batch_size"] = int(prompt("批次大小 (建?: 4-16)", default="8"))

    config["performance"]["max_workers"] = int(prompt("最大工作?程 (建?: 2-8)", default="4"))

    enable_cache = prompt("?用?存?", default="yes", options=["yes", "no"])
    config["performance"]["enable_cache"] = enable_cache == "yes"

    # 日志?置
    print("\n??? 日志?置 ???")

    config["logging"] = {}
    config["logging"]["level"] = prompt(
        "日誌級別", default="INFO", options=["DEBUG", "INFO", "WARNING", "ERROR"]
    )

    config["logging"]["file"] = prompt("日誌檔案路徑", default="./logs/paddleocr.log")

    # 儲存配置
    print("\n📦 儲存配置 📦")

    config_name = prompt("配置文件名", default="custom")

    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)

    config_path = config_dir / f"{config_name}.yaml"

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

    print(f"\n? 配置已保存到: {config_path}")
    print(f"\n使用方法:")
    print(f"  python -m paddleocr_toolkit input.pdf --config {config_path}")
    print()


def show_config(config_file: str):
    """?示配置文件?容"""
    config_path = Path(config_file)

    if not config_path.exists():
        print(f"??: 配置文件不存在: {config_file}")
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
