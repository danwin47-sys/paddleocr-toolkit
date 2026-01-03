# -*- coding: utf-8 -*-
"""
測試 LLM Client 核心模組
覆蓋 paddleocr_toolkit/llm/llm_client.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from paddleocr_toolkit.llm.llm_client import (
    create_llm_client,
    OllamaClient,
    OpenAIClient,
    GeminiClient,
    ClaudeClient,
    LLMClient,
)


class TestLLMClientFactory:
    """測試 LLM Client 工廠函數"""

    def test_create_ollama(self):
        client = create_llm_client("ollama")
        assert isinstance(client, OllamaClient)

    def test_create_openai(self):
        client = create_llm_client("openai", api_key="test-key")
        assert isinstance(client, OpenAIClient)
        assert client.api_key == "test-key"

    def test_create_gemini(self):
        client = create_llm_client("gemini", api_key="test-key")
        assert isinstance(client, GeminiClient)

    def test_create_claude(self):
        client = create_llm_client("claude", api_key="test-key")
        assert isinstance(client, ClaudeClient)

    def test_missing_api_key(self):
        with pytest.raises(ValueError, match="需要提供 api_key"):
            create_llm_client("openai")

        with pytest.raises(ValueError, match="需要提供 api_key"):
            create_llm_client("gemini")

        with pytest.raises(ValueError, match="需要提供 api_key"):
            create_llm_client("claude")

    def test_unsupported_provider(self):
        with pytest.raises(ValueError, match="不支援的 LLM 提供商"):
            create_llm_client("unknown")


class TestOllamaClient:
    """測試 Ollama 客戶端"""

    @pytest.fixture
    def client(self):
        return OllamaClient(base_url="http://test:11434")

    @patch("paddleocr_toolkit.llm.llm_client.requests")
    def test_is_available_success(self, mock_requests, client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        assert client.is_available() is True
        mock_requests.get.assert_called_with("http://test:11434/api/tags", timeout=5)

    @patch("paddleocr_toolkit.llm.llm_client.requests")
    def test_is_available_failure(self, mock_requests, client):
        mock_requests.get.side_effect = Exception("Connection refused")
        assert client.is_available() is False

    @patch("paddleocr_toolkit.llm.llm_client.requests")
    def test_generate_success(self, mock_requests, client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Hello World"}
        mock_requests.post.return_value = mock_response

        response = client.generate("Hi")
        assert response == "Hello World"

        # 驗證 payload
        args, kwargs = mock_requests.post.call_args
        assert kwargs["json"]["prompt"] == "Hi"
        assert kwargs["json"]["stream"] is False

    @patch("paddleocr_toolkit.llm.llm_client.requests")
    def test_generate_failure(self, mock_requests, client):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_requests.post.return_value = mock_response

        response = client.generate("Hi")
        assert response == ""  # 失敗返回空字串


class TestOpenAIClient:
    """測試 OpenAI 客戶端"""

    @pytest.fixture
    def client(self):
        return OpenAIClient(api_key="sk-test")

    @patch("paddleocr_toolkit.llm.llm_client.requests")
    def test_generate_success(self, mock_requests, client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "GPT Response"}}]
        }
        mock_requests.post.return_value = mock_response

        response = client.generate("Hi")
        assert response == "GPT Response"

        # 驗證 headers
        args, kwargs = mock_requests.post.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer sk-test"

    @patch("paddleocr_toolkit.llm.llm_client.requests")
    def test_generate_exception(self, mock_requests, client):
        mock_requests.post.side_effect = Exception("API Error")
        response = client.generate("Hi")
        assert response == ""


class TestGeminiClient:
    """測試 Gemini 客戶端"""

    @pytest.fixture
    def client(self):
        return GeminiClient(api_key="gemini-key")

    @patch("paddleocr_toolkit.llm.llm_client.requests")
    def test_is_available(self, mock_requests, client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response
        assert client.is_available() is True

    @patch("paddleocr_toolkit.llm.llm_client.requests")
    def test_generate_success(self, mock_requests, client):
        mock_response = Mock()
        mock_response.status_code = 200
        # 模擬 Gemini 複雜的結構
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Gemini Response"}]}}]
        }
        mock_requests.post.return_value = mock_response

        response = client.generate("Hi")
        assert response == "Gemini Response"

    @patch("paddleocr_toolkit.llm.llm_client.requests")
    def test_generate_malformed_response(self, mock_requests, client):
        mock_response = Mock()
        mock_response.status_code = 200
        # 結構不完整
        mock_response.json.return_value = {"candidates": []}
        mock_requests.post.return_value = mock_response

        response = client.generate("Hi")
        assert response == ""  # 解析失敗應返回空


class TestClaudeClient:
    """測試 Claude 客戶端"""

    @pytest.fixture
    def client(self):
        return ClaudeClient(api_key="claude-key")

    @patch("paddleocr_toolkit.llm.llm_client.requests")
    def test_generate_success(self, mock_requests, client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": [{"text": "Claude Response"}]}
        mock_requests.post.return_value = mock_response

        response = client.generate("Hi")
        assert response == "Claude Response"

        # 驗證 headers
        args, kwargs = mock_requests.post.call_args
        assert kwargs["headers"]["x-api-key"] == "claude-key"
