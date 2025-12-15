# -*- coding: utf-8 -*-
"""
pytest configuration and fixtures
"""

import sys
from unittest.mock import MagicMock

import pytest


# Mock paddleocr if not available (for CI environments)
try:
    import paddleocr
except ImportError:
    # Create mock paddleocr module
    mock_paddle = MagicMock()
    mock_paddle.PaddleOCR = MagicMock
    mock_paddle.PPStructureV3 = MagicMock
    mock_paddle.PaddleOCRVL = MagicMock
    mock_paddle.FormulaRecPipeline = MagicMock
    sys.modules['paddleocr'] = mock_paddle


@pytest.fixture
def mock_ocr_engine():
    """Mock OCR engine for testing"""
    engine = MagicMock()
    engine.predict.return_value = [
        [
            [[0, 0], [100, 0], [100, 30], [0, 30]],
            ("Sample text", 0.95)
        ]
    ]
    return engine


@pytest.fixture
def sample_pdf_path(tmp_path):
    """Create a sample PDF for testing"""
    pdf_path = tmp_path / "test.pdf"
    # Create a simple PDF using PyMuPDF
    try:
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Test content")
        doc.save(pdf_path)
        doc.close()
    except ImportError:
        # If PyMuPDF not available, create empty file
        pdf_path.write_bytes(b'')
    return str(pdf_path)


@pytest.fixture
def sample_image_path(tmp_path):
    """Create a sample image for testing"""
    img_path = tmp_path / "test.png"
    try:
        from PIL import Image
        import numpy as np
        # Create a simple test image
        img = Image.fromarray(np.ones((100, 100, 3), dtype=np.uint8) * 255)
        img.save(img_path)
    except ImportError:
        # Create empty file
        img_path.write_bytes(b'')
    return str(img_path)
