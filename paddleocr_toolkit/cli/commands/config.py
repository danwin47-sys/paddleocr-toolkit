```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paddleocr config - 配置向?命令
"""

from pathlib import Path
from typing import Any, List, Optional, Dict

import yaml
from paddleocr_toolkit.utils.logger import logger


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
        logger.info("") # Added logger.info for spacing
        print(f"{question}") # Keep simple print for interactive prompt
        for i, option in enumerate(options, 1):
            marker = " *" if option == default else "" # Changed marker
            print(f"  {i}. {option}{marker}") # Keep print for interactive menu

        while True:
            try:
                choice = input("Select (number): ").strip() # Changed prompt text
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

# Helper functions for config_wizard, derived from the diff's intent
def get_input(question: str, default: str) -> str:
    return prompt(question, default=default)

def get_selection(question: str, options: List[str], default: str) -> str:
    return prompt(question, default=default, options=options)


def config_wizard():
    """交互式配置向?"""
    logger.info("=" * 60)
    logger.info(" PaddleOCR Toolkit Configuration Wizard")
    logger.info("=" * 60)
    logger.info("This will help you create a custom configuration file")
    logger.info("(Press Enter to use default values)\n")

    config: Dict[str, Any] = {}

    # 1. OCR Settings
    logger.info("\n--- OCR Settings ---")

    config["ocr"] = {
        "mode": get_selection("Select OCR Mode", ["basic", "structure", "hybrid", "vl", "formula"], "hybrid"),
        "device": get_selection("Select Compute Device", ["gpu", "cpu"], "gpu"),
        "dpi": int(get_input("PDF DPI (Recommended: 150-300)", "200")),
        "lang": get_selection("Select Language", ["ch", "en", "korean", "japan", "chinese_cht"], "ch"),
        "use_gpu": get_selection("Use GPU?", ["true", "false"], "true") == "true", # Added from diff
        "use_angle_cls": get_selection("Use Angle Classification?", ["true", "false"], "true") == "true", # Added from diff
    }

    # 2. Output Settings
    logger.info("\n--- Output Settings ---")

    output_dir = get_input("Output Directory", "output") # Renamed variable
    
    logger.info("\nOutput Formats (comma separated, e.g., md,json)")
    logger.info("  Available: md, json, html, txt")
    formats_str = input("Formats [md,json]: ").strip() or "md,json" # Changed default and prompt
    formats = [f.strip() for f in formats_str.split(",")]

    config["output"] = {
        "format": formats, # Changed to list
        "directory": output_dir, # Used output_dir
    }

    # 3. Performance Settings
    logger.info("\n--- Performance Settings ---")

    config["performance"] = {
        "batch_size": int(get_input("Batch Size (Recommended: 4-16)", "8")),
        "max_workers": int(get_input("Max Workers (Recommended: 2-8)", "4")),
        "enable_cache": get_selection("Enable Cache?", ["yes", "no"], "yes") == "yes",
    }

    # 4. Logging Settings
    logger.info("\n--- Logging Settings ---")

    config["logging"] = {
        "level": get_selection("Log Level", ["DEBUG", "INFO", "WARNING", "ERROR"], "INFO"),
        "save_file": get_selection("Save log to file?", ["true", "false"], "true") == "true", # Added from diff
        "log_file": get_input("Log File", "paddleocr.log"), # Changed default
    }

    # Save Configuration
    logger.info("\n--- Save Configuration ---")

    config_name = get_input("Config file name", "custom") # Changed prompt

    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)

    config_path = config_dir / f"{config_name}.yaml"

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

    logger.info("Configuration saved to: %s", config_path)
    logger.info("Usage:")
    logger.info("  python -m paddleocr_toolkit input.pdf --config %s", config_path)
    logger.info("")


def show_config(config_file: str):
    """显示配置内容"""
    path = Path(config_file)
    if not path.exists():
        logger.error("Config file not found: %s", config_file)
        return

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    logger.info("Configuration: %s", config_file)
    logger.info("=" * 60)
    print(yaml.dump(config, default_flow_style=False, allow_unicode=True))  # Keep print for YAML dump output for now


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "show":
        show_config(sys.argv[2] if len(sys.argv) > 2 else "config/default.yaml")
    else:
        config_wizard()
