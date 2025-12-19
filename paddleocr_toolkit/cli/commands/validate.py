#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paddleocr validate - OCR?果??命令
"""

import difflib
import json
from pathlib import Path
from typing import List


def calculate_character_accuracy(predicted: str, ground_truth: str) -> float:
    """
    ?算字元準確率

    Args:
        predicted: ??文字
        ground_truth: 真?文字

    Returns:
        準確率 (0-1)
    """
    if not ground_truth:
        return 0.0

    # 使用??距離
    distance = edit_distance(predicted, ground_truth)
    max_len = max(len(predicted), len(ground_truth))

    if max_len == 0:
        return 1.0

    accuracy = 1.0 - (distance / max_len)
    return max(0.0, accuracy)


def edit_distance(s1: str, s2: str) -> int:
    """?算??距離 (Levenshtein distance)"""
    if len(s1) < len(s2):
        return edit_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # 插入、?除、替?
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def calculate_word_accuracy(
    predicted_words: List[str], ground_truth_words: List[str]
) -> float:
    """?算?準確率"""
    if not ground_truth_words:
        return 0.0

    correct = sum(1 for p, g in zip(predicted_words, ground_truth_words) if p == g)
    return correct / len(ground_truth_words)


def validate_ocr_results(ocr_results_file: str, ground_truth_file: str):
    """
    ??OCR?果

    Args:
        ocr_results_file: OCR?果檔案 (JSON)
        ground_truth_file: 真?文字檔案 (TXT)
    """
    print("\n" + "=" * 70)
    print(" PaddleOCR Toolkit ?果??")
    print("=" * 70)
    print()

    # ?取OCR?果
    ocr_path = Path(ocr_results_file)
    if not ocr_path.exists():
        print(f"??: OCR?果檔案不存在: {ocr_results_file}")
        return

    with open(ocr_path, "r", encoding="utf-8") as f:
        ocr_data = json.load(f)

    # 提取OCR文字
    if isinstance(ocr_data, list):
        # 假?是?面?果列表
        ocr_text = "\n".join(
            item.get("text", "")
            for page in ocr_data
            for item in (page if isinstance(page, list) else [page])
        )
    elif isinstance(ocr_data, dict) and "text" in ocr_data:
        ocr_text = ocr_data["text"]
    else:
        ocr_text = str(ocr_data)

    # ?取真?文字
    gt_path = Path(ground_truth_file)
    if not gt_path.exists():
        print(f"??: 真?文字檔案不存在: {ground_truth_file}")
        return

    with open(gt_path, "r", encoding="utf-8") as f:
        gt_text = f.read()

    # ?算指?
    print("?算??指?...")
    print()

    # 1. 字元準確率
    char_accuracy = calculate_character_accuracy(ocr_text, gt_text)
    print(f"字元準確率: {char_accuracy:.2%}")

    # 2. ?準確率
    ocr_words = ocr_text.split()
    gt_words = gt_text.split()
    word_accuracy = calculate_word_accuracy(ocr_words, gt_words)
    print(f"?準確率: {word_accuracy:.2%}")

    # 3. ??距離
    distance = edit_distance(ocr_text, gt_text)
    print(f"??距離: {distance}")

    # 4. ?度??
    print(f"\nOCR文字?度: {len(ocr_text)} 字元, {len(ocr_words)} ?")
    print(f"真?文字?度: {len(gt_text)} 字元, {len(gt_words)} ?")

    # 5. 差異?比
    print("\n" + "─" * 70)
    print(" 文字差異?比 (前300字元)")
    print("─" * 70)

    diff = list(
        difflib.unified_diff(
            gt_text[:300].splitlines(), ocr_text[:300].splitlines(), lineterm="", n=0
        )
    )

    if diff:
        for line in diff[:20]:  # 只?示前20行差異
            if line.startswith("-"):
                print(f"[真?] {line}")
            elif line.startswith("+"):
                print(f"[OCR]  {line}")
    else:
        print("? 完全匹配！")

    # 6. ?分
    print("\n" + "=" * 70)
    print(" ?合?分")
    print("=" * 70)

    overall_score = (char_accuracy + word_accuracy) / 2

    if overall_score >= 0.95:
        grade = "優秀"
        emoji = "+++"
    elif overall_score >= 0.85:
        grade = "良好"
        emoji = "++"
    elif overall_score >= 0.70:
        grade = "中等"
        emoji = "+"
    else:
        grade = "需改?"
        emoji = "-"

    print(f"\n?合準確率: {overall_score:.2%}")
    print(f"??: {emoji} {grade}")

    print("\n建?:")
    if overall_score < 0.95:
        print("  ‧ ??提高DPI (建?200-300)")
        print("  ‧ 使用hybrid或structure模式")
        print("  ‧ ?行?片??理 (降噪、二值化)")
    else:
        print("  ‧ OCR準確率已?很高！")

    print()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("使用方法: python validate.py <OCR?果JSON> <真?文字TXT>")
        print("範例: python validate.py output.json ground_truth.txt")
    else:
        validate_ocr_results(sys.argv[1], sys.argv[2])
