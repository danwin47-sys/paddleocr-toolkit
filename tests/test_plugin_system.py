# -*- coding: utf-8 -*-
"""
外掛系統測試
"""

import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# 確保可以匯入模組
sys.path.append(".")

from paddleocr_toolkit.api.main import app, plugin_loader
from paddleocr_toolkit.core.ocr_engine import OCREngineManager
from paddleocr_toolkit.plugins.base import OCRPlugin
from paddleocr_toolkit.plugins.loader import PluginLoader


class MockPlugin(OCRPlugin):
    name = "MockPlugin"
    version = "0.0.1"

    def on_init(self):
        return True

    def on_before_ocr(self, image):
        return "processed_image"

    def on_after_ocr(self, results):
        return "processed_results"


@pytest.fixture
def client():
    return TestClient(app)


def test_plugin_loader():
    """測試外掛載入器"""
    loader = PluginLoader("paddleocr_toolkit/plugins")
    plugins = loader.discover_plugins()
    assert len(plugins) > 0  # 應該至少有 example_plugin.py

    # 測試載入
    count = loader.load_all_plugins()
    assert count > 0

    # 驗證 ResultStats 外掛是否存在
    plugin = loader.get_plugin("ResultStats")
    assert plugin is not None
    assert plugin.version == "1.0.0"


def test_ocr_engine_with_plugin():
    """測試 OCR 引擎與外掛整合"""
    # 準備 Mock 外掛
    mock_plugin = MockPlugin()
    mock_plugin.initialize()

    loader = MagicMock()
    loader.get_all_plugins.return_value = {"MockPlugin": mock_plugin}

    # 初始化引擎
    with patch("paddleocr_toolkit.core.ocr_engine.PaddleOCR") as MockPaddleOCR:
        engine_instance = MockPaddleOCR.return_value
        engine_instance.ocr.return_value = "raw_results"

        manager = OCREngineManager(mode="basic", plugin_loader=loader)
        manager.init_engine()

        # 執行預測
        result = manager.predict("input_image")

        # 驗證外掛鉤子被呼叫
        # on_before_ocr 應該將 "input_image" 變為 "processed_image"
        engine_instance.ocr.assert_called_with("processed_image")

        # on_after_ocr 應該將 "raw_results" 變為 "processed_results"
        assert result == "processed_results"


def test_api_list_plugins(client):
    """測試 API 列出外掛"""
    response = client.get("/api/plugins")
    assert response.status_code == 200
    plugins = response.json()
    assert isinstance(plugins, list)
    assert len(plugins) > 0

    # 檢查是否包含 ResultStats
    found = False
    for p in plugins:
        if p["name"] == "ResultStats":
            found = True
            break
    assert found
