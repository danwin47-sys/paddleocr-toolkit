#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端整合测试
测试完整的OCR工作流程
"""

import pytest
import tempfile
import os
from pathlib import Path

try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

from paddle_ocr_tool import PaddleOCRTool


@pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
class TestEndToEndWorkflow:
    """端到端工作流程测试"""
    
    def test_complete_pdf_workflow(self):
        """测试完整PDF处理流程"""
        # 创建测试PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_pdf = f.name
        
        try:
            # 1. 创建测试PDF
            doc = fitz.open()
            page = doc.new_page(width=595, height=842)
            page.insert_text((50, 50), "测试文字\nTest Text")
            doc.save(temp_pdf)
            doc.close()
            
            # 2. 初始化OCR
            ocr_tool = PaddleOCRTool(mode="basic")
            
            # 3. 处理PDF
            all_results, _ = ocr_tool.process_pdf(temp_pdf, show_progress=False)
            
            # 4. 验证结果
            assert len(all_results) == 1
            assert len(all_results[0]) > 0
            
            # 5. 提取文字
            text = ocr_tool.get_text(all_results)
            assert len(text) > 0
            
        finally:
            if os.path.exists(temp_pdf):
                os.remove(temp_pdf)
    
    def test_searchable_pdf_generation(self):
        """测试可搜寻PDF生成"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            input_pdf = f.name
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            output_pdf = f.name
        
        try:
            # 创建输入PDF
            doc = fitz.open()
            page = doc.new_page(width=595, height=842)
            page.insert_text((50, 50), "Searchable Text")
            doc.save(input_pdf)
            doc.close()
            
            # 生成可搜寻PDF
            ocr_tool = PaddleOCRTool(mode="basic")
            results, pdf_gen = ocr_tool.process_pdf(
                input_pdf,
                output_searchable_pdf=output_pdf,
                show_progress=False
            )
            
            # 验证输出文件存在
            assert os.path.exists(output_pdf)
            assert os.path.getsize(output_pdf) > 0
            
        finally:
            for path in [input_pdf, output_pdf]:
                if os.path.exists(path):
                    os.remove(path)
    
    def test_batch_processing(self):
        """测试批次处理"""
        temp_files = []
        
        try:
            # 创建多个测试PDF
            for i in range(3):
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                    temp_pdf = f.name
                    temp_files.append(temp_pdf)
                
                doc = fitz.open()
                page = doc.new_page(width=595, height=842)
                page.insert_text((50, 50), f"Document {i+1}")
                doc.save(temp_pdf)
                doc.close()
            
            # 批次处理
            ocr_tool = PaddleOCRTool(mode="basic")
            
            all_results = []
            for pdf_file in temp_files:
                results, _ = ocr_tool.process_pdf(pdf_file, show_progress=False)
                all_results.append(results)
            
            # 验证结果
            assert len(all_results) == 3
            assert all(len(r) > 0 for r in all_results)
            
        finally:
            for path in temp_files:
                if os.path.exists(path):
                    os.remove(path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
