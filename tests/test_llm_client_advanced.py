# -*- coding: utf-8 -*-
"""
Advanced tests for LLM Client to maximize coverage.
"""
import pytest
from unittest.mock import MagicMock, patch, Mock

# Import conditionally to avoid import errors if requests is missing in env (though we mock it)
from paddleocr_toolkit.llm.llm_client import (
    create_llm_client,
    OllamaClient,
    OpenAIClient,
    GeminiClient,
    ClaudeClient,
)


class TestLLMClientAdvanced:
    @patch("paddleocr_toolkit.llm.llm_client.HAS_REQUESTS", False)
    def test_no_requests_module(self):
        """Test missing requests module raises ImportError"""
        with pytest.raises(ImportError):
            OllamaClient()
        with pytest.raises(ImportError):
            OpenAIClient(api_key="k")
        with pytest.raises(ImportError):
            GeminiClient(api_key="k")
        with pytest.raises(ImportError):
            ClaudeClient(api_key="k")

    # === Ollama Tests ===
    @patch(
        "paddleocr_toolkit.llm.llm_client.requests.get",
        side_effect=Exception("Conn Refused"),
    )
    def test_ollama_is_available_exception(self, mock_get):
        client = OllamaClient()
        assert client.is_available() is False

    @patch("paddleocr_toolkit.llm.llm_client.requests.post")
    def test_ollama_generate_error(self, mock_post):
        client = OllamaClient()
        # 404 Error
        mock_post.return_value.status_code = 404
        assert client.generate("test") == ""

        # Exception
        mock_post.side_effect = Exception("Timeout")
        assert client.generate("test") == ""

    # === OpenAI Tests ===
    @patch(
        "paddleocr_toolkit.llm.llm_client.requests.get",
        side_effect=Exception("Conn Err"),
    )
    def test_openai_is_available_exception(self, mock_get):
        client = OpenAIClient(api_key="k")
        assert client.is_available() is False

    @patch("paddleocr_toolkit.llm.llm_client.requests.post")
    def test_openai_generate_error(self, mock_post):
        client = OpenAIClient(api_key="k")

        # 500 Error
        mock_post.return_value.status_code = 500
        assert client.generate("test") == ""

        # Exception
        mock_post.side_effect = Exception("API Down")
        assert client.generate("test") == ""

    # === Gemini Tests ===
    @patch("paddleocr_toolkit.llm.llm_client.requests.post")
    def test_gemini_generate_error(self, mock_post):
        client = GeminiClient(api_key="k")

        # 500 Error
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = "Internal Server Error"
        assert client.generate("test") == ""

        # Malformed JSON (Parsing Error)
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"candidates": []}  # Missing content
        mock_post.side_effect = None
        assert client.generate("test") == ""

        # Exception
        mock_post.side_effect = Exception("Net Err")
        assert client.generate("test") == ""

    # === Claude Tests ===
    @patch(
        "paddleocr_toolkit.llm.llm_client.requests.post",
        side_effect=Exception("Conn Err"),
    )
    def test_claude_is_available_exception(self, mock_post):
        client = ClaudeClient(api_key="k")
        assert client.is_available() is False

    @patch("paddleocr_toolkit.llm.llm_client.requests.post")
    def test_claude_generate_error(self, mock_post):
        client = ClaudeClient(api_key="k")

        # 401 Error
        mock_post.return_value.status_code = 401
        mock_post.return_value.text = "Unauthorized"
        assert client.generate("test") == ""

        # Exception
        mock_post.side_effect = Exception("Timeout")
        assert client.generate("test") == ""

    def test_create_llm_client_invalid_provider(self):
        with pytest.raises(ValueError):
            create_llm_client("unknown")
