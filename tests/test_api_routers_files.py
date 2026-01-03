# -*- coding: utf-8 -*-
"""
Files Router Tests
"""
import os
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from pathlib import Path
from paddleocr_toolkit.api.routers import files


class TestFilesRouter:
    @pytest.fixture
    def client(self):
        """Create test client with files router"""
        app = FastAPI()

        # Setup temporary directories
        files.UPLOAD_DIR = Path("tmp_uploads_files")
        files.OUTPUT_DIR = Path("tmp_output_files")
        files.UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
        files.OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

        # Create dummy files
        (files.UPLOAD_DIR / "test1.png").write_text("content1")
        (files.OUTPUT_DIR / "result1.docx").write_text("result content")

        app.include_router(files.router)
        return TestClient(app)

    def test_list_files_uploads(self, client):
        """Test listing uploaded files"""
        response = client.get("/api/files/list?directory=uploads")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(f["name"] == "test1.png" for f in data["files"])

    def test_list_files_output(self, client):
        """Test listing output files"""
        response = client.get("/api/files/list?directory=output")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(f["name"] == "result1.docx" for f in data["files"])

    def test_download_file_success(self, client):
        """Test successful file download"""
        response = client.get("/api/files/download/test1.png?directory=uploads")
        assert response.status_code == 200
        assert response.text == "content1"
        assert "attachment" in response.headers["content-disposition"]

    def test_download_file_not_found(self, client):
        """Test 404 for missing file"""
        response = client.get("/api/files/download/missing.txt")
        assert response.status_code == 404

    def test_delete_file_success(self, client):
        """Test successful file deletion"""
        response = client.delete("/api/files/test1.png?directory=uploads")
        assert response.status_code == 200
        assert not (files.UPLOAD_DIR / "test1.png").exists()

    def test_get_file_stats(self, client):
        """Test file statistics endpoint"""
        response = client.get("/api/files/stats")
        assert response.status_code == 200
        data = response.json()
        assert "uploads" in data
        assert "outputs" in data
        assert data["uploads"]["count"] >= 0

    def test_cleanup_old_files(self, client):
        """Test cleanup endpoint"""
        # Set old mtime for a file
        old_file = files.UPLOAD_DIR / "old.txt"
        old_file.write_text("old")
        os.utime(str(old_file), (0, 0))  # Set to epoch

        response = client.post("/api/files/cleanup?days=1")
        assert response.status_code == 200
        assert not old_file.exists()
        assert response.json()["deleted_count"] >= 1
