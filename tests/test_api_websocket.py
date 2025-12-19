# -*- coding: utf-8 -*-
"""
API WebSocket 整合測試
"""

import asyncio
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# 確保可以匯入模組
sys.path.append(".")

from paddleocr_toolkit.api.main import app, results, tasks
from paddleocr_toolkit.api.websocket_manager import manager


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def api_headers():
    """提供 API 認證 headers"""
    from paddleocr_toolkit.api.main import API_KEY
    return {"X-API-Key": API_KEY}


@pytest.fixture
def mock_ocr_engine_manager():
    with patch("paddleocr_toolkit.api.main.OCREngineManager") as mock:
        instance = mock.return_value
        instance.predict.return_value = [
            [[[0, 0], [100, 0], [100, 30], [0, 30]], ("Test OCR Result", 0.99)]
        ]
        yield mock


def test_websocket_connection(client):
    """測試 WebSocket 連線"""
    task_id = "test_task_id"

    with client.websocket_connect(f"/ws/{task_id}") as websocket:
        # 驗證連線成功
        assert manager.get_connection_count(task_id) == 1

        # 測試傳送訊息
        websocket.send_text("ping")
        data = websocket.receive_json()
        assert data == {"type": "pong"}

    # 驗證斷開連線
    assert manager.get_connection_count(task_id) == 0


def test_create_task_and_status(client, api_headers, mock_ocr_engine_manager):
    """測試建立任務和狀態查詢"""
    # 建立虛擬檔案
    files = {"file": ("test.pdf", b"dummy content", "application/pdf")}

    # 傳送請求
    response = client.post("/api/ocr", files=files, headers=api_headers)
    assert response.status_code == 200
    data = response.json()

    task_id = data["task_id"]
    assert task_id is not None
    assert data["status"] == "queued"

    # 檢查任務是否在佇列中
    assert task_id in tasks

    # 獲取狀態
    response = client.get(f"/api/tasks/{task_id}", headers=api_headers)
    assert response.status_code == 200
    status_data = response.json()
    assert status_data["task_id"] == task_id
    # 注意：由於 TestClient 是同步的，後臺任務可能在請求返回後立即執行
    # 所以狀態可能是 queued, processing 或 completed


@pytest.mark.asyncio
async def test_websocket_progress_update():
    """測試 WebSocket 進度更新 (單元測試 manager)"""
    # 模擬 WebSocket
    mock_ws = MagicMock()
    mock_ws.accept = MagicMock(side_effect=lambda: asyncio.sleep(0))
    mock_ws.send_json = MagicMock(side_effect=lambda x: asyncio.sleep(0))

    task_id = "test_progress_task"

    # 連線
    await manager.connect(mock_ws, task_id)
    assert manager.get_connection_count(task_id) == 1

    # 傳送進度
    await manager.send_progress_update(task_id, 50, "processing", "Halfway there")

    # 驗證傳送呼叫
    mock_ws.send_json.assert_called()
    call_args = mock_ws.send_json.call_args[0][0]
    assert call_args["type"] == "progress"
    assert call_args["progress"] == 50
    assert call_args["message"] == "Halfway there"

    # 斷開
    manager.disconnect(mock_ws, task_id)
