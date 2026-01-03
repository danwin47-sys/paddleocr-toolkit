# -*- coding: utf-8 -*-
"""
Tasks Router - Task Management and Status Tracking Endpoints
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["tasks"])

# Shared state injected from main.py
tasks: Dict[str, Any] = {}
results: Dict[str, Any] = {}


class OCRResult(BaseModel):
    task_id: str
    status: str
    progress: int
    results: Optional[Any] = None
    error: Optional[str] = None
    file_path: Optional[str] = None


@router.get("/api/tasks/{task_id}", response_model=OCRResult)
async def get_task_status(task_id: str):
    """Get task status and results"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task_info = tasks[task_id]

    # If task completed, return result
    if task_id in results:
        return OCRResult(**results[task_id], task_id=task_id)

    # Otherwise return current status
    return OCRResult(
        task_id=task_id, status=task_info["status"], progress=task_info["progress"]
    )


@router.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete task and its results from memory"""
    if task_id in tasks:
        del tasks[task_id]
    if task_id in results:
        del results[task_id]

    return {"message": "任务已删除"}


@router.get("/api/stats")
async def get_stats():
    """Get system task statistics"""
    return {
        "total_tasks": len(tasks),
        "completed_tasks": sum(
            1 for t in tasks.values() if t.get("status") == "completed"
        ),
        "queued_tasks": sum(1 for t in tasks.values() if t.get("status") == "queued"),
        "processing_tasks": sum(
            1 for t in tasks.values() if t.get("status") == "processing"
        ),
    }
