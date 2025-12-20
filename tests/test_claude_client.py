# -*- coding: utf-8 -*-
"""
測試 ClaudeClient
"""

from unittest.mock import Mock, patch
import pytest
import sys

# 防護：如果環境中沒有 requests，則建立一個 mock 模組
try:
    import requests
except ImportError:
    from unittest.mock import MagicMock
    mock_req = MagicMock()
    sys.modules["requests"] = mock_req
    import requests

from paddleocr_toolkit.llm.llm_client import ClaudeClient, create_llm_client


class TestClaudeClient:
    """測試 ClaudeClient 類別"""

    @pytest.fixture
    def client(self):
        return ClaudeClient(api_key="test_key", model="claude-test")

    def test_init(self, client):
        """測試初始化"""
        assert client.api_key == "test_key"
        assert client.model == "claude-test"
        assert "anthropic.com" in client.base_url

    @patch("requests.post")
    def test_is_available_success(self, mock_post, client):
        """測試可用性檢查 (成功)"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        assert client.is_available() is True
        mock_post.assert_called_once()
        # 檢查 Header 中是否有正確的 API Key
        args, kwargs = mock_post.call_args
        assert kwargs["headers"]["x-api-key"] == "test_key"

    @patch("requests.post")
    def test_is_available_failure(self, mock_post, client):
        """測試可用性檢查 (失敗 - 401)"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        assert client.is_available() is False

    @patch("requests.post")
    def test_generate_success(self, mock_post, client):
        """測試生成文字 (成功)"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": "Hello User", "type": "text"}]
        }
        mock_post.return_value = mock_response
        
        result = client.generate("Hi")
        assert result == "Hello User"
        
        # 檢查 Payload 結構
        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert payload["messages"][0]["content"] == "Hi"
        assert payload["model"] == "claude-test"

    @patch("requests.post")
    def test_generate_error_format(self, mock_post, client):
        """測試生成文字 (格式錯誤)"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"unexpected": "data"}
        mock_post.return_value = mock_response
        
        result = client.generate("Hi")
        assert result == ""

    @patch("requests.post")
    def test_generate_http_error(self, mock_post, client):
        """測試生成文字 (HTTP 錯誤)"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        result = client.generate("Hi")
        assert result == ""


class TestClaudeFactory:
    """測試工廠函式整合"""

    def test_create_claude_client(self):
        """測試透過工廠建立 Claude 客戶端"""
        client = create_llm_client("claude", api_key="sk-test-123", model="claude-3-opus")
        assert isinstance(client, ClaudeClient)
        assert client.model == "claude-3-opus"

    def test_create_claude_without_key(self):
        """測試建立 Claude 時未提供 API Key"""
        with pytest.raises(ValueError, match="Claude 需要提供 api_key"):
            create_llm_client("claude")
