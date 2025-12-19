# -*- coding: utf-8 -*-
"""
測試 LLMClient - 額外覆蓋率測試
"""

from unittest.mock import Mock, patch

import pytest


class TestOllamaClientExtended:
    """測試 OllamaClient 額外功能"""

    @patch("paddleocr_toolkit.llm.llm_client.HAS_REQUESTS", True)
    @patch("requests.post")
    def test_ollama_client_with_custom_base_url(self, mock_post):
        """測試自訂 base URL"""
        from paddleocr_toolkit.llm import OllamaClient
        
        client = OllamaClient(base_url="http://custom:11434")
        
        assert client.base_url == "http://custom:11434"
        assert client.api_url == "http://custom:11434/api/generate"

    @patch("paddleocr_toolkit.llm.llm_client.HAS_REQUESTS", True)
    @patch("requests.post")
    def test_ollama_client_with_custom_timeout(self, mock_post):
        """測試自訂 timeout"""
        from paddleocr_toolkit.llm import OllamaClient
        
        client = OllamaClient(timeout=120)
        
        assert client.timeout == 120

    @patch("paddleocr_toolkit.llm.llm_client.HAS_REQUESTS", True)
    @patch("requests.post")
    def test_ollama_generate_with_custom_parameters(self, mock_post):
        """測試使用自訂引數生成"""
        from paddleocr_toolkit.llm import OllamaClient
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Generated text"}
        mock_post.return_value = mock_response
        
        client = OllamaClient()
        result = client.generate("Test prompt", temperature=0.7, max_tokens=1000)
        
        assert result == "Generated text"
        # 驗證引數被傳遞
        call_args = mock_post.call_args
        assert call_args[1]["json"]["options"]["temperature"] == 0.7

    @patch("paddleocr_toolkit.llm.llm_client.HAS_REQUESTS", True)
    @patch("requests.post")
    def test_ollama_generate_with_error_response(self, mock_post):
        """測試錯誤回應處理"""
        from paddleocr_toolkit.llm import OllamaClient
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        client = OllamaClient()
        result = client.generate("Test prompt")
        
        assert result == ""


class TestOpenAIClientExtended:
    """測試 OpenAIClient 額外功能"""

    @patch("paddleocr_toolkit.llm.llm_client.HAS_REQUESTS", True)
    @patch("requests.post")
    @patch("requests.get")
    def test_openai_client_with_custom_base_url(self, mock_get, mock_post):
        """測試自訂 base URL"""
        from paddleocr_toolkit.llm import OpenAIClient
        
        client = OpenAIClient(api_key="test-key", base_url="https://custom.api.com/v1")
        
        assert client.base_url == "https://custom.api.com/v1"

    @patch("paddleocr_toolkit.llm.llm_client.HAS_REQUESTS", True)
    @patch("requests.get")
    def test_openai_is_available_with_valid_key(self, mock_get):
        """測試有效 API Key 的可用性檢查"""
        from paddleocr_toolkit.llm import OpenAIClient
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        client = OpenAIClient(api_key="valid-key")
        result = client.is_available()
        
        assert result is True

    @patch("paddleocr_toolkit.llm.llm_client.HAS_REQUESTS", True)
    @patch("requests.post")
    def test_openai_generate_with_error(self, mock_post):
        """測試生成時的錯誤處理"""
        from paddleocr_toolkit.llm import OpenAIClient
        
        mock_post.side_effect = Exception("Network error")
        
        client = OpenAIClient(api_key="test-key")
        result = client.generate("Test prompt")
        
        assert result == ""


class TestLLMClientFactory:
    """測試 LLM 客戶端工廠函式"""

    @patch("paddleocr_toolkit.llm.llm_client.HAS_REQUESTS", True)
    def test_create_ollama_client(self):
        """測試建立 Ollama 客戶端"""
        from paddleocr_toolkit.llm import create_llm_client
        
        client = create_llm_client("ollama", model="custom-model")
        
        assert client.model == "custom-model"

    @patch("paddleocr_toolkit.llm.llm_client.HAS_REQUESTS", True)
    def test_create_openai_client(self):
        """測試建立 OpenAI 客戶端"""
        from paddleocr_toolkit.llm import create_llm_client
        
        client = create_llm_client("openai", api_key="test-key", model="gpt-4")
        
        assert client.model == "gpt-4"
        assert client.api_key == "test-key"

    @patch("paddleocr_toolkit.llm.llm_client.HAS_REQUESTS", True)
    def test_create_client_with_invalid_provider(self):
        """測試使用無效提供商"""
        from paddleocr_toolkit.llm import create_llm_client
        
        with pytest.raises(ValueError, match="不支援的 LLM 提供商"):
            create_llm_client("invalid-provider")

    @patch("paddleocr_toolkit.llm.llm_client.HAS_REQUESTS", True)
    def test_create_openai_without_api_key(self):
        """測試建立 OpenAI 客戶端時缺少 API Key"""
        from paddleocr_toolkit.llm import create_llm_client
        
        with pytest.raises(ValueError, match="api_key"):
            create_llm_client("openai")
