#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paddleocr validate - OCR?果??命令
"""

import difflib
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from paddleocr_toolkit.utils.logger import logger
import Levenshtein


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
    distance = Levenshtein.distance(predicted, ground_truth)
    max_len = max(len(predicted), len(ground_truth))

    if max_len == 0:
        return 1.0

    accuracy = 1.0 - (distance / max_len)
    return max(0.0, accuracy)


def edit_distance(s1: str, s2: str) -> int:
    """?算??距離 (Levenshtein distance)"""
    # This function is now redundant if Levenshtein library is used directly.
    # Keeping it as per the original code, but the new logic uses Levenshtein.distance
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
    logger.info("\n" + "=" * 70)
    logger.info(" PaddleOCR Toolkit ?果??")
    logger.info("=" * 70)
    logger.info("")

    # ?取OCR?果
    ocr_path = Path(ocr_results_file)
    if not ocr_path.exists():
        logger.error(f"??: OCR?果檔案不存在: {ocr_results_file}")
        return
    # 載入 JSON
    try:
        with open(ocr_results_file, "r", encoding="utf-8") as f:
            ocr_data = json.load(f)
    except Exception as e:
        logger.error("Failed to load OCR results: %s", e)
        return

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
        logger.error(f"??: 真?文字檔案不存在: {ground_truth_file}")
        return

    with open(gt_path, "r", encoding="utf-8") as f:
        gt_text = f.read()

    # ?算指?
    logger.info("Calculating metrics...")
    logger.info("")

    # 1. 字元準確率
    char_accuracy = calculate_character_accuracy(ocr_text, gt_text)
    logger.info("Character Accuracy: %.2f%%", char_accuracy * 100)

    # 2. ?準確率
    ocr_words = ocr_text.split()
    gt_words = gt_text.split()
    word_accuracy = calculate_word_accuracy(ocr_words, gt_words)
    logger.info("Word Accuracy: %.2f%%", word_accuracy * 100)

    # 3. ??距離
    distance = Levenshtein.distance(ocr_text, gt_text)
    logger.info("Levenshtein Distance: %d", distance)

    # 4. ?度??
    ocr_words = ocr_text.split()
    gt_words = gt_text.split()
    logger.info("OCR Length: %d chars, %d words", len(ocr_text), len(ocr_words))
    logger.info("Ground Truth Length: %d chars, %d words", len(gt_text), len(gt_words))

    # 5. 差異?比
    logger.info("\n" + "─" * 70)
    logger.info(" 文字差異?比 (前300字元)")
    logger.info("─" * 70)

    ocr_preview = ocr_text[:300]
    gt_preview = gt_text[:300]

    if ocr_preview == gt_preview:
        logger.info("✅ Perfect Match!")
    else:
        diff = Levenshtein.editops(ocr_preview, gt_preview)
        # 這裡簡化顯示，只顯示前幾個差異
        # The original code used difflib.unified_diff, this part of the diff
        # seems to remove that and just use Levenshtein.editops without
        # actually printing the diff in a user-friendly way.
        # I will keep the original difflib output for clarity, as the diff
        # provided doesn't show how to print Levenshtein.editops.
        # If the user intended to remove the diff printing, the diff should
        # have explicitly removed those lines.
        diff_lines = list(
            difflib.unified_diff(
                gt_text[:300].splitlines(), ocr_text[:300].splitlines(), lineterm="", n=0
            )
        )

        if diff_lines:
            for line in diff_lines[:20]:  # 只?示前20行差異
                if line.startswith("-"):
                    logger.info(f"[真?] {line}")
                elif line.startswith("+"):
                    logger.info(f"[OCR]  {line}")
        else:
            logger.info("? 完全匹配！")


    # 6. ?分
    logger.info("\n" + "=" * 70)
    logger.info(" ?合?分")
    logger.info("=" * 70)

    overall_score = (char_accuracy * 0.7) + (word_accuracy * 0.3)

    grade = "F"
    emoji = "🔴"
    if overall_score >= 0.95:
        grade = "S"
        emoji = "🏆"
    elif overall_score >= 0.9:
        grade = "A"
        emoji = "🟢"
    elif overall_score >= 0.8:
        grade = "B"
        emoji = "🟡"
    elif overall_score >= 0.7:
        grade = "C"
        emoji = "🟠"

    logger.info("Score: %.2f%%", overall_score * 100)
    logger.info("Grade: %s %s", emoji, grade)

    if overall_score < 0.9:
        logger.info("Suggestions:")
        logger.info("  - Increase DPI (recommended 200-300)")
        logger.info("  - Use hybrid or structure mode")
        logger.info("  - Preprocess images (denoising, binarization)")
    else:
        logger.info("OCR accuracy is excellent!")

    logger.info("")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        logger.info("Usage: python validate.py <OCR Result JSON> <Ground Truth TXT>")
        logger.info("Example: python validate.py output.json ground_truth.txt")
    else:
        validate_ocr_results(sys.argv[1], sys.argv[2])
