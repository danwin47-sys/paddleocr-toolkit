# -*- coding: utf-8 -*-
"""
System Router Tests
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from paddleocr_toolkit.api.routers import system


class TestSystemRouter:
    @pytest.fixture
    def client(self):
        """Create test client with system router"""
        app = FastAPI()

        # Inject dependencies
        system.app_start_time = MagicMock()
        system.app_start_time.total_seconds.return_value = 100
        system.ocr_engine_cache = MagicMock()
        system.task_queue = MagicMock()
        system.results = {"task1": {"status": "completed"}}

        # Simple async mock for manager.connect
        async def async_mock(websocket, *args, **kwargs):
            await websocket.accept()

        system.manager = MagicMock()
        system.manager.connect = MagicMock(side_effect=async_mock)
        system.manager.active_connections = []
        system.manager.log_connections = []

        app.include_router(system.router)
        return TestClient(app)

    def test_health_check(self, client):
        """Test health check endpoint"""
        from datetime import datetime as dt

        with patch("paddleocr_toolkit.api.routers.system.datetime") as mock_dt:
            # Mock datetime.now() to return a proper datetime object
            mock_now = dt(2024, 1, 1, 12, 0, 0)
            mock_dt.now.return_value = mock_now

            # Mock app_start_time to be 100 seconds earlier
            system.app_start_time = dt(2024, 1, 1, 11, 58, 20)

            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "uptime_seconds" in data
            assert data["components"]["ocr_engine"] == "ready"

    def test_get_metrics(self, client):
        """Test metrics endpoint"""
        with patch("paddleocr_toolkit.api.routers.system.psutil") as mock_psutil:
            mock_psutil.cpu_percent.return_value = 25.5
            mock_psutil.cpu_count.return_value = 4
            mock_psutil.virtual_memory.return_value = MagicMock(
                total=8 * 1024**3,
                available=4 * 1024**3,
                used=4 * 1024**3,
                percent=50.0,
            )
            mock_psutil.disk_usage.return_value = MagicMock(
                total=100 * 1024**3,
                used=50 * 1024**3,
                free=50 * 1024**3,
                percent=50.0,
            )
            mock_psutil.Process.return_value.memory_info.return_value.rss = (
                512 * 1024**2
            )

            response = client.get("/api/metrics")
            assert response.status_code == 200
            data = response.json()
            assert data["cpu"]["percent"] == 25.5
            assert data["cpu"]["count"] == 4
            assert data["memory"]["percent"] == 50.0
            assert data["disk"]["percent"] == 50.0

    def test_get_queue_status(self, client):
        """Test queue status endpoint"""
        system.task_queue.get_status.return_value = {
            "queue_size": 5,
            "active_tasks": 2,
            "max_workers": 2,
        }

        response = client.get("/api/queue/status")
        assert response.status_code == 200
        data = response.json()
        assert data["queue_size"] == 5
        assert data["active_tasks"] == 2

    def test_get_queue_status_not_initialized(self, client):
        """Test queue status when queue not initialized"""
        system.task_queue = None

        response = client.get("/api/queue/status")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["queue_size"] == 0

    def test_list_plugins(self, client):
        """Test listing plugins"""
        mock_loader = MagicMock()
        mock_loader.get_all_plugins.return_value = {
            "TestPlugin": MagicMock(version="1.0.0", description="Test")
        }
        system.plugin_loader = mock_loader

        response = client.get("/api/plugins")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "TestPlugin"

    def test_websocket_logs_connection(self, client):
        """Test WebSocket logs connection"""
        with client.websocket_connect("/ws/logs") as ws:
            ws.send_text("ping")
            # The actual behavior depends on how manager is mocked
            # But the connection itself should succeed
            pass
        assert system.manager.connect.called
