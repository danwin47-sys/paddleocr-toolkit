#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paddleocr init - ?目初始化命令
"""

from pathlib import Path

import yaml


def create_project_structure(directory: Path):
    """?建?目目??構"""
    directories = [
        directory / "input",
        directory / "output",
        directory / "config",
        directory / "logs",
    ]

    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  ?建目?: {dir_path.name}/")

    # ?建.gitignore
    gitignore_content = """# PaddleOCR Toolkit
output/
logs/
*.pyc
__pycache__/
.pytest_cache/
*.log
"""

    gitignore_path = directory / ".gitignore"
    gitignore_path.write_text(gitignore_content, encoding="utf-8")
    print(f"  ?建檔案: .gitignore")


def create_config_file(directory: Path):
    """?建默?配置檔案"""
    config = {
        "ocr": {
            "mode": "hybrid",
            "device": "gpu",
            "dpi": 200,
            "lang": "ch",
            "use_angle_cls": True,
        },
        "output": {
            "format": "md",
            "directory": "./output",
        },
        "performance": {
            "batch_size": 8,
            "max_workers": 4,
            "enable_cache": True,
        },
        "logging": {
            "level": "INFO",
            "file": "./logs/paddleocr.log",
        },
    }

    config_path = directory / "config" / "default.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

    print(f"  ?建配置: config/default.yaml")


def create_readme(directory: Path):
    """?建README檔案"""
    readme_content = """# PaddleOCR Toolkit ?目

???目使用 PaddleOCR Toolkit ?行文?OCR?理。

## 目??構

```
.
├── input/          # ?入檔案
├── output/         # ?出?果
├── config/         # 配置檔案
│   └── default.yaml
└── logs/           # 日誌檔案
```

## 使用方法

```bash
# ?理??檔案
python -m paddleocr_toolkit input/document.pdf

# 使用配置檔案
python -m paddleocr_toolkit input/document.pdf --config config/default.yaml

# 批次?理
python -m paddleocr_toolkit input/
```

## 配置

?? `config/default.yaml` ?自定??置。

## 文?

- [快速?始](https://github.com/danwin47-sys/paddleocr-toolkit/blob/master/docs/QUICK_START.md)
- [API文?](https://github.com/danwin47-sys/paddleocr-toolkit/blob/master/docs/API_GUIDE.md)
"""

    readme_path = directory / "README.md"
    readme_path.write_text(readme_content, encoding="utf-8")
    print(f"  ?建文?: README.md")


def init_command(directory: str = "."):
    """
    初始化PaddleOCR Toolkit?目

    Args:
        directory: ?目目?路?
    """
    print("\n?始初始化 PaddleOCR Toolkit ?目...")
    print("=" * 50)

    project_dir = Path(directory).absolute()

    # 1. ?建目??構
    print("\n[1/4] ?建?目?構...")
    create_project_structure(project_dir)

    # 2. ?建配置檔案
    print("\n[2/4] ?建配置檔案...")
    create_config_file(project_dir)

    # 3. ?建README
    print("\n[3/4] ?建?目文?...")
    create_readme(project_dir)

    # 4. 模型提示
    print("\n[4/4] 模型?查...")
    print("  提示: 首次?行??自?下?PaddleOCR模型")
    print("  大小: ?100MB")
    print("  位置: ~/.paddleocr/")

    print("\n" + "=" * 50)
    print("? ?目初始化完成！")
    print(f"\n?目目?: {project_dir}")
    print("\n下一步:")
    print("  1. ?PDF檔案放入 input/ 目?")
    print("  2. ?行: python -m paddleocr_toolkit input/your.pdf")
    print("  3. 檢視?果: output/")
    print()


if __name__ == "__main__":
    import sys

    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    init_command(directory)
