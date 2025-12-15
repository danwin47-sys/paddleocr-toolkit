#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paddleocr validate - OCR结果验证命令
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

import difflib
import json
from pathlib import Path
from typing import Dict, List


def calculate_character_accuracy(predicted: str, ground_truth: str) -> float:
    """
    计算字符准确率

    Args:
        predicted: 预测文本
        ground_truth: 真实文本

    Returns:
        准确率 (0-1)
    """
    if not ground_truth:
        return 0.0

    # 使用编辑距离
    distance = edit_distance(predicted, ground_truth)
    max_len = max(len(predicted), len(ground_truth))

    if max_len == 0:
        return 1.0

    accuracy = 1.0 - (distance / max_len)
    return max(0.0, accuracy)


def edit_distance(s1: str, s2: str) -> int:
    """计算编辑距离 (Levenshtein distance)"""
    if len(s1) < len(s2):
        return edit_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # 插入、删除、替换
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def calculate_word_accuracy(
    predicted_words: List[str], ground_truth_words: List[str]
) -> float:
    """计算词准确率"""
    if not ground_truth_words:
        return 0.0

    correct = sum(1 for p, g in zip(predicted_words, ground_truth_words) if p == g)
    return correct / len(ground_truth_words)


def validate_ocr_results(ocr_results_file: str, ground_truth_file: str):
    """
    验证OCR结果

    Args:
        ocr_results_file: OCR结果文件 (JSON)
        ground_truth_file: 真实文本文件 (TXT)
    """
    print("\n" + "=" * 70)
    print(" PaddleOCR Toolkit 结果验证")
    print("=" * 70)
    print()

    # 读取OCR结果
    ocr_path = Path(ocr_results_file)
    if not ocr_path.exists():
        print(f"错误: OCR结果文件不存在: {ocr_results_file}")
        return

    with open(ocr_path, "r", encoding="utf-8") as f:
        ocr_data = json.load(f)

    # 提取OCR文本
    if isinstance(ocr_data, list):
        # 假设是页面结果列表
        ocr_text = "\n".join(
            item.get("text", "")
            for page in ocr_data
            for item in (page if isinstance(page, list) else [page])
        )
    elif isinstance(ocr_data, dict) and "text" in ocr_data:
        ocr_text = ocr_data["text"]
    else:
        ocr_text = str(ocr_data)

    # 读取真实文本
    gt_path = Path(ground_truth_file)
    if not gt_path.exists():
        print(f"错误: 真实文本文件不存在: {ground_truth_file}")
        return

    with open(gt_path, "r", encoding="utf-8") as f:
        gt_text = f.read()

    # 计算指标
    print("计算验证指标...")
    print()

    # 1. 字符准确率
    char_accuracy = calculate_character_accuracy(ocr_text, gt_text)
    print(f"字符准确率: {char_accuracy:.2%}")

    # 2. 词准确率
    ocr_words = ocr_text.split()
    gt_words = gt_text.split()
    word_accuracy = calculate_word_accuracy(ocr_words, gt_words)
    print(f"词准确率: {word_accuracy:.2%}")

    # 3. 编辑距离
    distance = edit_distance(ocr_text, gt_text)
    print(f"编辑距离: {distance}")

    # 4. 长度统计
    print(f"\nOCR文本长度: {len(ocr_text)} 字符, {len(ocr_words)} 词")
    print(f"真实文本长度: {len(gt_text)} 字符, {len(gt_words)} 词")

    # 5. 差异对比
    print("\n" + "─" * 70)
    print(" 文本差异对比 (前300字符)")
    print("─" * 70)

    diff = list(
        difflib.unified_diff(
            gt_text[:300].splitlines(), ocr_text[:300].splitlines(), lineterm="", n=0
        )
    )

    if diff:
        for line in diff[:20]:  # 只显示前20行差异
            if line.startswith("-"):
                print(f"[真实] {line}")
            elif line.startswith("+"):
                print(f"[OCR]  {line}")
    else:
        print("✓ 完全匹配！")

    # 6. 评分
    print("\n" + "=" * 70)
    print(" 综合评分")
    print("=" * 70)

    overall_score = (char_accuracy + word_accuracy) / 2

    if overall_score >= 0.95:
        grade = "优秀"
        emoji = "+++"
    elif overall_score >= 0.85:
        grade = "良好"
        emoji = "++"
    elif overall_score >= 0.70:
        grade = "中等"
        emoji = "+"
    else:
        grade = "需改进"
        emoji = "-"

    print(f"\n综合准确率: {overall_score:.2%}")
    print(f"评级: {emoji} {grade}")

    print("\n建议:")
    if overall_score < 0.95:
        print("  • 尝试提高DPI (建议200-300)")
        print("  • 使用hybrid或structure模式")
        print("  • 进行图片预处理 (降噪、二值化)")
    else:
        print("  • OCR准确率已经很高！")

    print()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("使用方法: python validate.py <OCR结果JSON> <真实文本TXT>")
        print("范例: python validate.py output.json ground_truth.txt")
    else:
        validate_ocr_results(sys.argv[1], sys.argv[2])
