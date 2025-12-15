#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI后端 - Web界面
v1.2.0新增 - REST API服务
"""

import asyncio
import os
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from paddleocr_toolkit.api.websocket_manager import manager
from paddleocr_toolkit.core.ocr_engine import OCREngineManager
from paddleocr_toolkit.plugins.loader import PluginLoader

# 找到 web 目錄
WEB_DIR = Path(__file__).parent.parent.parent / "web"

app = FastAPI(
    title="PaddleOCR Toolkit API", 
    description="专业级OCR文件处理API", 
    version="1.2.0",
    docs_url="/docs",  # API 文件放在 /docs
    redoc_url="/redoc"
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
PLUGIN_DIR = Path("paddleocr_toolkit/plugins")

# 初始化插件載入器
plugin_loader = PluginLoader(str(PLUGIN_DIR))
plugin_loader.load_all_plugins()


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


async def process_ocr_task(task_id: str, file_path: str, mode: str):
    """
    后台OCR处理任务 (Async)

    Args:
        task_id: 任务ID
        file_path: 文件路径
        mode: OCR模式
    """
    try:
        tasks[task_id] = {"status": "processing", "progress": 0}
        await manager.send_progress_update(task_id, 0, "processing", "任务开始")

        # 1. 初始化引擎
        await manager.send_progress_update(task_id, 10, "processing", "初始化OCR引擎...")

        def run_ocr():
            # 在线程中运行阻塞的OCR操作
            ocr_manager = OCREngineManager(
                mode=mode, device="cpu", plugin_loader=plugin_loader
            )  # 默认使用CPU以确保兼容性
            ocr_manager.init_engine()
            return ocr_manager

        # 使用 asyncio.to_thread 運行阻塞代碼
        ocr_manager = await asyncio.to_thread(run_ocr)

        # 2. 執行預測
        await manager.send_progress_update(task_id, 30, "processing", "正在進行OCR識別...")

        def predict(engine, path):
            return engine.predict(path)

        ocr_result = await asyncio.to_thread(predict, ocr_manager, file_path)

        # 3. 處理結果
        await manager.send_progress_update(task_id, 90, "processing", "處理結果...")

        # 簡單序列化結果 (根據實際返回結構可能需要調整)
        # 假設 result 是 list 或 dict，可以直接序列化
        # 如果包含 numpy array，需要轉換

        # 模擬結果處理 (實際應解析 ocr_result)
        final_result = {
            "raw_result": str(ocr_result)[:1000] + "..."
            if len(str(ocr_result)) > 1000
            else str(ocr_result),
            "pages": 1,  # 暫時 hardcode
            "confidence": 0.95,
        }

        # 完成
        results[task_id] = {
            "status": "completed",
            "progress": 100,
            "results": final_result,
        }
        tasks[task_id] = {"status": "completed", "progress": 100}

        await manager.send_completion(task_id, final_result)

        # 清理
        ocr_manager.close()

    except Exception as e:
        error_msg = str(e)
        print(f"Task {task_id} failed: {error_msg}")
        results[task_id] = {"status": "failed", "progress": 0, "error": error_msg}
        tasks[task_id] = {"status": "failed", "progress": 0}
        await manager.send_error(task_id, error_msg)

@app.get("/", response_class=HTMLResponse)
async def root():
    """提供用戶友好的 Web 介面"""
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="""
        <h1>PaddleOCR Toolkit API</h1>
        <p>Version: 1.2.0</p>
        <p><a href="/docs">API 文件</a></p>
    """)


@app.post("/api/ocr", response_model=TaskResponse)
async def upload_and_ocr(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,  # type: ignore[assignment]
    mode: str = "hybrid",
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

    return TaskResponse(task_id=task_id, status="queued", message="任务已创建，正在处理...")


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
        task_id=task_id, status=task_info["status"], progress=task_info["progress"]
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
        "processing_tasks": sum(
            1 for t in tasks.values() if t["status"] == "processing"
        ),
    }


@app.get("/api/files")
async def list_files():
    """列出所有上傳的檔案"""
    files = []
    if UPLOAD_DIR.exists():
        for f in UPLOAD_DIR.iterdir():
            if f.is_file():
                stat = f.stat()
                files.append(
                    {
                        "name": f.name,
                        "size": stat.st_size,
                        "created_at": stat.st_ctime,
                        "modified_at": stat.st_mtime,
                    }
                )
    return files


@app.delete("/api/files/{filename}")
async def delete_file(filename: str):
    """刪除檔案"""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="檔案不存在")

    try:
        os.remove(file_path)
        return {"message": f"檔案 {filename} 已刪除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除失敗: {str(e)}")


@app.get("/api/files/{filename}/download")
async def download_file(filename: str):
    """下載檔案"""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="檔案不存在")

    return FileResponse(
        path=file_path, filename=filename, media_type="application/octet-stream"
    )


@app.get("/api/plugins")
async def list_plugins():
    """列出所有插件"""
    return plugin_loader.list_plugins()


@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time task updates
    """
    await manager.connect(websocket, task_id)
    try:
        while True:
            # Keep connection alive and listen for client messages if needed
            # For now, we just push updates from server
            data = await websocket.receive_text()
            # Optional: handle client commands
            if data == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, task_id)


if __name__ == "__main__":
    import uvicorn

    print(
        """
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║     PaddleOCR Toolkit API Server                     ║
    ║     v1.2.0                                           ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    
    启动服务器...
    API文档: http://localhost:8000/docs
    """
    )

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
