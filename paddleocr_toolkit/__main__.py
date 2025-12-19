# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - 命令列入口點

使用方法：
    python -m paddleocr_toolkit --help
    python -m paddleocr_toolkit input.pdf --mode hybrid
"""

import os
import sys

# 新增父目錄到路徑以支援 paddle_ocr_tool
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 呼叫原始的 main 函式
from paddle_ocr_tool import main

if __name__ == "__main__":
    main()
