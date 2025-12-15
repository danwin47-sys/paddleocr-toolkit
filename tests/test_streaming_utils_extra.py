# -*- coding: utf-8 -*-
"""
串流處理工具測試
測試 paddleocr_toolkit/core/streaming_utils.py
"""

from unittest.mock import MagicMock, patch

import pytest


class TestStreamingUtils:
    """測試串流處理工具"""

    def test_import_streaming_utils(self):
        """測試匯入串流處理工具"""
        from paddleocr_toolkit.core import streaming_utils

        assert streaming_utils is not None

    def test_import_streaming_pdf_processor(self):
        """測試匯入串流 PDF 處理器"""
        try:
            from paddleocr_toolkit.core.streaming_utils import StreamingPDFProcessor

            assert StreamingPDFProcessor is not None
        except ImportError:
            pytest.skip("StreamingPDFProcessor not available")

    def test_import_pdf_pages_generator(self):
        """測試匯入 PDF 頁面生成器"""
        try:
            from paddleocr_toolkit.core.streaming_utils import pdf_pages_generator

            assert callable(pdf_pages_generator)
        except ImportError:
            pytest.skip("pdf_pages_generator not available")

    def test_import_batch_pages_generator(self):
        """測試匯入批次頁面生成器"""
        try:
            from paddleocr_toolkit.core.streaming_utils import batch_pages_generator

            assert callable(batch_pages_generator)
        except ImportError:
            pytest.skip("batch_pages_generator not available")


class TestOpenPDFContext:
    """測試 PDF 上下文管理器"""

    def test_import_open_pdf_context(self):
        """測試匯入 open_pdf_context"""
        try:
            from paddleocr_toolkit.core.streaming_utils import open_pdf_context

            assert open_pdf_context is not None
        except ImportError:
            pytest.skip("open_pdf_context not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
