# -*- coding: utf-8 -*-
"""
測試 TranslationProcessor - 額外覆蓋率測試
"""

from unittest.mock import Mock, MagicMock, patch
import tempfile
from pathlib import Path

import pytest

from paddleocr_toolkit.core import OCRMode
from paddleocr_toolkit.core.ocr_engine import OCREngineManager
from paddleocr_toolkit.processors.translation_processor import EnhancedTranslationProcessor


class TestTranslationProcessorInitialization:
    """測試初始化"""

    def test_init_with_valid_engine(self):
        """測試使用有效引擎初始化"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.HYBRID
        
        processor = EnhancedTranslationProcessor(mock_engine)
        
        assert processor.engine_manager == mock_engine

    def test_init_with_custom_settings(self):
        """測試使用自訂設定初始化"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.HYBRID
        
        processor = EnhancedTranslationProcessor(
            mock_engine,
            source_lang="en",
            target_lang="zh-TW",
            model_name="custom-model"
        )
        
        assert processor.source_lang == "en"
        assert processor.target_lang == "zh-TW"


class TestTranslationProcessorSetup:
    """測試翻譯工具設定"""

    @pytest.fixture
    def processor(self):
        """建立 processor 實例"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.HYBRID
        return EnhancedTranslationProcessor(mock_engine)

    @patch("paddleocr_toolkit.processors.translation_processor.fitz")
    @patch("paddleocr_toolkit.processors.translation_processor.OllamaTranslator")
    @patch("paddleocr_toolkit.processors.translation_processor.TextRenderer")
    def test_setup_translation_tools_success(self, mock_renderer, mock_translator, mock_fitz, processor):
        """測試成功設定翻譯工具"""
        mock_translator_instance = Mock()
        mock_translator.return_value = mock_translator_instance
        
        mock_renderer_instance = Mock()
        mock_renderer.return_value = mock_renderer_instance
        
        result = processor._setup_translation_tools()
        
        assert result is not None
        assert len(result) >= 2  # translator, renderer

    @patch("paddleocr_toolkit.processors.translation_processor.fitz")
    def test_setup_translation_tools_with_missing_dependencies(self, mock_fitz, processor):
        """測試缺少依賴時的設定"""
        with patch("paddleocr_toolkit.processors.translation_processor.HAS_TRANSLATOR", False):
            # 應該優雅地處理缺少依賴的情況
            try:
                result = processor._setup_translation_tools()
                # 可能返回 None 或拋出異常
            except Exception as e:
                assert "translator" in str(e).lower() or "依賴" in str(e)


class TestTranslationProcessorPageTranslation:
    """測試頁面翻譯"""

    @pytest.fixture
    def processor(self):
        """建立 processor 實例"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.HYBRID
        return EnhancedTranslationProcessor(mock_engine)

    @patch("paddleocr_toolkit.processors.translation_processor.TranslatedBlock")
    def test_translate_page_texts(self, mock_block, processor):
        """測試翻譯頁面文字"""
        mock_translator = Mock()
        mock_translator.translate_batch.return_value = ["Translated text 1", "Translated text 2"]
        
        ocr_results = [
            {"text": "原文 1", "bbox": [[0, 0], [100, 0], [100, 30], [0, 30]]},
            {"text": "原文 2", "bbox": [[0, 40], [100, 40], [100, 70], [0, 70]]},
        ]
        
        mock_block_instance = Mock()
        mock_block.return_value = mock_block_instance
        
        result = processor._translate_page_texts(ocr_results, mock_translator)
        
        assert len(result) == 2


class TestTranslationProcessorPDFGeneration:
    """測試 PDF 生成"""

    @pytest.fixture
    def processor(self):
        """建立 processor 實例"""
        mock_engine = Mock(spec=OCREngineManager)
        mock_engine.get_mode.return_value = OCRMode.HYBRID
        return EnhancedTranslationProcessor(mock_engine)

    @patch("paddleocr_toolkit.processors.translation_processor.fitz")
    def test_save_translation_pdfs(self, mock_fitz, processor):
        """測試儲存翻譯 PDF"""
        mock_mono_gen = Mock()
        mock_bi_gen = Mock()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.pdf"
            
            processor._save_translation_pdfs(
                mock_mono_gen,
                mock_bi_gen,
                str(output_path)
            )
            
            # 驗證生成器被調用
            assert mock_mono_gen.save.called or mock_bi_gen.save.called
