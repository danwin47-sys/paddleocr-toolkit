# -*- coding: utf-8 -*-
"""
性能優化測試 - 驗證記憶體和 I/O 優化效果
"""

import pytest
import time
import tracemalloc
import tempfile
import os
from pathlib import Path

try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

from paddleocr_toolkit.core.streaming_utils import (
    open_pdf_context,
    pdf_pages_generator,
    batch_pages_generator,
    StreamingPDFProcessor
)
from paddleocr_toolkit.core.buffered_writer import (
    BufferedWriter,
    BufferedJSONWriter,  
    write_text_efficient,
    write_json_efficient
)


class TestStreamingUtils:
    """測試串流處理工具"""
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_open_pdf_context(self):
        """測試 PDF context manager"""
        # 建立測試 PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            doc = fitz.open()
            page = doc.new_page(width=100, height=100)
            page.insert_text((10, 50), "Test")
            doc.save(temp_path)
            doc.close()
            
            # 測試 context manager
            with open_pdf_context(temp_path) as pdf_doc:
                assert len(pdf_doc) == 1
            
            # 確認已關閉
            # PDF 已在 context manager 中關閉
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_pdf_pages_generator(self):
        """測試頁面生成器"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            # 建立 3 頁測試 PDF
            doc = fitz.open()
            for i in range(3):
                page = doc.new_page(width=100, height=100)
                page.insert_text((10, 50), f"Page {i+1}")
            doc.save(temp_path)
            doc.close()
            
            # 測試生成器
            pages = list(pdf_pages_generator(temp_path, dpi=72))
            
            assert len(pages) == 3
            assert all(page_num == i for i, (page_num, _) in enumerate(pages))
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_batch_pages_generator(self):
        """測試批次生成器"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            # 建立 10 頁測試 PDF
            doc = fitz.open()
            for i in range(10):
                page = doc.new_page(width=100, height=100)
                page.insert_text((10, 50), f"Page {i+1}")
            doc.save(temp_path)
            doc.close()
            
            # 測試批次生成器 (batch_size=3)
            batches = list(batch_pages_generator(temp_path, dpi=72, batch_size=3))
            
            assert len(batches) == 4  # 10 頁分成 4 批 (3+3+3+1)
            assert len(batches[0]) == 3
            assert len(batches[-1]) == 1
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestBufferedWriter:
    """測試緩衝寫入器"""
    
    def test_buffered_writer_basic(self, tmp_path):
        """測試基本寫入功能"""
        output_file = tmp_path / "test.txt"
        
        lines = [f"Line {i}" for i in range(100)]
        
        with BufferedWriter(str(output_file), buffer_size=10) as writer:
            for line in lines:
                writer.write(line)
        
        # 驗證寫入
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Line 0" in content
            assert "Line 99" in content
    
    def test_buffered_json_writer(self, tmp_path):
        """測試 JSON 寫入器"""
        output_file = tmp_path / "test.json"
        
        objects = [{'id': i, 'text': f'Item {i}'} for i in range(50)]
        
        with BufferedJSONWriter(str(output_file), buffer_size=10) as writer:
            for obj in objects:
                writer.write(obj)
        
        # 驗證 JSON
        import json
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert len(data) == 50
            assert data[0]['id'] == 0
            assert data[49]['id'] == 49
    
    def test_write_text_efficient(self, tmp_path):
        """測試高效文字寫入"""
        output_file = tmp_path / "efficient.txt"
        
        lines = [f"Line {i}" for i in range(1000)]
        
        start_time = time.time()
        write_text_efficient(str(output_file), lines, buffer_size=100)
        elapsed = time.time() - start_time
        
        # 驗證快速
        assert elapsed < 1.0  # 應該很快
        
        # 驗證正確
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Line 0" in content
            assert "Line 999" in content


class TestMemoryOptimization:
    """測試記憶體優化效果"""
    
    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_memory_usage_streaming(self):
        """測試串流處理記憶體使用"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            # 建立較大的測試 PDF (20 頁)
            doc = fitz.open()
            for i in range(20):
                page = doc.new_page(width=595, height=842)
                page.insert_text((50, 50), f"Page {i+1}")
            doc.save(temp_path)
            doc.close()
            
            # 測量記憶體
            tracemalloc.start()
            
            # 串流處理（記憶體應該恆定）
            for page_num, image in pdf_pages_generator(temp_path, dpi=150):
                pass  # 模擬處理
            
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # 峰值記憶體應該小於 30MB（串流處理效果）
            # 如果不用串流，100頁會需要 200MB+
            assert peak < 30 * 1024 * 1024
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestIOOptimization:
    """測試 I/O 優化效果"""
    
    def test_buffered_write_speed(self, tmp_path):
        """測試緩衝寫入速度"""
        output_file = tmp_path / "speed_test.txt"
        
        # 10000 行文字
        lines = [f"This is line number {i} with some text" for i in range(10000)]
        
        # 測量時間
        start_time = time.time()
        write_text_efficient(str(output_file), lines, buffer_size=1000)
        elapsed = time.time() - start_time
        
        # 應該在 2 秒內完成
        assert elapsed < 2.0
        
        # 驗證正確性
        with open(output_file, 'r', encoding='utf-8') as f:
            written_lines = f.readlines()
            assert len(written_lines) == 10000
