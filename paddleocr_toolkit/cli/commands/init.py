#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paddleocr init - 项目初始化命令
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

import os
import shutil
from pathlib import Path

import yaml


def create_project_structure(directory: Path):
    """创建项目目录结构"""
    directories = [
        directory / "input",
        directory / "output",
        directory / "config",
        directory / "logs",
    ]

    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  创建目录: {dir_path.name}/")

    # 创建.gitignore
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
    print(f"  创建文件: .gitignore")


def create_config_file(directory: Path):
    """创建默认配置文件"""
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

    print(f"  创建配置: config/default.yaml")


def create_readme(directory: Path):
    """创建README文件"""
    readme_content = """# PaddleOCR Toolkit 项目

这个项目使用 PaddleOCR Toolkit 进行文档OCR处理。

## 目录结构

```
.
├── input/          # 输入文件
├── output/         # 输出结果
├── config/         # 配置文件
│   └── default.yaml
└── logs/           # 日志文件
```

## 使用方法

```bash
# 处理单个文件
python -m paddleocr_toolkit input/document.pdf

# 使用配置文件
python -m paddleocr_toolkit input/document.pdf --config config/default.yaml

# 批量处理
python -m paddleocr_toolkit input/
```

## 配置

编辑 `config/default.yaml` 来自定义设置。

## 文档

- [快速开始](https://github.com/danwin47-sys/paddleocr-toolkit/blob/master/docs/QUICK_START.md)
- [API文档](https://github.com/danwin47-sys/paddleocr-toolkit/blob/master/docs/API_GUIDE.md)
"""

    readme_path = directory / "README.md"
    readme_path.write_text(readme_content, encoding="utf-8")
    print(f"  创建文档: README.md")


def init_command(directory: str = "."):
    """
    初始化PaddleOCR Toolkit项目

    Args:
        directory: 项目目录路径
    """
    print("\n开始初始化 PaddleOCR Toolkit 项目...")
    print("=" * 50)

    project_dir = Path(directory).absolute()

    # 1. 创建目录结构
    print("\n[1/4] 创建项目结构...")
    create_project_structure(project_dir)

    # 2. 创建配置文件
    print("\n[2/4] 创建配置文件...")
    create_config_file(project_dir)

    # 3. 创建README
    print("\n[3/4] 创建项目文档...")
    create_readme(project_dir)

    # 4. 模型提示
    print("\n[4/4] 模型检查...")
    print("  提示: 首次运行时会自动下载PaddleOCR模型")
    print("  大小: 约100MB")
    print("  位置: ~/.paddleocr/")

    print("\n" + "=" * 50)
    print("✓ 项目初始化完成！")
    print(f"\n项目目录: {project_dir}")
    print("\n下一步:")
    print("  1. 将PDF文件放入 input/ 目录")
    print("  2. 运行: python -m paddleocr_toolkit input/your.pdf")
    print("  3. 查看结果: output/")
    print()


if __name__ == "__main__":
    import sys

    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    init_command(directory)
