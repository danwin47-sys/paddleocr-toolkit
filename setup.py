#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from pathlib import Path

# 读取README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="paddleocr-toolkit",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="专业级OCR文件辨识与处理工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/danwin47-sys/paddleocr-toolkit",
    packages=find_packages(exclude=["tests*", "docs*", "examples*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "paddleocr>=3.0.0",
        "PyMuPDF>=1.23.0",
        "Pillow>=10.0.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "black>=23.12.1",
            "isort>=5.13.2",
            "mypy>=1.7.1",
        ],
        "ui": [
            "rich>=14.2.0",
        ],
        "perf": [
            "psutil>=5.9.0",
        ],
        "all": [
            "rich>=14.2.0",
            "psutil>=5.9.0",
            "wordninja>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "paddleocr-toolkit=paddle_ocr_tool:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="ocr paddleocr pdf image-recognition text-extraction",
    project_urls={
        "Bug Reports": "https://github.com/danwin47-sys/paddleocr-toolkit/issues",
        "Source": "https://github.com/danwin47-sys/paddleocr-toolkit",
        "Documentation": "https://github.com/dan win47-sys/paddleocr-toolkit/blob/master/README.md",
    },
)
