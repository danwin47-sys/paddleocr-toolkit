# -*- coding: utf-8 -*-
"""
Tasks Router Tests
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from paddleocr_toolkit.api.routers import tasks


class TestTasksRouter:
    @pytest.fixture
    def client(self):
        """Create test client with tasks router"""
        app = FastAPI()
        tasks.tasks = {}
        tasks.results = {}
        app.include_router(tasks.router)
        return TestClient(app)

    def test_get_task_status_not_found(self, client):
        """Test 404 for missing task"""
        response = client.get("/api/tasks/missing")
        assert response.status_code == 404

    def test_get_task_status_queued(self, client):
        """Test status for queued task"""
        tasks.tasks["t1"] = {"status": "queued", "progress": 0}
        response = client.get("/api/tasks/t1")
        assert response.status_code == 200
        assert response.json()["status"] == "queued"

    def test_get_task_status_completed(self, client):
        """Test status for completed task"""
        tasks.tasks["t1"] = {"status": "completed", "progress": 100}
        tasks.results["t1"] = {
            "status": "completed",
            "progress": 100,
            "results": {"data": "ok"},
        }

        response = client.get("/api/tasks/t1")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
        assert response.json()["results"]["data"] == "ok"

    def test_delete_task(self, client):
        """Test task deletion"""
        tasks.tasks["t1"] = {}
        tasks.results["t1"] = {}
        response = client.delete("/api/tasks/t1")
        assert response.status_code == 200
        assert "t1" not in tasks.tasks
        assert "t1" not in tasks.results

    def test_get_stats(self, client):
        """Test getting task stats"""
        tasks.tasks = {
            "1": {"status": "completed"},
            "2": {"status": "queued"},
            "3": {"status": "processing"},
        }
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["completed_tasks"] == 1
        assert data["queued_tasks"] == 1
        assert data["processing_tasks"] == 1
