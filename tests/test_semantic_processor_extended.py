# -*- coding: utf-8 -*-
"""
測試 SemanticProcessor - 額外覆蓋率測試
"""

from unittest.mock import Mock, patch

import pytest

from paddleocr_toolkit.processors.semantic_processor import SemanticProcessor


class TestSemanticProcessorEdgeCases:
    """測試邊界情況"""

    @pytest.fixture
    def processor(self):
        """建立 processor 例項"""
        with patch(
            "paddleocr_toolkit.processors.semantic_processor.create_llm_client"
        ) as mock_create:
            mock_client = Mock()
            mock_client.is_available.return_value = True
            mock_client.model = "test-model"
            mock_client.provider = "ollama"
            mock_create.return_value = mock_client
            proc = SemanticProcessor(llm_provider="ollama")
            proc.llm_client = mock_client
            return proc

    def test_correct_text_with_empty_string(self, processor):
        """測試空字串修正"""
        processor.llm_client.generate = Mock(return_value="")

        result = processor.correct_ocr_errors("")

        assert result == ""

    def test_correct_text_with_very_long_text(self, processor):
        """測試超長文字修正"""
        long_text = "測試" * 1000
        processor.llm_client.generate = Mock(return_value=long_text)

        result = processor.correct_ocr_errors(long_text)

        assert len(result) > 0

    def test_extract_structured_data_with_invalid_schema(self, processor):
        """測試無效 schema"""
        processor.llm_client.generate = Mock(return_value='{"invalid": "json"')

        result = processor.extract_structured_data("測試文字", schema={})

        # 應該返回空字典或處理錯誤
        assert isinstance(result, (dict, str))

    def test_correct_text_with_llm_error(self, processor):
        """測試 LLM 錯誤處理"""
        processor.llm_client.generate = Mock(side_effect=Exception("LLM 錯誤"))

        # 應該優雅地處理錯誤
        result = processor.correct_ocr_errors("測試")
        # 應該返回原文
        assert result == "測試"


class TestSemanticProcessorLanguageSupport:
    """測試多語言支援"""

    @pytest.fixture
    def processor(self):
        """建立 processor 例項"""
        with patch(
            "paddleocr_toolkit.processors.semantic_processor.create_llm_client"
        ) as mock_create:
            mock_client = Mock()
            mock_client.is_available.return_value = True
            mock_client.model = "test-model"
            mock_client.provider = "ollama"
            mock_create.return_value = mock_client
            proc = SemanticProcessor(llm_provider="ollama")
            proc.llm_client = mock_client
            return proc

    def test_correct_english_text(self, processor):
        """測試英文修正"""
        processor.llm_client.generate = Mock(return_value="Corrected English text")

        result = processor.correct_ocr_errors("Englsh text", language="en")

        assert "Corrected" in result or "English" in result

    def test_correct_chinese_text(self, processor):
        """測試中文修正"""
        processor.llm_client.generate = Mock(return_value="修正後的中文")

        result = processor.correct_ocr_errors("錯誤的中文", language="zh")

        assert len(result) > 0


class TestSemanticProcessorPromptBuilding:
    """測試提示詞建構"""

    @pytest.fixture
    def processor(self):
        """建立 processor 例項"""
        with patch(
            "paddleocr_toolkit.processors.semantic_processor.create_llm_client"
        ) as mock_create:
            mock_client = Mock()
            mock_client.is_available.return_value = True
            mock_client.model = "test-model"
            mock_client.provider = "ollama"
            mock_create.return_value = mock_client
            return SemanticProcessor(llm_provider="ollama")

    def test_build_chinese_correction_prompt(self, processor):
        """測試中文修正提示詞"""
        # 這個測試驗證內部方法
        prompt = processor._build_chinese_correction_prompt("測試文字", "")

        assert "繁體中文" in prompt or "Traditional Chinese" in prompt
        assert "測試文字" in prompt

    def test_build_english_correction_prompt(self, processor):
        """測試英文修正提示詞"""
        prompt = processor._build_english_correction_prompt("Test text", "")

        assert "OCR" in prompt or "proofreader" in prompt
        assert "Test text" in prompt
