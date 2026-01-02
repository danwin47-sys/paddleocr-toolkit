#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paddleocr benchmark - 性能??命令
"""

import json
import os
import time
from pathlib import Path
from typing import Optional

import psutil
from paddleocr_toolkit.utils.logger import logger


def run_benchmark(pdf_path: str, output: Optional[str] = None):
    """
    ?行性能基准??

    Args:
        pdf_path: PDF文件路?
        output: ?出?告路?
    """
    from paddle_ocr_tool import PaddleOCRTool

    logger.info("=" * 70)
    logger.info(" PaddleOCR Toolkit Benchmark")
    logger.info("=" * 70)
    logger.info("Target file: %s", pdf_path)
    logger.info("")

    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        logger.error("File not found: %s", pdf_path)
        return

    # ???景
    scenarios = [
        {"name": "Basic (DPI 150)", "mode": "basic", "dpi": 150},
        {"name": "Basic (DPI 200)", "mode": "basic", "dpi": 200},
        {"name": "Hybrid (DPI 150)", "mode": "hybrid", "dpi": 150},
        {"name": "Hybrid (DPI 200)", "mode": "hybrid", "dpi": 200},
    ]

    results = []
    process = psutil.Process(os.getpid())

    for i, scenario in enumerate(scenarios, 1):
        logger.info("[%d/%d] Scenario: %s", i, len(scenarios), scenario['name'])
        logger.info("-" * 70)

        # ??初始?存
        initial_memory = process.memory_info().rss / 1024 / 1024

        # 初始化OCR
        logger.info("  Initializing OCR engine...")
        init_start = time.time()
        ocr_tool = PaddleOCRTool(mode=scenario["mode"])
        init_time = time.time() - init_start

        post_init_memory = process.memory_info().rss / 1024 / 1024

        # ?理PDF
        logger.info("  Processing PDF...")
        process_start = time.time()
        all_results, _ = ocr_tool.process_pdf(
            str(pdf_file),
            dpi=scenario["dpi"],
        )
        process_time = time.time() - process_start

        # ??峰值?存
        peak_memory = process.memory_info().rss / 1024 / 1024

        # ??
        total_pages = len(all_results)
        total_texts = sum(len(page) for page in all_results)

        result = {
            "scenario": scenario["name"],
            "mode": scenario["mode"],
            "dpi": scenario["dpi"],
            "pages": total_pages,
            "texts": total_texts,
            "init_time": round(init_time, 2),
            "process_time": round(process_time, 2),
            "total_time": round(init_time + process_time, 2),
            "time_per_page": round(process_time / total_pages, 2)
            if total_pages > 0
            else 0,
            "initial_memory": round(initial_memory, 1),
            "peak_memory": round(peak_memory, 1),
            "memory_used": round(peak_memory - initial_memory, 1),
        }

        results.append(result)

        # ?示?果
        # ?示?果
        logger.info("  Done")
        logger.info("    Pages: %d", total_pages)
        logger.info("    Texts: %d", total_texts)
        logger.info("    Time: %.2fs (%.2fs/page)", result['total_time'], result['time_per_page'])
        logger.info("    Memory: %.1fMB", result['memory_used'])

    # ?示??
    logger.info("=" * 70)
    logger.info(" Benchmark Summary")
    logger.info("=" * 70)
    logger.info("")
    logger.info("%-25s %10s %12s %10s", "Scenario", "Time", "Speed", "Memory")
    logger.info("-" * 70)

    for result in results:
        logger.info(
            "%-25s %9.2fs %9.2fs/p %9.1fMB",
            result['scenario'],
            result['total_time'],
            result['time_per_page'],
            result['memory_used']
        )

    logger.info("=" * 70)

    # 最快的scene
    fastest = min(results, key=lambda x: x["time_per_page"])
    logger.info("Fastest: %s (%.2fs/page)", fastest['scenario'], fastest['time_per_page'])

    # 最省?存
    lightest = min(results, key=lambda x: x["memory_used"])
    logger.info("Lowest Memory: %s (%.1fMB)", lightest['scenario'], lightest['memory_used'])

    # 保存?果
    if output:
        output_path = Path(output)
    else:
        output_path = Path("benchmark_results.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info("Report saved: %s", output_path)
    logger.info("")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        logger.info("Usage: python benchmark.py <pdf_file> [output_file]")
        logger.info("Example: python benchmark.py test.pdf results.json")
    else:
        pdf_path = sys.argv[1]
        output = sys.argv[2] if len(sys.argv) > 2 else None
        run_benchmark(pdf_path, output)
