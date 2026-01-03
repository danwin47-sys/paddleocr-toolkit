# -*- coding: utf-8 -*-
"""
WebSocket Manager Tests (Compatible with Python 3.7)
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch
from paddleocr_toolkit.api.websocket_manager import ConnectionManager


# Helper to create a Hashable Mock
def create_hashable_mock(cls_name="MockWS"):
    mock = MagicMock(name=cls_name)
    # Ensure it's hashable for sets
    mock.__hash__.return_value = id(mock)
    # Mock async methods to return awaitables
    mock.accept = MagicMock(return_value=asyncio.Future())
    mock.accept.return_value.set_result(None)
    mock.send_json = MagicMock(return_value=asyncio.Future())
    mock.send_json.return_value.set_result(None)
    mock.send_text = MagicMock(return_value=asyncio.Future())
    mock.send_text.return_value.set_result(None)
    return mock


class TestConnectionManager:
    @pytest.mark.asyncio
    async def test_connect(self):
        manager = ConnectionManager()
        mock_ws = create_hashable_mock()
        await manager.connect(mock_ws, "task1")
        assert "task1" in manager.active_connections
        assert mock_ws in manager.active_connections["task1"]

    @pytest.mark.asyncio
    async def test_connect_logs(self):
        manager = ConnectionManager()
        mock_ws = create_hashable_mock()
        await manager.connect_logs(mock_ws)
        assert mock_ws in manager.log_connections

    def test_disconnect(self):
        manager = ConnectionManager()
        mock_ws = create_hashable_mock()
        manager.active_connections["task1"] = {mock_ws}
        manager.disconnect(mock_ws, "task1")
        assert "task1" not in manager.active_connections

    def test_disconnect_logs(self):
        manager = ConnectionManager()
        mock_ws = create_hashable_mock()
        manager.log_connections.add(mock_ws)
        manager.disconnect_logs(mock_ws)
        assert mock_ws not in manager.log_connections

    @pytest.mark.asyncio
    async def test_broadcast_to_task_success(self):
        manager = ConnectionManager()
        mock_ws1 = create_hashable_mock()
        mock_ws2 = create_hashable_mock()
        manager.active_connections["task1"] = {mock_ws1, mock_ws2}

        await manager.broadcast_to_task("task1", {"msg": "hi"})
        assert mock_ws1.send_json.called
        assert mock_ws2.send_json.called

    @pytest.mark.asyncio
    async def test_broadcast_to_task_failure_cleanup(self):
        manager = ConnectionManager()
        mock_ws_good = create_hashable_mock("Good")
        mock_ws_bad = create_hashable_mock("Bad")

        # Make send_json fail
        mock_ws_bad.send_json.side_effect = Exception("Disc")

        manager.active_connections["task1"] = {mock_ws_good, mock_ws_bad}
        await manager.broadcast_to_task("task1", {"msg": "hi"})

        assert mock_ws_bad not in manager.active_connections["task1"]
        assert mock_ws_good in manager.active_connections["task1"]

    @pytest.mark.asyncio
    async def test_send_updates(self):
        manager = ConnectionManager()
        mock_ws = create_hashable_mock()
        manager.active_connections["task1"] = {mock_ws}

        await manager.send_progress_update("task1", 50, "doing")
        await manager.send_completion("task1", {"res": "ok"})
        await manager.send_error("task1", "fail")

        assert mock_ws.send_json.call_count == 3

    @pytest.mark.asyncio
    async def test_broadcast_log(self):
        manager = ConnectionManager()
        mock_ws = create_hashable_mock()
        manager.log_connections.add(mock_ws)

        await manager.broadcast_log("hello log")
        assert mock_ws.send_text.called

    def test_get_connection_count(self):
        manager = ConnectionManager()
        ws_mock = create_hashable_mock()
        manager.active_connections["t1"] = {ws_mock}
        assert manager.get_connection_count("t1") == 1
        assert manager.get_connection_count() == 1
