#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI后端 - Web界面
v1.2.0新增 - REST API服务
"""

import sys
import io

# Windows UTF-8修复
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except:
        pass

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import time
from pathlib import Path

app = FastAPI(
    title="PaddleOCR Toolkit API",
    description="专业级OCR文件处理API",
    version="1.2.0"
)

# CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 任务存储（生产环境应使用Redis等）
tasks = {}
results = {}

# 配置
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class OCRRequest(BaseModel):
    """OCR请求模型"""
    mode: str = "hybrid"
    dpi: int = 200
    lang: str = "ch"


class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: str
    status: str
    message: str


class OCRResult(BaseModel):
    """OCR结果模型"""
    task_id: str
    status: str
    progress: float
    results: Optional[Any] = None
    error: Optional[str] = None


def process_ocr_task(task_id: str, file_path: str, mode: str):
    """
    后台OCR处理任务
    
    Args:
        task_id: 任务ID
        file_path: 文件路径
        mode: OCR模式
    """
    try:
        tasks[task_id] = {"status": "processing", "progress": 0}
        
        # 模拟OCR处理
        time.sleep(2)  # 实际应该调用OCR引擎
        
        # 更新进度
        tasks[task_id] = {"status": "processing", "progress": 50}
        time.sleep(1)
        
        # 完成
        results[task_id] = {
            "status": "completed",
            "progress": 100,
            "results": {
                "text": "这是OCR识别的文字",
                "pages": 1,
                "confidence": 0.95
            }
        }
        tasks[task_id] = {"status": "completed", "progress": 100}
        
    except Exception as e:
        results[task_id] = {
            "status": "failed",
            "progress": 0,
            "error": str(e)
        }
        tasks[task_id] = {"status": "failed", "progress": 0}


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "PaddleOCR Toolkit API",
        "version": "1.2.0",
        "status": "running"
    }


@app.post("/api/ocr", response_model=TaskResponse)
async def upload_and_ocr(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    mode: str = "hybrid"
):
    """
    上传文件并进行OCR处理
    
    Args:
        file: 上传的文件
        background_tasks: 后台任务
        mode: OCR模式
        
    Returns:
        任务ID和状态
    """
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 保存文件
    file_path = UPLOAD_DIR / f"{task_id}_{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # 创建后台任务
    background_tasks.add_task(process_ocr_task, task_id, str(file_path), mode)
    
    # 初始化任务状态
    tasks[task_id] = {"status": "queued", "progress": 0}
    
    return TaskResponse(
        task_id=task_id,
        status="queued",
        message="任务已创建，正在处理..."
    )


@app.get("/api/tasks/{task_id}", response_model=OCRResult)
async def get_task_status(task_id: str):
    """
    获取任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务状态和结果
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task_info = tasks[task_id]
    
    # 如果任务完成，返回结果
    if task_id in results:
        return OCRResult(**results[task_id], task_id=task_id)
    
    # 否则返回当前状态
    return OCRResult(
        task_id=task_id,
        status=task_info["status"],
        progress=task_info["progress"]
    )


@app.get("/api/results/{task_id}")
async def get_results(task_id: str):
    """
    获取OCR结果
    
    Args:
        task_id: 任务ID
        
    Returns:
        OCR结果
    """
    if task_id not in results:
        raise HTTPException(status_code=404, detail="结果不存在")
    
    return results[task_id]


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    if task_id in tasks:
        del tasks[task_id]
    if task_id in results:
        del results[task_id]
    
    return {"message": "任务已删除"}


@app.get("/api/stats")
async def get_stats():
    """获取系统统计"""
    return {
        "total_tasks": len(tasks),
        "completed_tasks": sum(1 for t in tasks.values() if t["status"] == "completed"),
        "queued_tasks": sum(1 for t in tasks.values() if t["status"] == "queued"),
        "processing_tasks": sum(1 for t in tasks.values() if t["status"] == "processing")
    }


if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║     PaddleOCR Toolkit API Server                     ║
    ║     v1.2.0                                           ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    
    启动服务器...
    API文档: http://localhost:8000/docs
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
