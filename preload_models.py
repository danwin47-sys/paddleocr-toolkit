#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docker 構建時預載 PaddleOCR 模型
此腳本在 Docker Image 構建階段執行，將模型打包進映像檔
"""
import sys

print("=" * 60)
print("🚀 開始預載 PaddleOCR 模型到 Docker Image...")
print("=" * 60)

try:
    from paddleocr import PaddleOCR

    # 初始化 PaddleOCR (觸發模型下載)
    print("\n📦 正在下載 PP-OCRv5 中文模型...")
    ocr = PaddleOCR(use_textline_orientation=False, lang="ch", device="cpu")

    print("\n✓ 模型預載完成！")
    print("  - 檢測模型: PP-OCRv5_server_det")
    print("  - 識別模型: PP-OCRv5_server_rec")
    print("  - 文檔校正: UVDoc")
    print("=" * 60)

except Exception as e:
    print(f"\n✗ 錯誤：模型預載失敗: {e}", file=sys.stderr)
    sys.exit(1)
