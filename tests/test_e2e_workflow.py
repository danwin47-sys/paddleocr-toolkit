#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端整合测试
测试完整的OCR工作流程（使用 PaddleOCRFacade）
"""

import os
import tempfile
from pathlib import Path

import pytest

try:
    import fitz

    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

from paddle_ocr_facade import PaddleOCRFacade


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

            # 2. 初始化OCR Facade
            ocr_tool = PaddleOCRFacade(mode="basic")

            # 3. 处理PDF (使用 Facade 的 process_basic 方法)
            result = ocr_tool.process_basic(temp_pdf)

            # 4. 验证结果
            assert result is not None
            # Facade 返回 dict 结构
            assert isinstance(result, dict)

        finally:
            if os.path.exists(temp_pdf):
                os.remove(temp_pdf)

    def test_searchable_pdf_generation(self):
        """测试PDF处理（简化版本）"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            input_pdf = f.name

        try:
            # 创建输入PDF
            doc = fitz.open()
            page = doc.new_page(width=595, height=842)
            page.insert_text((50, 50), "Searchable Text")
            doc.save(input_pdf)
            doc.close()

            # 处理PDF
            ocr_tool = PaddleOCRFacade(mode="basic")
            result = ocr_tool.process_basic(input_pdf)

            # 验证处理完成
            assert result is not None

        finally:
            if os.path.exists(input_pdf):
                os.remove(input_pdf)

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
            ocr_tool = PaddleOCRFacade(mode="basic")

            all_results = []
            for pdf_file in temp_files:
                result = ocr_tool.process_basic(pdf_file)
                all_results.append(result)

            # 验证结果
            assert len(all_results) == 3
            assert all(r is not None for r in all_results)

        finally:
            for path in temp_files:
                if os.path.exists(path):
                    os.remove(path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
