# -*- coding: utf-8 -*-
"""
效能基準測試套件

測試不同場景下的 OCR 效能。
"""

import time
from pathlib import Path
from typing import Dict, List
import json

import pytest


class PerformanceBenchmark:
    """效能基準測試基類"""
    
    def __init__(self):
        self.results: List[Dict] = []
    
    def measure_time(self, func, *args, **kwargs):
        """測量函式執行時間"""
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        return result, elapsed
    
    def record_result(self, test_name: str, elapsed: float, **metadata):
        """記錄測試結果"""
        self.results.append({
            "test_name": test_name,
            "elapsed_seconds": elapsed,
            "timestamp": time.time(),
            **metadata
        })
    
    def save_results(self, output_path: str):
        """儲存結果到 JSON"""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)


class TestPDFProcessingBenchmark:
    """PDF 處理效能基準測試"""
    
    @pytest.fixture
    def benchmark(self):
        """建立基準測試例項"""
        return PerformanceBenchmark()
    
    @pytest.mark.benchmark
    @pytest.mark.skipif(not Path("test_data").exists(), reason="需要測試資料")
    def test_small_pdf_performance(self, benchmark):
        """測試小型 PDF (< 10 頁) 效能"""
        from paddle_ocr_facade import PaddleOCRFacade
        
        facade = PaddleOCRFacade(mode="basic")
        
        # 假設有測試 PDF
        test_pdf = "test_data/small.pdf"
        if not Path(test_pdf).exists():
            pytest.skip("測試 PDF 不存在")
        
        result, elapsed = benchmark.measure_time(
            facade.process_pdf,
            test_pdf
        )
        
        benchmark.record_result(
            "small_pdf_basic_mode",
            elapsed,
            pages=result.get("pages_processed", 0),
            mode="basic"
        )
        
        # 斷言效能在合理範圍內（< 30 秒）
        assert elapsed < 30, f"處理時間過長: {elapsed:.2f}s"
    
    @pytest.mark.benchmark
    @pytest.mark.skipif(not Path("test_data").exists(), reason="需要測試資料")
    def test_medium_pdf_performance(self, benchmark):
        """測試中型 PDF (10-50 頁) 效能"""
        from paddle_ocr_facade import PaddleOCRFacade
        
        facade = PaddleOCRFacade(mode="hybrid")
        
        test_pdf = "test_data/medium.pdf"
        if not Path(test_pdf).exists():
            pytest.skip("測試 PDF 不存在")
        
        result, elapsed = benchmark.measure_time(
            facade.process_pdf,
            test_pdf
        )
        
        benchmark.record_result(
            "medium_pdf_hybrid_mode",
            elapsed,
            pages=result.get("pages_processed", 0),
            mode="hybrid"
        )
        
        # 斷言效能在合理範圍內（< 120 秒）
        assert elapsed < 120, f"處理時間過長: {elapsed:.2f}s"


class TestSemanticProcessingBenchmark:
    """語義處理效能基準測試"""
    
    @pytest.fixture
    def benchmark(self):
        """建立基準測試例項"""
        return PerformanceBenchmark()
    
    @pytest.mark.benchmark
    def test_text_correction_performance(self, benchmark):
        """測試文字修正效能"""
        from unittest.mock import Mock, patch
        
        with patch("paddleocr_toolkit.processors.semantic_processor.HAS_REQUESTS", True):
            with patch("paddleocr_toolkit.llm.llm_client.HAS_REQUESTS", True):
                from paddleocr_toolkit.processors.semantic_processor import SemanticProcessor
                from paddleocr_toolkit.llm import OllamaClient
                
                mock_client = Mock(spec=OllamaClient)
                mock_client.generate.return_value = "修正後的文字"
                
                processor = SemanticProcessor(llm_client=mock_client)
                
                test_text = "這是一段包含錯誤的OCR文字" * 10
                
                result, elapsed = benchmark.measure_time(
                    processor.correct_text,
                    test_text
                )
                
                benchmark.record_result(
                    "semantic_text_correction",
                    elapsed,
                    text_length=len(test_text)
                )
                
                # 斷言效能在合理範圍內（< 5 秒）
                assert elapsed < 5, f"處理時間過長: {elapsed:.2f}s"


def generate_performance_report(results_path: str = "benchmark_results.json"):
    """生成效能報告"""
    if not Path(results_path).exists():
        print("沒有找到基準測試結果")
        return
    
    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)
    
    print("\n" + "="*60)
    print("效能基準測試報告")
    print("="*60)
    
    for result in results:
        print(f"\n測試: {result['test_name']}")
        print(f"  執行時間: {result['elapsed_seconds']:.2f} 秒")
        if "pages" in result:
            print(f"  處理頁數: {result['pages']}")
            print(f"  每頁平均: {result['elapsed_seconds']/result['pages']:.2f} 秒")
        if "mode" in result:
            print(f"  模式: {result['mode']}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    # 執行基準測試
    pytest.main([__file__, "-v", "-m", "benchmark"])
    
    # 生成報告
    generate_performance_report()
