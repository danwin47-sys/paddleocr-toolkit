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


# Added from Ultra Coverage
from paddleocr_toolkit.api.file_manager import (
    list_files,
    download_file,
    delete_file,
    cleanup_old_files,
    get_file_stats,
)
from fastapi import HTTPException
from unittest.mock import MagicMock, patch
import pytest


class TestFileManagerUltra:
    @pytest.mark.asyncio
    async def test_file_manager_remaining_gaps(self):
        # 1. list_files "output" and "uploads" (lines 56, 58, 63, 65-82)
        with patch("paddleocr_toolkit.api.file_manager.OUTPUT_DIR") as mock_out, patch(
            "paddleocr_toolkit.api.file_manager.UPLOAD_DIR"
        ) as mock_up:
            mock_out.exists.return_value = False
            mock_up.exists.return_value = True

            mock_file = MagicMock()
            mock_file.is_file.return_value = True
            mock_file.name = "test.txt"
            mock_file.suffix = ".txt"
            mock_file.stat.return_value.st_size = 100
            mock_file.stat.return_value.st_mtime = 123456789
            mock_up.iterdir.return_value = [mock_file]

            res_up = await list_files(directory="uploads")
            assert res_up.total == 1
            assert res_up.files[0].name == "test.txt"

            res_out = await list_files(directory="output")
            assert res_out.total == 0

        # 3. download_file success (lines 113-115)
        with patch("paddleocr_toolkit.api.file_manager.OUTPUT_DIR") as mock_out:
            mock_file = mock_out / "test.txt"
            mock_file.exists.return_value = True
            mock_file.is_file.return_value = True
            res = await download_file("test.txt", directory="output")
            assert res is not None

        # 4. delete_file success (line 151)
        with patch("paddleocr_toolkit.api.file_manager.UPLOAD_DIR") as mock_up:
            mock_up.__truediv__.return_value.exists.return_value = True
            res = await delete_file("test.txt")
            assert "已刪除" in res["message"]

        # 6. cleanup_old_files success (line 181)
        with patch("paddleocr_toolkit.api.file_manager.UPLOAD_DIR") as mock_up, patch(
            "paddleocr_toolkit.api.file_manager.OUTPUT_DIR"
        ) as mock_out:
            mock_up.exists.return_value = True
            mock_out.exists.return_value = False
            mock_file = MagicMock()
            mock_file.is_file.return_value = True
            mock_file.stat.return_value.st_mtime = 0  # Very old
            mock_up.iterdir.return_value = [mock_file]

            res = await cleanup_old_files(days=1)
            assert res["deleted_count"] == 1

            # 2. list_files invalid type (line 60)
            with pytest.raises(HTTPException) as exc:
                await list_files(directory="invalid")
            assert exc.value.status_code == 400

        # 3. download_file "uploads" and invalid (lines 98, 102, 110)
        with patch("paddleocr_toolkit.api.file_manager.UPLOAD_DIR") as mock_up:
            mock_up.__truediv__.return_value.exists.return_value = True
            mock_up.__truediv__.return_value.is_file.return_value = False  # Not a file
            with pytest.raises(HTTPException) as exc:
                await download_file("test.txt", directory="uploads")
            assert exc.value.status_code == 400

            with pytest.raises(HTTPException) as exc:
                await download_file("test.txt", directory="invalid")
            assert exc.value.status_code == 400

        # 4. delete_file "output" and invalid (lines 139-142)
        with patch("paddleocr_toolkit.api.file_manager.OUTPUT_DIR") as mock_out:
            mock_out.__truediv__.return_value.exists.return_value = False
            with pytest.raises(HTTPException) as exc:
                await delete_file("test.txt", directory="output")
            assert exc.value.status_code == 404

            with pytest.raises(HTTPException) as exc:
                await delete_file("test.txt", directory="invalid")
            assert exc.value.status_code == 400

        # 5. delete_file exception (lines 152-153)
        with patch("paddleocr_toolkit.api.file_manager.UPLOAD_DIR") as mock_up:
            mock_up.__truediv__.return_value.exists.return_value = True
            mock_up.__truediv__.return_value.unlink.side_effect = Exception(
                "Unlink failed"
            )
            with pytest.raises(HTTPException) as exc:
                await delete_file("test.txt")
            assert exc.value.status_code == 500

        # 6. cleanup_old_files gaps (lines 174, 182-183)
        with patch("paddleocr_toolkit.api.file_manager.UPLOAD_DIR") as mock_up, patch(
            "paddleocr_toolkit.api.file_manager.OUTPUT_DIR"
        ) as mock_out:
            mock_up.exists.return_value = False
            mock_out.exists.return_value = True
            mock_file = MagicMock()
            mock_file.is_file.return_value = True
            mock_file.stat.return_value.st_mtime = 0  # Very old
            mock_file.unlink.side_effect = Exception("Failed")
            mock_out.iterdir.return_value = [mock_file]

            res = await cleanup_old_files(days=1)
            assert res["deleted_count"] == 0  # Failed unlink

        # 7. get_file_stats paths (lines 191-197)
        with patch("paddleocr_toolkit.api.file_manager.UPLOAD_DIR") as mock_up, patch(
            "paddleocr_toolkit.api.file_manager.OUTPUT_DIR"
        ) as mock_out:
            mock_up.exists.return_value = False
            mock_out.exists.return_value = False
            res = await get_file_stats()
            assert res["uploads"]["count"] == 0

    @pytest.mark.asyncio
    async def test_cleanup_errors(self):
        with patch("paddleocr_toolkit.api.file_manager.UPLOAD_DIR") as mock_up, patch(
            "paddleocr_toolkit.api.file_manager.OUTPUT_DIR"
        ) as mock_out, patch("time.time", return_value=1000):
            mock_up.exists.return_value = True
            mock_out.exists.return_value = True
            mock_file = MagicMock()
            mock_file.is_file.return_value = True
            mock_file.stat.return_value.st_mtime = 0
            mock_file.unlink.side_effect = Exception("Delete error")
            mock_up.iterdir.return_value = [mock_file]
            mock_out.iterdir.return_value = []
            res = await cleanup_old_files(days=1)
            assert res["deleted_count"] == 0

    @pytest.mark.asyncio
    async def test_delete_file_exception(self):
        with patch("paddleocr_toolkit.api.file_manager.UPLOAD_DIR") as mock_up:
            mock_file = MagicMock()
            mock_file.exists.return_value = True
            mock_file.unlink.side_effect = Exception("Boom")
            mock_up.__truediv__.return_value = mock_file
            with pytest.raises(HTTPException):
                await delete_file("test.txt", directory="uploads")

    @pytest.mark.asyncio
    async def test_download_file_errors(self):
        with pytest.raises(HTTPException):
            await download_file("test.txt", directory="invalid")
        with patch("paddleocr_toolkit.api.file_manager.OUTPUT_DIR") as mock_out:
            mock_out.__truediv__.return_value.exists.return_value = False
            with pytest.raises(HTTPException):
                await download_file("test.txt", directory="output")
