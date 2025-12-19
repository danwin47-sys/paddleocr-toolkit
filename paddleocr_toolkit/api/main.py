#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI後端 - Web介面
v1.2.0新增 - REST API服務
"""

import asyncio
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Security,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from paddleocr_toolkit.api.websocket_manager import manager
from paddleocr_toolkit.core.ocr_engine import OCREngineManager
from paddleocr_toolkit.plugins.loader import PluginLoader

# 環境變數讀取
import os
from dotenv import load_dotenv

load_dotenv()  # 讀取 .env 檔案

# 安全性設定
API_KEY = os.getenv("API_KEY", "dev-key-change-in-production")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# API Key 驗證
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    驗證 API Key
    
    Args:
        api_key: 從 header 中提取的 API Key
    
    Raises:
        HTTPException: 如果 API Key 無效
    """
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key


# 找到 web 目錄
WEB_DIR = Path(__file__).parent.parent.parent / "web"

app = FastAPI(
    title="PaddleOCR Toolkit API", 
    description="專業級OCR檔案處理API", 
    version="1.2.0",
    docs_url="/docs",  # API 檔案放在 /docs
    redoc_url="/redoc"
)

# CORS設定 (使用環境變數)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 任務儲存（生產環境應使用Redis等）
tasks = {}
results = {}

# 配置
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
PLUGIN_DIR = Path("paddleocr_toolkit/plugins")

# 初始化外掛載入器（安全性：可透過環境變數禁用）
ENABLE_PLUGINS = os.getenv("ENABLE_PLUGINS", "true").lower() == "true"
plugin_loader = PluginLoader(str(PLUGIN_DIR), enable_plugins=ENABLE_PLUGINS)
plugin_loader.load_all_plugins()

# 圖片大小限制 (避免 OCR 記憶體不足)
MAX_IMAGE_SIDE = 2500  # 畫素


def resize_image_if_needed(file_path: str, max_side: int = MAX_IMAGE_SIDE) -> str:
    """
    檢測並縮小大圖片以避免 OCR 記憶體問題
    
    Args:
        file_path: 圖片路徑
        max_side: 最大邊長（預設 2500px）
    
    Returns:
        處理後的圖片路徑（縮小後的新檔案或原檔案）
    """
    try:
        from PIL import Image
        
        with Image.open(file_path) as img:
            width, height = img.size
            max_dim = max(width, height)
            
            if max_dim <= max_side:
                print(f"圖片大小 {width}x{height} 在限制內，不需要縮小")
                return file_path
            
            # 計算縮放比例
            scale = max_side / max_dim
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            print(f"圖片太大 ({width}x{height})，縮小為 {new_width}x{new_height}")
            
            # 縮小圖片
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 儲存到新檔案
            path = Path(file_path)
            new_path = path.parent / f"{path.stem}_resized{path.suffix}"
            resized_img.save(str(new_path), quality=95)
            
            print(f"縮小後圖片已儲存: {new_path}")
            return str(new_path)
            
    except Exception as e:
        print(f"縮小圖片時發生錯誤: {e}，使用原始圖片")
        return file_path


class OCRRequest(BaseModel):
    """OCR請求模型"""

    mode: str = "hybrid"
    dpi: int = 200
    lang: str = "ch"


class TaskResponse(BaseModel):
    """任務回應模型"""
    task_id: str
    status: str
    message: str
    result: Optional[Dict[str, Any]] = None


class OCRResult(BaseModel):
    """OCR結果模型"""

    task_id: str
    status: str
    progress: float
    results: Optional[Any] = None
    error: Optional[str] = None


async def process_ocr_task(task_id: str, file_path: str, mode: str):
    """
    後臺OCR處理任務 (Async)

    Args:
        task_id: 任務ID
        file_path: 檔案路徑
        mode: OCR模式
    """
    try:
        tasks[task_id] = {"status": "processing", "progress": 0}
        await manager.send_progress_update(task_id, 0, "processing", "任務開始")

        # 0. 檢測並縮小大圖片
        processed_path = file_path
        if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp')):
            await manager.send_progress_update(task_id, 5, "processing", "檢查圖片大小...")
            processed_path = await asyncio.to_thread(resize_image_if_needed, file_path)

        # 1. 初始化引擎
        await manager.send_progress_update(task_id, 10, "processing", "初始化OCR引擎...")

        def run_ocr():
            # 在執行緒中執行阻塞的OCR操作
            ocr_manager = OCREngineManager(
                mode=mode, device="cpu", plugin_loader=plugin_loader
            )  # 預設使用CPU以確保相容性
            ocr_manager.init_engine()
            return ocr_manager

        # 使用 asyncio.to_thread 執行阻塞程式碼
        ocr_manager = await asyncio.to_thread(run_ocr)

        # 2. 執行預測
        await manager.send_progress_update(task_id, 30, "processing", "正在進行OCR識別...")

        def predict(engine, path):
            return engine.predict(path)

        ocr_result = await asyncio.to_thread(predict, ocr_manager, processed_path)

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
    """提供使用者友好的 Web 介面"""
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="""
        <h1>PaddleOCR Toolkit API</h1>
        <p>Version: 1.2.0</p>
        <p><a href="/docs">API 檔案</a></p>
    """)


@app.post("/api/ocr", response_model=TaskResponse)
async def upload_and_ocr(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,  # type: ignore[assignment]
    mode: str = "hybrid",
    api_key: str = Depends(verify_api_key),
):
    """
    上傳檔案並進行OCR處理

    Args:
        file: 上傳的檔案
        background_tasks: 後臺任務
        mode: OCR模式

    Returns:
        任務ID和狀態
    """
    # 生成任務ID
    task_id = str(uuid.uuid4())

    # 儲存檔案 (安全性：清理檔名以防止路徑遍歷)
    safe_filename = Path(file.filename).name
    file_path = UPLOAD_DIR / f"{task_id}_{safe_filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 建立後臺任務
    background_tasks.add_task(process_ocr_task, task_id, str(file_path), mode)

    # 初始化任務狀態
    tasks[task_id] = {"status": "queued", "progress": 0}

    return TaskResponse(task_id=task_id, status="queued", message="任務已建立，正在處理...")


@app.get("/api/status/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """
    獲取任務狀態

    Args:
        task_id: 任務ID

    Returns:
        任務狀態和結果
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任務不存在")

    task_info = tasks[task_id]

    # 如果任務完成，返回結果
    if task_id in results:
        return TaskResponse(
            task_id=task_id,
            status=results[task_id]["status"],
            message="任務已完成",
            result=results[task_id]["results"]
        )

    # 否則返回當前狀態
    return TaskResponse(
        task_id=task_id,
        status=task_info["status"],
        message="任務正在處理中",
        result=None
    )


@app.get("/api/results/{task_id}")
async def get_results(task_id: str):
    """
    獲取OCR結果

    Args:
        task_id: 任務ID

    Returns:
        OCR結果
    """
    if task_id not in results:
        raise HTTPException(status_code=404, detail="結果不存在")

    return results[task_id]


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """刪除任務"""
    if task_id in tasks:
        del tasks[task_id]
    if task_id in results:
        del results[task_id]

    return {"message": "任務已刪除"}


@app.get("/api/stats")
async def get_stats():
    """獲取系統統計"""
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


@app.delete("/api/files/{filename}", dependencies=[Depends(verify_api_key)])
async def delete_file(filename: str):
    """刪除檔案"""
    # 安全性：清理檔名以防止路徑遍歷
    safe_filename = Path(filename).name
    file_path = UPLOAD_DIR / safe_filename
    
    # 確保檔案在 UPLOAD_DIR 內 - Python 3.8 兼容
    try:
        file_path_resolved = file_path.resolve()
        upload_dir_resolved = UPLOAD_DIR.resolve()
        if not str(file_path_resolved).startswith(str(upload_dir_resolved)):
            raise HTTPException(status_code=400, detail="無效的檔案路徑")
    except (ValueError, OSError):
        raise HTTPException(status_code=400, detail="無效的檔案路徑")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="檔案不存在")

    try:
        os.remove(file_path)
        return {"message": f"檔案 {filename} 已刪除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除失敗: {str(e)}")


@app.get("/api/files/{filename}/download", dependencies=[Depends(verify_api_key)])
async def download_file(filename: str):
    """下載檔案"""
    file_path = UPLOAD_DIR / filename
    
    # 安全性檢查：防止路徑遍歷攻擊
    # Python 3.8 兼容：使用 resolve() 和字串比較代替 is_relative_to
    try:
        file_path_resolved = file_path.resolve()
        upload_dir_resolved = UPLOAD_DIR.resolve()
        # 檢查解析後的路徑是否以上傳目錄開頭
        if not str(file_path_resolved).startswith(str(upload_dir_resolved)):
            raise HTTPException(status_code=400, detail="Invalid file path")
    except (ValueError, OSError):
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="檔案不存在")

    return FileResponse(file_path, filename=filename)


@app.get("/api/plugins")
async def list_plugins():
    """列出所有外掛"""
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
    
    啟動伺服器...
    API文件: http://localhost:8000/docs
    """
    )

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
