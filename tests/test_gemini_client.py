# -*- coding: utf-8 -*-
"""
測試 GeminiClient
"""

import sys
from unittest.mock import Mock, patch

import pytest

# 防護：如果環境中沒有 requests，則建立一個 mock 模組以避免 decorator 失敗
try:
    import requests
except ImportError:
    from unittest.mock import MagicMock

    mock_req = MagicMock()
    sys.modules["requests"] = mock_req
    import requests

from paddleocr_toolkit.llm.llm_client import GeminiClient, create_llm_client


class TestGeminiClient:
    """測試 GeminiClient 功能"""

    def test_init(self):
        """測試初始化"""
        client = GeminiClient(api_key="test-key", model="gemini-3-flash")
        assert client.api_key == "test-key"
        assert client.model == "gemini-3-flash"
        assert "key=test-key" in client.api_url
        assert "gemini-3-flash" in client.api_url

    @patch("requests.get")
    def test_is_available_success(self, mock_get):
        """測試可用性檢查成功"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = GeminiClient(api_key="test-key")
        assert client.is_available() is True
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_is_available_failure(self, mock_get):
        """測試可用性檢查失敗"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        client = GeminiClient(api_key="invalid-key")
        assert client.is_available() is False

    @patch("requests.post")
    def test_generate_success(self, mock_post):
        """測試生成文字成功"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Hello form Gemini 3!"}]}}]
        }
        mock_post.return_value = mock_response

        client = GeminiClient(api_key="test-key")
        result = client.generate("Say hello")

        assert result == "Hello form Gemini 3!"
        # 驗證 payload
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["contents"][0]["parts"][0]["text"] == "Say hello"

    @patch("requests.post")
    def test_generate_error_format(self, mock_post):
        """測試錯誤回應格式處理"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "unexpected format"}
        mock_post.return_value = mock_response

        client = GeminiClient(api_key="test-key")
        result = client.generate("Say hello")

        assert result == ""

    @patch("requests.post")
    def test_generate_http_error(self, mock_post):
        """測試 HTTP 錯誤處理"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        client = GeminiClient(api_key="test-key")
        result = client.generate("Say hello")

        assert result == ""


class TestGeminiFactory:
    """測試工廠函式整合"""

    def test_create_gemini_client(self):
        """測試透過工廠建立 Gemini 客戶端"""
        client = create_llm_client(
            "gemini", api_key="factory-key", model="gemini-3-flash"
        )
        assert isinstance(client, GeminiClient)
        assert client.api_key == "factory-key"

    def test_create_gemini_without_api_key(self):
        """測試缺少 API Key 時丟擲錯誤"""
        with pytest.raises(ValueError, match="api_key"):
            create_llm_client("gemini", model="gemini-3-flash")
