#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ PaddleOCR Toolkit 性能基準測試
測試不同PDF大小、DPI設定的處理速度和記憶體使用

使用方法:
    python benchmark.py
    python benchmark.py --mode structure --dpi 300
"""

import time
import psutil
import os
import sys
from pathlib import Path
from typing import Dict, List
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

from paddle_ocr_tool import PaddleOCRTool

# 嘗試導入rich用於漂亮輸出
try:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False


class BenchmarkRunner:
    """性能基準測試執行器"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.results = []
    
    def create_test_pdf(self, num_pages: int) -> str:
        """創建測試PDF"""
        if not HAS_FITZ:
            raise ImportError("需要 PyMuPDF")
        
        temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        doc = fitz.open()
        for i in range(num_pages):
            page = doc.new_page(width=595, height=842)  # A4
            # 添加一些文字
            text = f"測試頁面 {i+1}\n" * 20
            page.insert_text((50, 50), text, fontsize=12)
        
        doc.save(temp_path)
        doc.close()
        
        return temp_path
    
    def measure_memory(self) -> float:
        """測量當前記憶體使用(MB)"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def run_benchmark(
        self, 
        pdf_path: str, 
        mode: str = "basic", 
        dpi: int = 150
    ) -> Dict:
        """執行基準測試"""
        print(f"\n🧪 測試: {Path(pdf_path).name}")
        print(f"   模式: {mode}, DPI: {dpi}")
        
        # 記錄初始記憶體
        initial_memory = self.measure_memory()
        
        # 初始化OCR
        print("   ⏱️  初始化OCR引擎...")
        init_start = time.time()
        ocr_tool = PaddleOCRTool(mode=mode, device="gpu")
        init_time = time.time() - init_start
        
        post_init_memory = self.measure_memory()
        
        # 執行OCR
        print("   📄 處理PDF...")
        process_start = time.time()
        all_results, _ = ocr_tool.process_pdf(
            pdf_path,
            dpi=dpi,
            show_progress=False
        )
        process_time = time.time() - process_start
        
        # 記錄峰值記憶體
        peak_memory = self.measure_memory()
        
        # 計算統計
        total_pages = len(all_results)
        total_texts = sum(len(page_results) for page_results in all_results)
        
        result = {
            'pdf': Path(pdf_path).name,
            'mode': mode,
            'dpi': dpi,
            'pages': total_pages,
            'texts': total_texts,
            'init_time': init_time,
            'process_time': process_time,
            'total_time': init_time + process_time,
            'time_per_page': process_time / total_pages if total_pages > 0 else 0,
            'initial_memory': initial_memory,
            'post_init_memory': post_init_memory,
            'peak_memory': peak_memory,
            'memory_used': peak_memory - initial_memory,
        }
        
        print(f"   ✅ 完成: {process_time:.2f}s ({result['time_per_page']:.2f}s/頁)")
        print(f"   💾 記憶體: {result['memory_used']:.1f}MB")
        
        return result
    
    def print_results_table(self):
        """列印結果表格"""
        if not self.results:
            print("沒有測試結果")
            return
        
        if HAS_RICH:
            self._print_rich_table()
        else:
            self._print_plain_table()
    
    def _print_rich_table(self):
        """使用rich列印漂亮的表格"""
        table = Table(
            title="⚡ 性能基準測試結果",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("測試", style="cyan")
        table.add_column("頁數", justify="right", style="blue")
        table.add_column("總時間", justify="right", style="yellow")
        table.add_column("速度", justify="right", style="green")
        table.add_column("記憶體", justify="right", style="red")
        table.add_column("文字數", justify="right", style="magenta")
        
        for r in self.results:
            test_name = f"{r['mode']}/{r['dpi']}"
            table.add_row(
                test_name,
                str(r['pages']),
                f"{r['total_time']:.2f}s",
                f"{r['time_per_page']:.2f}s/頁",
                f"{r['memory_used']:.1f}MB",
                str(r['texts'])
            )
        
        console.print("\n")
        console.print(table)
    
    def _print_plain_table(self):
        """列印純文字表格"""
        print("\n" + "="*80)
        print("性能基準測試結果")
        print("="*80)
        print(f"{'測試':<20} {'頁數':<8} {'總時間':<12} {'速度':<15} {'記憶體':<12} {'文字數':<8}")
        print("-"*80)
        
        for r in self.results:
            test_name = f"{r['mode']}/{r['dpi']}"
            print(f"{test_name:<20} {r['pages']:<8} {r['total_time']:.2f}s      "
                  f"{r['time_per_page']:.2f}s/頁     {r['memory_used']:.1f}MB     {r['texts']:<8}")
        
        print("="*80)


def main():
    """主程式"""
    print("🚀 PaddleOCR Toolkit 性能基準測試")
    print("="*50)
    
    if not HAS_FITZ:
        print("❌ 需要安裝 PyMuPDF: pip install PyMuPDF")
        return
    
    runner = BenchmarkRunner()
    
    # 測試場景
    test_scenarios = [
        # (頁數, 模式, DPI)
        (10, "basic", 150),
        (10, "basic", 200),
        (10, "hybrid", 150),
        (50, "basic", 150),
    ]
    
    print(f"\n📋 將執行 {len(test_scenarios)} 個測試場景")
    print("⚠️  這可能需要幾分鐘時間...\n")
    
    temp_pdfs = []
    
    try:
        for i, (pages, mode, dpi) in enumerate(test_scenarios, 1):
            print(f"\n{'='*50}")
            print(f"場景 {i}/{len(test_scenarios)}")
            print(f"{'='*50}")
            
            # 創建或重用測試PDF
            pdf_path = None
            for temp_pdf, temp_pages in temp_pdfs:
                if temp_pages == pages:
                    pdf_path = temp_pdf
                    break
            
            if not pdf_path:
                print(f"📝 創建 {pages}頁 測試PDF...")
                pdf_path = runner.create_test_pdf(pages)
                temp_pdfs.append((pdf_path, pages))
            
            # 執行測試
            result = runner.run_benchmark(pdf_path, mode, dpi)
            runner.results.append(result)
        
        # 顯示結果
        runner.print_results_table()
        
        # 總結
        print("\n📊 測試總結:")
        avg_time_per_page = sum(r['time_per_page'] for r in runner.results) / len(runner.results)
        avg_memory = sum(r['memory_used'] for r in runner.results) / len(runner.results)
        
        print(f"   平均速度: {avg_time_per_page:.2f}s/頁")
        print(f"   平均記憶體: {avg_memory:.1f}MB")
        print(f"   最快測試: {min(runner.results, key=lambda x: x['time_per_page'])['mode']}/{min(runner.results, key=lambda x: x['time_per_page'])['dpi']}")
        print(f"   最省記憶體: {min(runner.results, key=lambda x: x['memory_used'])['mode']}/{min(runner.results, key=lambda x: x['memory_used'])['dpi']}")
        
    finally:
        # 清理臨時檔案
        for temp_pdf, _ in temp_pdfs:
            try:
                os.remove(temp_pdf)
            except:
                pass


if __name__ == "__main__":
    main()
