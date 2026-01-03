# -*- coding: utf-8 -*-
"""
語義處理器測試
"""

from unittest.mock import Mock, patch

import pytest

from paddleocr_toolkit.processors.semantic_processor import SemanticProcessor


class TestSemanticProcessor:
    """語義處理器測試套件"""

    def test_init_with_ollama(self):
        """測試使用 Ollama 初始化"""
        with patch("paddleocr_toolkit.llm.llm_client.HAS_REQUESTS", True), patch(
            "paddleocr_toolkit.llm.llm_client.requests", create=True
        ) as mock_requests:
            # Mock Ollama 服務可用
            mock_requests.get.return_value.status_code = 200

            processor = SemanticProcessor(llm_provider="ollama")
            assert processor.is_enabled()

    def test_init_without_service(self):
        """測試服務不可用時的初始化"""
        with patch("paddleocr_toolkit.llm.llm_client.HAS_REQUESTS", True), patch(
            "paddleocr_toolkit.llm.llm_client.requests", create=True
        ) as mock_requests:
            # Mock 服務不可用
            mock_requests.get.side_effect = Exception("Connection refused")

            processor = SemanticProcessor(llm_provider="ollama")
            assert not processor.is_enabled()

    def test_correct_ocr_errors_disabled(self):
        """測試未啟用時返回原始文字"""
        with patch("paddleocr_toolkit.llm.llm_client.HAS_REQUESTS", True), patch(
            "paddleocr_toolkit.llm.llm_client.requests", create=True
        ) as mock_requests:
            mock_requests.get.side_effect = Exception("Connection refused")

            processor = SemanticProcessor(llm_provider="ollama")

            original_text = "這個文建可能有銷別字"
            result = processor.correct_ocr_errors(original_text)

            assert result == original_text

    def test_correct_ocr_errors_success(self):
        """測試成功修正 OCR 錯誤"""
        with patch("paddleocr_toolkit.llm.llm_client.HAS_REQUESTS", True), patch(
            "paddleocr_toolkit.llm.llm_client.requests", create=True
        ) as mock_requests:
            # Mock 服務可用
            mock_get = Mock()
            mock_get.status_code = 200
            mock_requests.get.return_value = mock_get

            # Mock 修正結果
            mock_post = Mock()
            mock_post.status_code = 200
            mock_post.json.return_value = {"response": "這個檔案可能有錯別字"}
            mock_requests.post.return_value = mock_post

            processor = SemanticProcessor(llm_provider="ollama")

            original_text = "這個文建可能有銷別字"
            corrected = processor.correct_ocr_errors(original_text)

            assert corrected == "這個檔案可能有錯別字"
            assert "文建" not in corrected
            assert "銷別字" not in corrected

    def test_extract_structured_data(self):
        """測試結構化資料提取"""
        with patch("paddleocr_toolkit.llm.llm_client.HAS_REQUESTS", True), patch(
            "paddleocr_toolkit.llm.llm_client.requests", create=True
        ) as mock_requests:
            # Mock 服務可用
            mock_get = Mock()
            mock_get.status_code = 200
            mock_requests.get.return_value = mock_get

            # Mock JSON 返回
            mock_post = Mock()
            mock_post.status_code = 200
            mock_post.json.return_value = {
                "response": '{"name": "張三", "age": 30, "email": "zhang@example.com"}'
            }
            mock_requests.post.return_value = mock_post

            processor = SemanticProcessor(llm_provider="ollama")

            text = "姓名：張三\n年齡：30\n電子郵件：zhang@example.com"
            schema = {"name": "string", "age": "number", "email": "string"}

            result = processor.extract_structured_data(text, schema)

            assert result["name"] == "張三"
            assert result["age"] == 30
            assert result["email"] == "zhang@example.com"

    def test_summarize_document(self):
        """測試檔案摘要"""
        with patch("paddleocr_toolkit.llm.llm_client.HAS_REQUESTS", True), patch(
            "paddleocr_toolkit.llm.llm_client.requests", create=True
        ) as mock_requests:
            # Mock 服務可用
            mock_get = Mock()
            mock_get.status_code = 200
            mock_requests.get.return_value = mock_get

            # Mock 摘要結果
            mock_post = Mock()
            mock_post.status_code = 200
            mock_post.json.return_value = {"response": "這是關於 PaddleOCR 工具包的技術檔案"}
            mock_requests.post.return_value = mock_post

            processor = SemanticProcessor(llm_provider="ollama")

            long_text = (
                """
            PaddleOCR Toolkit 是一個強大的光學字元識別工具包，
            支援多種語言和格式。本檔案介紹瞭如何使用該工具包
            進行文字識別、翻譯和檔案處理。
            """
                * 10
            )

            summary = processor.summarize_document(long_text, max_length=50)

            assert len(summary) <= 50
            assert "PaddleOCR" in summary or "OCR" in summary.lower()


class TestLLMClient:
    """LLM 客戶端測試"""

    def test_ollama_client_creation(self):
        """測試 Ollama 客戶端建立處理"""
        from paddleocr_toolkit.llm import OllamaClient, create_llm_client

        with patch("paddleocr_toolkit.llm.llm_client.HAS_REQUESTS", True):
            client = create_llm_client("ollama", model="qwen2.5:7b")
            assert isinstance(client, OllamaClient)
            assert client.model == "qwen2.5:7b"

    def test_unsupported_provider(self):
        """測試不支援的提供商"""
        from paddleocr_toolkit.llm import create_llm_client

        with pytest.raises(ValueError, match="不支援的 LLM 提供商"):
            create_llm_client("unsupported_provider")


# Added from Ultra Coverage
from paddleocr_toolkit.processors.semantic_processor import SemanticProcessor
from unittest.mock import MagicMock, patch


class TestSemanticExceptions:
    def test_summarize_exception(self):
        proc = SemanticProcessor()
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = Exception("Summarization error")
        proc.llm_client = mock_llm
        res = proc.summarize_document("Long text", max_length=5)
        assert res == "Long ..."


class TestSemanticUltra:
    def test_semantic_fallbacks_and_markdown(self):
        with patch(
            "paddleocr_toolkit.processors.semantic_processor.create_llm_client"
        ) as mock_create:
            mock_llm = MagicMock()
            mock_llm.is_available.return_value = False
            mock_create.return_value = mock_llm
            proc = SemanticProcessor(llm_provider="ollama")
            proc.llm_client = None
            assert proc.extract_structured_data("text", {}) == {}
            assert proc.summarize_document("Long text") == "Long text..."
        proc = SemanticProcessor()
        mock_llm = MagicMock()
        proc.llm_client = mock_llm
        mock_llm.generate.return_value = '```json\n{"key": "value"}\n```'
        res = proc.extract_structured_data("text", {})
        assert res == {"key": "value"}

    def test_correction_prompts(self):
        proc = SemanticProcessor()
        p1 = proc._build_chinese_correction_prompt("text", "ctx")
        assert "上下文資訊" in p1
        p2 = proc._build_english_correction_prompt("text", "ctx")
        assert "Context:" in p2
