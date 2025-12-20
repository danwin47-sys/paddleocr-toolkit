# -*- coding: utf-8 -*-
"""
PaddleOCR Toolkit - LLM 客戶端抽象層

支援多種 LLM 提供商：
- Ollama (本地部署)
- OpenAI API (雲端服務)
- Claude API (雲端服務)
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class LLMClient(ABC):
    """LLM 客戶端抽象基類"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """生成文字回應"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """檢查服務是否可用"""
        pass


class OllamaClient(LLMClient):
    """Ollama 本地 LLM 客戶端"""
    
    def __init__(
        self,
        model: str = "qwen2.5:7b",
        base_url: str = "http://localhost:11434",
        timeout: int = 60
    ):
        """
        初始化 Ollama 客戶端
        
        Args:
            model: 模型名稱
            base_url: Ollama 服務地址
            timeout: 請求超時時間（秒）
        """
        if not HAS_REQUESTS:
            raise ImportError("需要安裝 requests: pip install requests")
        
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.api_url = f"{self.base_url}/api/generate"
    
    def is_available(self) -> bool:
        """檢查 Ollama 服務是否可用"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logging.warning(f"Ollama 服務不可用: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        使用 Ollama 生成文字
        
        Args:
            prompt: 提示詞
            **kwargs: 額外引數（temperature, max_tokens 等）
        
        Returns:
            str: 生成的文字
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.3),
                    "num_predict": kwargs.get("max_tokens", 2048),
                }
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logging.error(f"Ollama 請求失敗: {response.status_code}")
                return ""
        
        except Exception as e:
            logging.error(f"Ollama 生成失敗: {e}")
            return ""


class OpenAIClient(LLMClient):
    """OpenAI API 客戶端"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        base_url: Optional[str] = None
    ):
        """
        初始化 OpenAI 客戶端
        
        Args:
            api_key: OpenAI API 金鑰
            model: 模型名稱
            base_url: 可選的基礎 URL（用於代理或自定義端點）
        """
        if not HAS_REQUESTS:
            raise ImportError("需要安裝 requests: pip install requests")
        
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"
        self.api_url = f"{self.base_url}/chat/completions"
    
    def is_available(self) -> bool:
        """檢查 OpenAI API 是否可用"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logging.warning(f"OpenAI API 不可用: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> str:
        """使用 OpenAI API 生成文字"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", 0.3),
                "max_tokens": kwargs.get("max_tokens", 2048),
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                logging.error(f"OpenAI 請求失敗: {response.status_code}")
                return ""
        
        except Exception as e:
            logging.error(f"OpenAI 生成失敗: {e}")
            return ""


class GeminiClient(LLMClient):
    """Google Gemini API 客戶端 (支援 Gemini 3 Flash)"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3-flash",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    ):
        """
        初始化 Gemini 客戶端
        
        Args:
            api_key: Google AI API 金鑰
            model: 模型名稱 (預設 gemini-3-flash)
            base_url: Google AI API 基礎 URL
        """
        if not HAS_REQUESTS:
            raise ImportError("需要安裝 requests: pip install requests")
        
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip('/')
        # v1beta 版本的 generateContent 端點
        self.api_url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
    
    def is_available(self) -> bool:
        """檢查 Gemini API 是否可用"""
        try:
            # 嘗試列出模型來檢查金鑰
            check_url = f"{self.base_url}/models?key={self.api_key}"
            response = requests.get(check_url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logging.warning(f"Gemini API 不可用: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> str:
        """使用 Gemini API 生成文字"""
        try:
            payload = {
                "contents": [
                    {
                        "parts": [{"text": prompt}]
                    }
                ],
                "generationConfig": {
                    "temperature": kwargs.get("temperature", 0.3),
                    "maxOutputTokens": kwargs.get("max_tokens", 2048),
                }
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                # 解析 Gemini 的多層回應結構
                try:
                    return result["candidates"][0]["content"]["parts"][0]["text"].strip()
                except (KeyError, IndexError):
                    logging.error(f"Gemini 回應格式解析失敗: {result}")
                    return ""
            else:
                logging.error(f"Gemini 請求失敗: {response.status_code} - {response.text}")
                return ""
        
        except Exception as e:
            logging.error(f"Gemini 生成失敗: {e}")
            return ""


class ClaudeClient(LLMClient):
    """Anthropic Claude API 客戶端"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20240620",
        base_url: str = "https://api.anthropic.com/v1"
    ):
        """
        初始化 Claude 客戶端
        
        Args:
            api_key: Anthropic API 金鑰
            model: 模型名稱
            base_url: Claude API 基礎 URL
        """
        if not HAS_REQUESTS:
            raise ImportError("需要安裝 requests: pip install requests")
        
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/messages"
    
    def is_available(self) -> bool:
        """檢查 Claude API 是否可用"""
        # 簡單驗證 API Key 的端點不穩定，這裡使用一個簡單的預檢請求
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        try:
            # 只請求 1 個 token 來驗證
            payload = {
                "model": self.model,
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "Hi"}]
            }
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logging.warning(f"Claude API 不可用: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> str:
        """使用 Claude API 生成文字"""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", 2048),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.3),
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["content"][0]["text"].strip()
            else:
                logging.error(f"Claude 請求失敗: {response.status_code} - {response.text}")
                return ""
        except Exception as e:
            logging.error(f"Claude 生成失敗: {e}")
            return ""


def create_llm_client(
    provider: str = "ollama",
    **kwargs
) -> LLMClient:
    """
    工廠函式：建立 LLM 客戶端
    
    Args:
        provider: 提供商 ("ollama", "openai", "gemini", "claude")
        **kwargs: 提供商特定引數
    
    Returns:
        LLMClient: LLM 客戶端例項
    """
    if provider == "ollama":
        return OllamaClient(**kwargs)
    elif provider == "openai":
        if "api_key" not in kwargs:
            raise ValueError("OpenAI 需要提供 api_key")
        return OpenAIClient(**kwargs)
    elif provider == "gemini":
        if "api_key" not in kwargs:
            raise ValueError("Gemini 需要提供 api_key")
        return GeminiClient(**kwargs)
    elif provider == "claude":
        if "api_key" not in kwargs:
            raise ValueError("Claude 需要提供 api_key")
        return ClaudeClient(**kwargs)
    else:
        raise ValueError(f"不支援的 LLM 提供商: {provider}")
