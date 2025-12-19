# -*- coding: utf-8 -*-
"""
API 檔案管理測試
"""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# 確保可以匯入模組
sys.path.append(".")

from paddleocr_toolkit.api.main import UPLOAD_DIR, app, API_KEY


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def api_headers():
    """提供 API 認證 headers"""
    return {"X-API-Key": API_KEY}


@pytest.fixture
def temp_upload_file():
    """建立暫存上傳檔案"""
    filename = "test_file.txt"
    content = b"test content"
    file_path = UPLOAD_DIR / filename

    # 確保目錄存在
    UPLOAD_DIR.mkdir(exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(content)

    yield filename

    # 清理
    if file_path.exists():
        os.remove(file_path)


def test_list_files(client, api_headers, temp_upload_file):
    """測試列出檔案"""
    response = client.get("/api/files", headers=api_headers)
    assert response.status_code == 200
    files = response.json()
    assert isinstance(files, list)

    # 檢查是否包含測試檔案
    found = False
    for f in files:
        if f["name"] == temp_upload_file:
            found = True
            break
    assert found


def test_download_file(client, api_headers, temp_upload_file):
    """測試下載檔案"""
    response = client.get(f"/api/files/{temp_upload_file}/download", headers=api_headers)
    assert response.status_code == 200
    assert response.content == b"test content"


def test_delete_file(client, api_headers, temp_upload_file):
    """測試刪除檔案"""
    # 刪除檔案
    response = client.delete(f"/api/files/{temp_upload_file}", headers=api_headers)
    assert response.status_code == 200
    assert response.json() == {"message": f"檔案 {temp_upload_file} 已刪除"}

    # 確認檔案已刪除
    file_path = UPLOAD_DIR / temp_upload_file
    assert not file_path.exists()

    # 再次刪除應返回 404
    response = client.delete(f"/api/files/{temp_upload_file}", headers=api_headers)
    assert response.status_code == 404
