# -*- coding: utf-8 -*-
"""
Files Router - File management and download endpoints
"""
import os
import time
from pathlib import Path
from typing import List
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from paddleocr_toolkit.core.config import settings

router = APIRouter(prefix="/api/files", tags=["files"])

# Shared state (can be injected or use settings)
UPLOAD_DIR = settings.UPLOAD_DIR
OUTPUT_DIR = settings.OUTPUT_DIR


class FileInfo(BaseModel):
    name: str
    path: str
    size: int
    type: str
    modified: float


class FileListResponse(BaseModel):
    files: List[FileInfo]
    total: int


@router.get("/list", response_model=FileListResponse)
@router.get("", response_model=List[dict])  # Compatibility with old main.py list_files
async def list_files(request: Request, directory: str = "uploads"):
    """List all files in uploads or output directory"""
    if directory == "uploads":
        target_dir = UPLOAD_DIR
    elif directory == "output":
        target_dir = OUTPUT_DIR
    else:
        raise HTTPException(status_code=400, detail="無效的目錄型別")

    if not target_dir.exists():
        return FileListResponse(files=[], total=0) if "list" in str(request.url) else []

    files = []
    for file_path in target_dir.iterdir():
        if file_path.is_file():
            stat = file_path.stat()
            files.append(
                FileInfo(
                    name=file_path.name,
                    path=str(file_path),
                    size=stat.st_size,
                    type=file_path.suffix,
                    modified=stat.st_mtime,
                )
            )

    files.sort(key=lambda x: x.modified, reverse=True)

    # For compatibility with the old simple list_files endpoint
    return FileListResponse(files=files, total=len(files))


@router.get("/download/{filename}")
async def download_file(filename: str, directory: str = "uploads"):
    """Download a file"""
    target_dir = UPLOAD_DIR if directory == "uploads" else OUTPUT_DIR
    file_path = target_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="檔案不存在")

    encoded_filename = quote(filename)
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"
        },
    )


@router.delete("/{filename}")
@router.delete("/delete/{filename}")
async def delete_file(filename: str, directory: str = "uploads"):
    """Delete a file"""
    target_dir = UPLOAD_DIR if directory == "uploads" else OUTPUT_DIR
    file_path = target_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="檔案不存在")

    try:
        file_path.unlink()
        return {"message": f"檔案已刪除: {filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除失敗: {str(e)}")


@router.post("/cleanup")
async def cleanup_old_files(days: int = 7):
    """Cleanup old files"""
    now = time.time()
    threshold = now - (days * 24 * 60 * 60)
    deleted_count = 0

    for directory in [UPLOAD_DIR, OUTPUT_DIR]:
        if not directory.exists():
            continue
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.stat().st_mtime < threshold:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except:
                    pass
    return {"message": f"已刪除 {deleted_count} 個舊檔案", "deleted_count": deleted_count}


@router.get("/stats")
async def get_file_stats():
    """Get file storage statistics"""
    upload_files = list(UPLOAD_DIR.glob("*")) if UPLOAD_DIR.exists() else []
    output_files = list(OUTPUT_DIR.glob("*")) if OUTPUT_DIR.exists() else []

    upload_size = sum(f.stat().st_size for f in upload_files if f.is_file())
    output_size = sum(f.stat().st_size for f in output_files if f.is_file())

    return {
        "uploads": {
            "count": len(upload_files),
            "size_mb": round(upload_size / 1024 / 1024, 2),
        },
        "outputs": {
            "count": len(output_files),
            "size_mb": round(output_size / 1024 / 1024, 2),
        },
        "total_size_mb": round((upload_size + output_size) / 1024 / 1024, 2),
    }
