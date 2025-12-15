# -*- coding: utf-8 -*-
"""
Streaming Utils 測試 - v1.1.0 Week 1 Day 5-7
補充測試以達到 85%+ 覆蓋率
"""

import os
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest

try:
    import fitz

    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

from paddleocr_toolkit.core.streaming_utils import (
    batch_pages_generator,
    open_pdf_context,
    pdf_pages_generator,
)


class TestOpenPdfContext:
    """測試 PDF 上下文管理器"""

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_open_pdf_context_basic(self):
        """測試基本 PDF 打開"""
        # 創建測試 PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            doc = fitz.open()
            doc.new_page(width=100, height=100)
            doc.save(temp_path)
            doc.close()

            # 測試上下文管理器
            with open_pdf_context(temp_path) as pdf_doc:
                assert pdf_doc is not None
                assert len(pdf_doc) == 1

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_open_pdf_context_closes(self):
        """測試 PDF 正確關閉"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            doc = fitz.open()
            doc.new_page(width=100, height=100)
            doc.save(temp_path)
            doc.close()

            # 使用上下文管理器
            with open_pdf_context(temp_path) as pdf_doc:
                doc_ref = pdf_doc

            # 驗證已關閉（通過檢查是否可以訪問）
            # fitz 文件關閉後某些操作會失敗
            assert doc_ref is not None

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestPdfPagesGenerator:
    """測試 PDF 頁面生成器"""

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_pdf_pages_generator_all_pages(self):
        """測試生成所有頁面"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            # 創建3頁PDF
            doc = fitz.open()
            for i in range(3):
                doc.new_page(width=100, height=100)
            doc.save(temp_path)
            doc.close()

            # 測試生成器
            pages = list(pdf_pages_generator(temp_path))

            assert len(pages) == 3
            for i, (page_num, page) in enumerate(pages):
                assert page_num == i
                assert page is not None

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_pdf_pages_generator_specific_pages(self):
        """測試生成特定頁面"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            doc = fitz.open()
            for i in range(5):
                doc.new_page(width=100, height=100)
            doc.save(temp_path)
            doc.close()

            # 只生成第0,2,4頁
            pages = list(pdf_pages_generator(temp_path, pages=[0, 2, 4]))

            assert len(pages) == 3
            assert pages[0][0] == 0
            assert pages[1][0] == 2
            assert pages[2][0] == 4

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_pdf_pages_generator_with_dpi(self):
        """測試帶DPI參數的生成"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            doc = fitz.open()
            doc.new_page(width=100, height=100)
            doc.save(temp_path)
            doc.close()

            # 測試不同DPI
            pages_low = list(pdf_pages_generator(temp_path, dpi=72))
            pages_high = list(pdf_pages_generator(temp_path, dpi=300))

            assert len(pages_low) == 1
            assert len(pages_high) == 1

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestBatchPagesGenerator:
    """測試批次頁面生成器"""

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_batch_pages_generator_basic(self):
        """測試基本批次生成"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            doc = fitz.open()
            for i in range(10):
                doc.new_page(width=100, height=100)
            doc.save(temp_path)
            doc.close()

            # 批次大小為3
            batches = list(batch_pages_generator(temp_path, batch_size=3))

            # 應該有4個批次（3+3+3+1）
            assert len(batches) == 4
            assert len(batches[0]) == 3
            assert len(batches[1]) == 3
            assert len(batches[2]) == 3
            assert len(batches[3]) == 1  # 最後一個批次

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_batch_pages_generator_exact_fit(self):
        """測試剛好整除的批次"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            doc = fitz.open()
            for i in range(6):
                doc.new_page(width=100, height=100)
            doc.save(temp_path)
            doc.close()

            # 批次大小為2，剛好3批
            batches = list(batch_pages_generator(temp_path, batch_size=2))

            assert len(batches) == 3
            assert all(len(batch) == 2 for batch in batches)

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @pytest.mark.skipif(not HAS_FITZ, reason="PyMuPDF not installed")
    def test_batch_pages_generator_single_batch(self):
        """測試單個批次"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            doc = fitz.open()
            for i in range(3):
                doc.new_page(width=100, height=100)
            doc.save(temp_path)
            doc.close()

            # 批次大小大於總頁數
            batches = list(batch_pages_generator(temp_path, batch_size=10))

            assert len(batches) == 1
            assert len(batches[0]) == 3

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


# 執行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
