# -*- coding: utf-8 -*-
"""
TranslationProcessor 测试
"""

from unittest.mock import MagicMock, Mock

import pytest

from paddleocr_toolkit.core.models import OCRResult
from paddleocr_toolkit.processors.translation_processor import TranslationProcessor


class TestTranslationProcessor:
    """测试翻译处理器"""

    def test_init(self):
        """测试初始化"""
        processor = TranslationProcessor()
        assert processor.translator is None
        assert processor.renderer is None

    def test_init_with_components(self):
        """测试带组件的初始化"""
        mock_translator = Mock()
        mock_renderer = Mock()

        processor = TranslationProcessor(
            translator=mock_translator, renderer=mock_renderer
        )

        assert processor.translator == mock_translator
        assert processor.renderer == mock_renderer

    def test_process_translation_no_translator(self):
        """测试无翻译器时的错误"""
        processor = TranslationProcessor()

        results = [OCRResult("Test", 0.95, [[0, 0], [100, 0], [100, 50], [0, 50]])]

        with pytest.raises(ValueError):
            processor.process_translation(results)

    def test_process_translation_success(self):
        """测试成功翻译"""
        mock_translator = Mock()
        mock_translator.translate_batch.return_value = ["Translated"]

        processor = TranslationProcessor(translator=mock_translator)

        results = [OCRResult("原文", 0.95, [[0, 0], [100, 0], [100, 50], [0, 50]])]

        translated = processor.process_translation(
            results, source_lang="zh", target_lang="en"
        )

        assert len(translated) == 1
        assert translated[0]["original"] == "原文"
        assert translated[0]["translated"] == "Translated"
        assert translated[0]["confidence"] == 0.95

    def test_process_translation_multiple(self):
        """测试多文本翻译"""
        mock_translator = Mock()
        mock_translator.translate_batch.return_value = ["Trans1", "Trans2"]

        processor = TranslationProcessor(translator=mock_translator)

        results = [
            OCRResult("Text1", 0.95, [[0, 0], [100, 0], [100, 50], [0, 50]]),
            OCRResult("Text2", 0.92, [[0, 60], [100, 60], [100, 110], [0, 110]]),
        ]

        translated = processor.process_translation(results)

        assert len(translated) == 2
        assert translated[0]["translated"] == "Trans1"
        assert translated[1]["translated"] == "Trans2"

    def test_generate_bilingual_pdf(self):
        """测试双语PDF生成"""
        processor = TranslationProcessor()

        blocks = [
            {
                "original": "Text",
                "translated": "Transl",
                "bbox": [[0, 0]],
                "confidence": 0.9,
            }
        ]

        # 这里只测试方法存在和返回值
        result = processor.generate_bilingual_pdf(
            "input.pdf", blocks, "output.pdf", mode="alternating"
        )

        assert isinstance(result, bool)

    def test_extract_translation_text_simple(self):
        """测试提取翻译文字（仅译文）"""
        processor = TranslationProcessor()

        blocks = [
            {
                "original": "Hello",
                "translated": "你好",
                "bbox": [[0, 0]],
                "confidence": 0.9,
            },
            {
                "original": "World",
                "translated": "世界",
                "bbox": [[0, 50]],
                "confidence": 0.85,
            },
        ]

        text = processor.extract_translation_text(blocks, include_original=False)

        assert text == "你好\n世界"

    def test_extract_translation_text_with_original(self):
        """测试提取翻译文字（含原文）"""
        processor = TranslationProcessor()

        blocks = [
            {
                "original": "Hello",
                "translated": "你好",
                "bbox": [[0, 0]],
                "confidence": 0.9,
            }
        ]

        text = processor.extract_translation_text(blocks, include_original=True)

        assert "Hello" in text
        assert "你好" in text

    def test_process_translation_error(self):
        """测试翻译错误处理"""
        mock_translator = Mock()
        mock_translator.translate_batch.side_effect = Exception("Translation error")

        processor = TranslationProcessor(translator=mock_translator)

        results = [OCRResult("Test", 0.95, [[0, 0], [100, 0], [100, 50], [0, 50]])]

        translated = processor.process_translation(results)

        assert len(translated) == 0

    def test_extract_empty_blocks(self):
        """测试空块列表"""
        processor = TranslationProcessor()

        text = processor.extract_translation_text([], include_original=False)
        assert text == ""
