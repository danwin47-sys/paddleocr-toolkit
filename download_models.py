#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
強制下載 PaddleOCR 模型
"""
import os
from pathlib import Path

print("=" * 60)
print("開始下載 PaddleOCR 模型...")
print("=" * 60)

# 檢查當前模型目錄大小
paddleocr_dir = Path.home() / ".paddleocr"
if paddleocr_dir.exists():
    initial_size = sum(
        f.stat().st_size for f in paddleocr_dir.rglob("*") if f.is_file()
    ) / (1024 * 1024)
    print(f"\n初始模型目錄大小: {initial_size:.2f} MB")
else:
    print("\n模型目錄尚不存在")

# 初始化 PaddleOCR (這會觸發自動下載)
print("\n正在初始化 PaddleOCR (ch 繁中/簡中模型)...")
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    use_textline_orientation=False,  # 不使用文字方向檢測
    lang="ch",  # 中文模型
    device="cpu",  # CPU 模式
)

print("\n✓ PaddleOCR 初始化完成！")

# 檢查下載後的大小
if paddleocr_dir.exists():
    final_size = sum(
        f.stat().st_size for f in paddleocr_dir.rglob("*") if f.is_file()
    ) / (1024 * 1024)
    print(f"\n最終模型目錄大小: {final_size:.2f} MB")
    print(f"下載大小: {final_size - initial_size:.2f} MB")

    if final_size > 10:
        print("\n✓ 模型下載成功！")
    else:
        print("\n⚠ 警告：模型大小異常，可能下載不完整")
else:
    print("\n✗ 模型目錄仍不存在，下載失敗")

print("\n" + "=" * 60)
print("完成！")
print("=" * 60)
