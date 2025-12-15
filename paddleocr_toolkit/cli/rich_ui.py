#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - CLI ¬ü₪ֶ¼ׂ²ױ v1.2.0
¨ֿ¥־ rich ®w´£¨ׁ¶W¬¯×÷©R¥O¦C₪¶­±
₪ה«ש¸ף¥­¥x¡]­׳־`Windows????¡^
"""

import io
import sys

# שששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששש
# Windows ½s½X­׳´_ (v1.2.0·s¼W) - ֱ׳§K¦b´ת¸ױְפ¹ׂ₪₪°ץ¦ז
# שששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששש
if sys.platform == "win32" and "pytest" not in sys.modules:
    try:
        # ±j¨מ UTF-8 ¿י¥X
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True
        )
    except Exception:
        pass  # ¦p×G¥¢±ׁ¡Aִ~ִע¨ֿ¥־ְq»{½s½X

# שששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששש
# Rich®w¾ֹ₪J
# שששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששש
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

# שששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששש
# ¸ף¥­¥x¹ֿ¼׀©w¸q (v1.2.0·s¼W)
# שששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששש
if sys.platform == "win32":
    # Windows ASCII ´ְ¥N₪ט®׳
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
    # Unix/Mac EM¥־oji
    ICONS = {
        "logo": "??",
        "success": "?",
        "error": "?",
        "warning": "??",
        "info": "??",
        "processing": "??",
        "page": "??",
        "text": "??",
        "confidence": "??",
        "time": "??",
        "excellent": "??",
        "good": "??",
        "fair": "??",
        "poor": "??",
    }

if HAS_RICH:
    console = Console()
else:
    console = None

# שששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששש
# ₪½¦@¨ח¼ֶ
# שששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששש


def print_banner():
    """ֵד¥Ü±ׂ°Ê¾מ´T"""
    if not HAS_RICH:
        print("=== PaddleOCR Toolkit ===")
        return

    banner = f"""
    שÝשששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששß
    שר                                                       שר
    שר     {ICONS['logo']}  PaddleOCR Toolkit  {ICONS['logo']}                         שר
    שר                                                       שר
    שר     ±M·~¯ֵ OCR ₪ו¥ף¿כֳׁ»P³B²z₪u¨ד                      שר
    שר     v1.2.0 | ´ת¸ױֲ׀»\²v: 84% | 391­׃´ת¸ױ³q¹L          שר
    שר                                                       שר
    שדשששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששו
    """

    console.print(banner, style="bold cyan")


def print_success(message: str):
    """ֵד¥Ü¦¨¥\°T®§"""
    icon = ICONS["success"]
    if not HAS_RICH:
        print(f"{icon} {message}")
        return

    console.print(f"{icon} {message}", style="bold green")


def print_error(message: str):
    """ֵד¥Ü¿ש»~°T®§"""
    icon = ICONS["error"]
    if not HAS_RICH:
        print(f"{icon} {message}")
        return

    console.print(f"{icon} {message}", style="bold red")


def print_warning(message: str):
    """ֵד¥Üִµ§i°T®§"""
    icon = ICONS["warning"]
    if not HAS_RICH:
        print(f"{icon} {message}")
        return

    console.print(f"{icon} {message}", style="bold yellow")


def print_info(message: str):
    """ֵד¥Ü¸ך°T°T®§"""
    icon = ICONS["info"]
    if not HAS_RICH:
        print(f"{icon} {message}")
        return

    console.print(f"{icon} {message}", style="bold blue")


def create_results_table(results_data: list):
    """
    ³׀«״OCRµ²×G×ם®ז

    Args:
        results_data: [(­¶¼ֶ, ₪ו¦r¼ֶ, ¥­§¡«H₪ß«׳), ...]
    """
    if not HAS_RICH:
        return None

    table = Table(
        title=f"{ICONS['page']} OCR ³B²zµ²×G²־­p",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )

    table.add_column("­¶¼ֶ", justify="center", style="cyan", no_wrap=True)
    table.add_column("ֳׁ§O₪ו¦r¼ֶ", justify="right", style="green")
    table.add_column("¥­§¡«H₪ß«׳", justify="right", style="yellow")
    table.add_column("×¬÷A", justify="center")

    for page_num, text_count, avg_conf in results_data:
        # ®Ú¾Ú«H₪ß«׳¿ן¾Ü×¬÷A
        if avg_conf >= 0.9:
            status = f"{ICONS['excellent']} ְu¨q"
        elif avg_conf >= 0.7:
            status = f"{ICONS['good']} ¨}¦n"
        else:
            status = f"{ICONS['poor']} »Ýְֻ¬d"

        table.add_row(str(page_num), str(text_count), f"{avg_conf:.1%}", status)

    return table


def create_progress_bar(total: int, description: str = "³B²z₪₪"):
    """
    ³׀«״¶i«׳±ר

    Args:
        total: ֱ`¶µ¥״¼ֶ
        description: ´y­z₪ו¦r
    """
    if not HAS_RICH:
        return None

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(complete_style="green", finished_style="bold green"),
        TaskProgressColumn(),
        TextColumn("¡E"),
        TimeRemainingColumn(),
        console=console,
    )

    return progress


def print_performance_summary(stats: dict):
    """
    ֵד¥Ü©Ê¯א÷K­n

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
        print("\n=== ©Ê¯א÷K­n ===")
        for key, value in stats.items():
            print(f"{key}: {value}")
        return

    panel_content = f"""
    {ICONS['page']} ֱ`­¶¼ֶ: [bold cyan]{stats.get('total_pages', 0)}[/bold cyan]
    {ICONS['time']} ֱ`®ֹ¶¡: [bold yellow]{stats.get('total_time', 0):.2f}s[/bold yellow]
    {ICONS['processing']} ¥­§¡³t«׳: [bold green]{stats.get('avg_time_per_page', 0):.2f}s/­¶[/bold green]
    ®p­ָ°O¾׀ֵי: [bold magenta]{stats.get('peak_memory_mb', 0):.1f}MB[/bold magenta]
    {ICONS['text']} ֳׁ§O₪ו¦r: [bold blue]{stats.get('total_texts', 0)}­׃[/bold blue]
    """

    panel = Panel(
        panel_content,
        title=f"{ICONS['confidence']} ©Ê¯א÷K­n",
        border_style="bold green",
        box=box.DOUBLE,
    )

    console.print(panel)


def print_logo():
    """ֵד¥ÜASCII Logo"""
    if not HAS_RICH:
        print("PaddleOCR Toolkit")
        return

    logo = """
    ¢i¢i¢i¢i¢i¢iשß  ¢i¢i¢i¢i¢i¢iשß ¢i¢i¢i¢i¢i¢iשß     ¢i¢i¢i¢i¢i¢i¢i¢iשß ¢i¢i¢i¢i¢i¢iשß  ¢i¢i¢i¢i¢i¢iשß ¢i¢iשß     
    ¢i¢iשÝשששש¢i¢iשß¢i¢iשÝשששששש¢i¢iשß¢i¢iשÝשששש¢i¢iשß    שדשששש¢i¢iשÝשששששו¢i¢iשÝשששששש¢i¢iשß¢i¢iשÝשששששש¢i¢iשß¢i¢iשר     
    ¢i¢i¢i¢i¢i¢iשÝשו¢i¢iשר   ¢i¢iשר¢i¢i¢i¢i¢i¢iשÝשו       ¢i¢iשר   ¢i¢iשר   ¢i¢iשר¢i¢iשר   ¢i¢iשר¢i¢iשר     
    ¢i¢iשÝשששששששו ¢i¢iשר   ¢i¢iשר¢i¢iשÝשששש¢i¢iשß       ¢i¢iשר   ¢i¢iשר   ¢i¢iשר¢i¢iשר   ¢i¢iשר¢i¢iשר     
    ¢i¢iשר     שד¢i¢i¢i¢i¢i¢iשÝשו¢i¢iשר  ¢i¢iשר       ¢i¢iשר   שד¢i¢i¢i¢i¢i¢iשÝשושד¢i¢i¢i¢i¢i¢iשÝשו¢i¢i¢i¢i¢i¢i¢iשß
    שדשששו      שדשששששששששששו שדשששו  שדשששו       שדשששו    שדשששששששששששו  שדשששששששששששו שדשששששששששששששו
    """

    console.print(logo, style="bold cyan")


# שששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששש
# ¥Ü¨ׂ¨ֿ¥־
# שששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששששש
if __name__ == "__main__":
    if HAS_RICH:
        print_logo()
        print_banner()

        print_success("¼ׂ²ױ¸ü₪J¦¨¥\¡I")
        print_info("¶}©l³B²z PDF ₪ו¥ף...")
        print_warning("DPI ³]©w¸û§C¡A¥i¯א¼vֵTֳׁ§O²v")

        # ¥Ü¨ׂµ²×G×ם®ז
        results = [
            (1, 145, 0.95),
            (2, 132, 0.88),
            (3, 167, 0.92),
        ]

        table = create_results_table(results)
        console.print(table)

        # ¥Ü¨ׂ©Ê¯א÷K­n
        stats = {
            "total_pages": 3,
            "total_time": 12.5,
            "avg_time_per_page": 4.17,
            "peak_memory_mb": 245.8,
            "total_texts": 444,
        }

        print_performance_summary(stats)

    else:
        print("½׀¦w¸ֻ rich: pip install rich")
