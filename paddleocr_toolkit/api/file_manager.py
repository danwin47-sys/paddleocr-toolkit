#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檔案管理API
提供檔案列表、刪除、下載功能
"""

import sys
import io

# Windows UTF-8修復
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except:
        pass

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List
from pydantic import BaseModel
import os
import time

router = APIRouter(prefix="/api/files", tags=["files"])

# 設定目錄
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("output")

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


class FileInfo(BaseModel):
    """檔案資訊模型"""
    name: str
    path: str
    size: int
    type: str
    modified: float


class FileListResponse(BaseModel):
    """檔案列表回應"""
    files: List[FileInfo]
    total: int


@router.get("/list", response_model=FileListResponse)
async def list_files(directory: str = "uploads"):
    """
    列出檔案
    
    Args:
        directory: 目錄類型 (uploads/output)
    
    Returns:
        檔案列表
    """
    if directory == "uploads":
        target_dir = UPLOAD_DIR
    elif directory == "output":
        target_dir = OUTPUT_DIR
    else:
        raise HTTPException(status_code=400, detail="無效的目錄類型")
    
    if not target_dir.exists():
        return FileListResponse(files=[], total=0)
    
    files = []
    for file_path in target_dir.iterdir():
        if file_path.is_file():
            stat = file_path.stat()
            files.append(FileInfo(
                name=file_path.name,
                path=str(file_path),
                size=stat.st_size,
                type=file_path.suffix,
                modified=stat.st_mtime
            ))
    
    # 按修改時間排序（最新的在前）
    files.sort(key=lambda x: x.modified, reverse=True)
    
    return FileListResponse(files=files, total=len(files))


@router.get("/download/{filename}")
async def download_file(filename: str, directory: str = "output"):
    """
    下載檔案
    
    Args:
        filename: 檔案名稱
        directory: 目錄類型
    
    Returns:
        檔案回應
    """
    if directory == "uploads":
        target_dir = UPLOAD_DIR
    elif directory == "output":
        target_dir = OUTPUT_DIR
    else:
        raise HTTPException(status_code=400, detail="無效的目錄類型")
    
    file_path = target_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="檔案不存在")
    
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="不是檔案")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )


@router.delete("/delete/{filename}")
async def delete_file(filename: str, directory: str = "uploads"):
    """
    刪除檔案
    
    Args:
        filename: 檔案名稱
        directory: 目錄類型
    
    Returns:
        刪除結果
    """
    if directory == "uploads":
        target_dir = UPLOAD_DIR
    elif directory == "output":
        target_dir = OUTPUT_DIR
    else:
        raise HTTPException(status_code=400, detail="無效的目錄類型")
    
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
    """
    清理舊檔案
    
    Args:
        days: 保留天數
    
    Returns:
        清理結果
    """
    now = time.time()
    threshold = now - (days * 24 * 60 * 60)
    
    deleted_count = 0
    
    for directory in [UPLOAD_DIR, OUTPUT_DIR]:
        if not directory.exists():
            continue
        
        for file_path in directory.iterdir():
            if file_path.is_file():
                if file_path.stat().st_mtime < threshold:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception:
                        pass
    
    return {
        "message": f"已刪除 {deleted_count} 個舊檔案",
        "deleted_count": deleted_count
    }


@router.get("/stats")
async def get_file_stats():
    """取得檔案統計"""
    upload_files = list(UPLOAD_DIR.glob("*")) if UPLOAD_DIR.exists() else []
    output_files = list(OUTPUT_DIR.glob("*")) if OUTPUT_DIR.exists() else []
    
    upload_size = sum(f.stat().st_size for f in upload_files if f.is_file())
    output_size = sum(f.stat().st_size for f in output_files if f.is_file())
    
    return {
        "uploads": {
            "count": len(upload_files),
            "size": upload_size,
            "size_mb": round(upload_size / 1024 / 1024, 2)
        },
        "outputs": {
            "count": len(output_files),
            "size": output_size,
            "size_mb": round(output_size / 1024 / 1024, 2)
        },
        "total_size_mb": round((upload_size + output_size) / 1024 / 1024, 2)
    }
