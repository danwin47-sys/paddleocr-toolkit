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
            **kwargs: 額外參數（temperature, max_tokens 等）
        
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


def create_llm_client(
    provider: str = "ollama",
    **kwargs
) -> LLMClient:
    """
    工廠函數：建立 LLM 客戶端
    
    Args:
        provider: 提供商 ("ollama", "openai")
        **kwargs: 提供商特定參數
    
    Returns:
        LLMClient: LLM 客戶端實例
    
    Example:
        >>> client = create_llm_client("ollama", model="qwen2.5:14b")
        >>> response = client.generate("Hello!")
    """
    if provider == "ollama":
        return OllamaClient(**kwargs)
    elif provider == "openai":
        if "api_key" not in kwargs:
            raise ValueError("OpenAI 需要提供 api_key")
        return OpenAIClient(**kwargs)
    else:
        raise ValueError(f"不支援的 LLM 提供商: {provider}")
