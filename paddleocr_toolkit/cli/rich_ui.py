#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - CLI 美化模組 v1.2.0
使用 rich 庫提供超炫的命令列介面
支持跨平台（修复Windows编码问题）
"""

import io
import sys

# ═══════════════════════════════════════════════════════════
# Windows 編碼修復 (v1.2.0新增) - 避免在測試環境中執行
# ═══════════════════════════════════════════════════════════
if sys.platform == "win32" and "pytest" not in sys.modules:
    try:
        # 強制 UTF-8 輸出
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True
        )
    except Exception:
        pass  # 如果失敗，繼續使用默認編碼

# ═══════════════════════════════════════════════════════════
# Rich庫導入
# ═══════════════════════════════════════════════════════════
try:
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
        TimeRemainingColumn,
    )
    from rich.table import Table

    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# ═══════════════════════════════════════════════════════════
# 跨平台圖標定義 (v1.2.0新增)
# ═══════════════════════════════════════════════════════════
if sys.platform == "win32":
    # Windows ASCII 替代方案
    ICONS = {
        "logo": "OCR",
        "success": "[OK]",
        "error": "[X]",
        "warning": "[!]",
        "info": "[i]",
        "processing": "[>]",
        "page": "#",
        "text": "T",
        "confidence": "%",
        "time": "t",
        "excellent": "+++",
        "good": "++",
        "fair": "+",
        "poor": "-",
    }
else:
    # Unix/Mac EM用oji
    ICONS = {
        "logo": "🔍",
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "processing": "⚙️",
        "page": "📄",
        "text": "📝",
        "confidence": "🎯",
        "time": "⏱️",
        "excellent": "🟢",
        "good": "🟡",
        "fair": "🟠",
        "poor": "🔴",
    }

if HAS_RICH:
    console = Console()
else:
    console = None

# ═══════════════════════════════════════════════════════════
# 公共函數
# ═══════════════════════════════════════════════════════════


def print_banner():
    """顯示啟動橫幅"""
    if not HAS_RICH:
        print("=== PaddleOCR Toolkit ===")
        return

    banner = f"""
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║     {ICONS['logo']}  PaddleOCR Toolkit  {ICONS['logo']}                         ║
    ║                                                       ║
    ║     專業級 OCR 文件辨識與處理工具                      ║
    ║     v1.2.0 | 測試覆蓋率: 84% | 391個測試通過          ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """

    console.print(banner, style="bold cyan")


def print_success(message: str):
    """顯示成功訊息"""
    icon = ICONS["success"]
    if not HAS_RICH:
        print(f"{icon} {message}")
        return

    console.print(f"{icon} {message}", style="bold green")


def print_error(message: str):
    """顯示錯誤訊息"""
    icon = ICONS["error"]
    if not HAS_RICH:
        print(f"{icon} {message}")
        return

    console.print(f"{icon} {message}", style="bold red")


def print_warning(message: str):
    """顯示警告訊息"""
    icon = ICONS["warning"]
    if not HAS_RICH:
        print(f"{icon} {message}")
        return

    console.print(f"{icon} {message}", style="bold yellow")


def print_info(message: str):
    """顯示資訊訊息"""
    icon = ICONS["info"]
    if not HAS_RICH:
        print(f"{icon} {message}")
        return

    console.print(f"{icon} {message}", style="bold blue")


def create_results_table(results_data: list):
    """
    創建OCR結果表格

    Args:
        results_data: [(頁數, 文字數, 平均信心度), ...]
    """
    if not HAS_RICH:
        return None

    table = Table(
        title=f"{ICONS['page']} OCR 處理結果統計",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )

    table.add_column("頁數", justify="center", style="cyan", no_wrap=True)
    table.add_column("識別文字數", justify="right", style="green")
    table.add_column("平均信心度", justify="right", style="yellow")
    table.add_column("狀態", justify="center")

    for page_num, text_count, avg_conf in results_data:
        # 根據信心度選擇狀態
        if avg_conf >= 0.9:
            status = f"{ICONS['excellent']} 優秀"
        elif avg_conf >= 0.7:
            status = f"{ICONS['good']} 良好"
        else:
            status = f"{ICONS['poor']} 需檢查"

        table.add_row(str(page_num), str(text_count), f"{avg_conf:.1%}", status)

    return table


def create_progress_bar(total: int, description: str = "處理中"):
    """
    創建進度條

    Args:
        total: 總項目數
        description: 描述文字
    """
    if not HAS_RICH:
        return None

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(complete_style="green", finished_style="bold green"),
        TaskProgressColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
        console=console,
    )

    return progress


def print_performance_summary(stats: dict):
    """
    顯示性能摘要

    Args:
        stats: {
            'total_pages': int,
            'total_time': float,
            'avg_time_per_page': float,
            'peak_memory_mb': float,
            'total_texts': int
        }
    """
    if not HAS_RICH:
        print("\n=== 性能摘要 ===")
        for key, value in stats.items():
            print(f"{key}: {value}")
        return

    panel_content = f"""
    {ICONS['page']} 總頁數: [bold cyan]{stats.get('total_pages', 0)}[/bold cyan]
    {ICONS['time']} 總時間: [bold yellow]{stats.get('total_time', 0):.2f}s[/bold yellow]
    {ICONS['processing']} 平均速度: [bold green]{stats.get('avg_time_per_page', 0):.2f}s/頁[/bold green]
    峰值記憶體: [bold magenta]{stats.get('peak_memory_mb', 0):.1f}MB[/bold magenta]
    {ICONS['text']} 識別文字: [bold blue]{stats.get('total_texts', 0)}個[/bold blue]
    """

    panel = Panel(
        panel_content,
        title=f"{ICONS['confidence']} 性能摘要",
        border_style="bold green",
        box=box.DOUBLE,
    )

    console.print(panel)


def print_logo():
    """顯示ASCII Logo"""
    if not HAS_RICH:
        print("PaddleOCR Toolkit")
        return

    logo = """
    ██████╗  ██████╗ ██████╗     ████████╗ ██████╗  ██████╗ ██╗     
    ██╔══██╗██╔═══██╗██╔══██╗    ╚══██╔══╝██╔═══██╗██╔═══██╗██║     
    ██████╔╝██║   ██║██████╔╝       ██║   ██║   ██║██║   ██║██║     
    ██╔═══╝ ██║   ██║██╔══██╗       ██║   ██║   ██║██║   ██║██║     
    ██║     ╚██████╔╝██║  ██║       ██║   ╚██████╔╝╚██████╔╝███████╗
    ╚═╝      ╚═════╝ ╚═╝  ╚═╝       ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝
    """

    console.print(logo, style="bold cyan")


# ═══════════════════════════════════════════════════════════
# 示例使用
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    if HAS_RICH:
        print_logo()
        print_banner()

        print_success("模組載入成功！")
        print_info("開始處理 PDF 文件...")
        print_warning("DPI 設定較低，可能影響識別率")

        # 示例結果表格
        results = [
            (1, 145, 0.95),
            (2, 132, 0.88),
            (3, 167, 0.92),
        ]

        table = create_results_table(results)
        console.print(table)

        # 示例性能摘要
        stats = {
            "total_pages": 3,
            "total_time": 12.5,
            "avg_time_per_page": 4.17,
            "peak_memory_mb": 245.8,
            "total_texts": 444,
        }

        print_performance_summary(stats)

    else:
        print("請安裝 rich: pip install rich")
