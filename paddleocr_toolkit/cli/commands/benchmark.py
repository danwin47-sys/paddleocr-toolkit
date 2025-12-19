#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paddleocr benchmark - 效能??命令
"""

import json
import os
import time
from pathlib import Path
from typing import Optional

import psutil


def run_benchmark(pdf_path: str, output: Optional[str] = None):
    """
    ?行效能基準??

    Args:
        pdf_path: PDF檔案路?
        output: ?出?告路?
    """
    from paddle_ocr_tool import PaddleOCRTool

    print("\n" + "=" * 70)
    print(" PaddleOCR Toolkit 效能基準??")
    print("=" * 70)
    print(f"\n??檔案: {pdf_path}")
    print()

    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"??: 檔案不存在: {pdf_path}")
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
        print(f"\n[{i}/{len(scenarios)}] ??: {scenario['name']}")
        print("─" * 70)

        # ??初始?存
        initial_memory = process.memory_info().rss / 1024 / 1024

        # 初始化OCR
        print("  初始化OCR引擎...")
        init_start = time.time()
        ocr_tool = PaddleOCRTool(mode=scenario["mode"])
        init_time = time.time() - init_start

        post_init_memory = process.memory_info().rss / 1024 / 1024

        # ?理PDF
        print("  ?理PDF...")
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
        print(f"  ? 完成")
        print(f"    ??: {total_pages}")
        print(f"    文字: {total_texts}")
        print(f"    ??: {result['total_time']}s ({result['time_per_page']}s/?)")
        print(f"    ?存: {result['memory_used']}MB")

    # ?示??
    print("\n" + "=" * 70)
    print(" ???果??")
    print("=" * 70)
    print()
    print(f"{'?景':<25} {'???':>10} {'速度':>12} {'?存':>10}")
    print("─" * 70)

    for result in results:
        print(
            f"{result['scenario']:<25} "
            f"{result['total_time']:>9.2f}s "
            f"{result['time_per_page']:>9.2f}s/? "
            f"{result['memory_used']:>9.1f}MB"
        )

    print("=" * 70)

    # 最快的scene
    fastest = min(results, key=lambda x: x["time_per_page"])
    print(f"\n最快: {fastest['scenario']} ({fastest['time_per_page']}s/?)")

    # 最省?存
    lightest = min(results, key=lambda x: x["memory_used"])
    print(f"最省記憶體: {lightest['scenario']} ({lightest['memory_used']}MB)")

    # 儲存結果
    if output:
        output_path = Path(output)
    else:
        # 儲存結果
        output_path = Path(f"benchmark_{int(time.time())}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"\n📊 報告已儲存: {output_path}")
    print()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("使用方法: python benchmark.py <pdf檔案> [?出檔案]")
        print("範例: python benchmark.py test.pdf results.json")
    else:
        pdf_path = sys.argv[1]
        output = sys.argv[2] if len(sys.argv) > 2 else None
        run_benchmark(pdf_path, output)
