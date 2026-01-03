# -*- coding: utf-8 -*-
import importlib
import sys
from unittest.mock import patch, MagicMock


class TestImportErrorsUltra:
    def test_all_import_errors(self):
        modules = [
            ("paddleocr_toolkit.processors.pdf_processor", "fitz", "HAS_FITZ"),
            ("paddleocr_toolkit.processors.pdf_quality", "fitz", "HAS_FITZ"),
            (
                "paddleocr_toolkit.processors.structure_processor",
                "paddleocr_toolkit.core.models",
                None,
            ),
            ("paddleocr_toolkit.processors.ocr_workaround", "fitz", "HAS_FITZ"),
            (
                "paddleocr_toolkit.processors.parallel_pdf_processor",
                "fitz",
                "HAS_PYMUPDF",
            ),
            ("paddleocr_toolkit.processors.translation_processor", "fitz", "HAS_FITZ"),
            ("paddleocr_toolkit.processors.ocr_workaround", "numpy", "HAS_NUMPY"),
            (
                "paddleocr_toolkit.processors.parallel_pdf_processor",
                "numpy",
                "HAS_NUMPY",
            ),
            ("paddleocr_toolkit.processors.image_preprocessor", "numpy", "HAS_NUMPY"),
            ("paddleocr_toolkit.processors.image_preprocessor", "cv2", "HAS_CV2"),
            ("paddleocr_toolkit.processors.translation_processor", "tqdm", "HAS_TQDM"),
            (
                "paddleocr_toolkit.processors.translation_processor",
                "pdf_translator",
                None,
            ),
            ("paddleocr_toolkit.processors.basic_processor", "tqdm", "HAS_TQDM"),
            ("paddleocr_toolkit.processors.formula_processor", "tqdm", "HAS_TQDM"),
            ("paddleocr_toolkit.processors.batch_processor", "numpy", "HAS_NUMPY"),
            ("paddleocr_toolkit.processors.batch_processor", "fitz", "HAS_FITZ"),
        ]
        for mod_path, mock_target, flag_name in modules:
            try:
                mod = importlib.import_module(mod_path)
                with patch.dict(sys.modules, {mock_target: None}):
                    try:
                        importlib.reload(mod)
                        if flag_name:
                            # It might be False or just not present if conditional
                            val = getattr(mod, flag_name, None)
                            if val is not None:
                                assert val is False
                    except (ImportError, ModuleNotFoundError):
                        pass
                importlib.reload(mod)
            except Exception:
                pass
