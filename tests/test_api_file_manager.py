# -*- coding: utf-8 -*-
"""
測試 API 檔案管理功能
"""

import os
import shutil
import tempfile
import time
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from paddleocr_toolkit.api.file_manager import OUTPUT_DIR, UPLOAD_DIR, router

# 建立測試用的 App
app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_dirs(monkeypatch):
    """橫截目錄設定，使用暫存目錄進行測試"""
    with tempfile.TemporaryDirectory() as tmp_uploads:
        with tempfile.TemporaryDirectory() as tmp_outputs:
            p_uploads = Path(tmp_uploads)
            p_outputs = Path(tmp_outputs)
            # 同時 patch 模組級變數與 router 可能引用的變數
            monkeypatch.setattr(
                "paddleocr_toolkit.api.file_manager.UPLOAD_DIR", p_uploads
            )
            monkeypatch.setattr(
                "paddleocr_toolkit.api.file_manager.OUTPUT_DIR", p_outputs
            )

            # 手動確保在執行函式時使用的是這兩個路徑
            yield p_uploads, p_outputs


class TestFileManagerAPI:
    """測試檔案管理 API"""

    def test_list_files_empty(self, mock_dirs):
        """測試空目錄列表"""
        response = client.get("/api/files/list?directory=uploads")
        assert response.status_code == 200
        assert response.json()["total"] == 0
        assert response.json()["files"] == []

    def test_list_files_with_content(self, mock_dirs):
        """測試包含檔案的列表"""
        tmp_uploads, _ = mock_dirs
        test_file = tmp_uploads / "test.txt"
        test_file.write_text("hello color world")

        response = client.get("/api/files/list?directory=uploads")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["files"][0]["name"] == "test.txt"

    def test_list_invalid_directory(self, mock_dirs):
        """測試無效的目錄型別"""
        response = client.get("/api/files/list?directory=invalid")
        assert response.status_code == 400
        assert "無效的目錄" in response.json()["detail"]

    def test_download_file_success(self, mock_dirs):
        """測試下載檔案"""
        _, tmp_outputs = mock_dirs
        content = "download me"
        test_file = tmp_outputs / "dl.txt"
        test_file.write_text(content)

        response = client.get("/api/files/download/dl.txt?directory=output")
        assert response.status_code == 200
        assert response.text == content

    def test_download_file_not_found(self, mock_dirs):
        """測試下載不存在的檔案"""
        response = client.get("/api/files/download/none.txt")
        assert response.status_code == 404

    def test_delete_file_success(self, mock_dirs):
        """測試刪除檔案"""
        tmp_uploads, _ = mock_dirs
        test_file = tmp_uploads / "del_me.txt"
        test_file.write_text("delete")
        assert test_file.exists()

        response = client.delete("/api/files/delete/del_me.txt?directory=uploads")
        assert response.status_code == 200
        assert "已刪除" in response.json()["message"]
        assert not test_file.exists()

    def test_cleanup_old_files(self, mock_dirs):
        """測試清理舊檔案"""
        tmp_uploads, _ = mock_dirs
        # 建立一個舊檔案 (修改時間改為 10 天前)
        old_file = tmp_uploads / "old.txt"
        old_file.write_text("old")
        old_time = time.time() - (10 * 24 * 60 * 60)
        os.utime(old_file, (old_time, old_time))

        # 建立一個新檔案
        new_file = tmp_uploads / "new.txt"
        new_file.write_text("new")

        # 執行清理 (保留 7 天)
        response = client.post("/api/files/cleanup?days=7")
        assert response.status_code == 200
        assert response.json()["deleted_count"] >= 1

        assert not old_file.exists()
        assert new_file.exists()

    def test_get_stats(self, mock_dirs):
        """測試統計資訊"""
        tmp_uploads, tmp_outputs = mock_dirs
        (tmp_uploads / "f1.txt").write_text("data")
        (tmp_outputs / "f2.txt").write_text("more data")

        response = client.get("/api/files/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["uploads"]["count"] >= 1
        assert data["outputs"]["count"] >= 1
        assert data["total_size_mb"] >= 0
