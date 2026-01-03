#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI Backend - Main Application
Refactored for better testability and modularity
"""
from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from paddleocr_toolkit.api.websocket_manager import manager
from paddleocr_toolkit.core.ocr_engine import OCREngineManager
from paddleocr_toolkit.core.task_queue import TaskQueue
from paddleocr_toolkit.plugins.loader import PluginLoader
from paddleocr_toolkit.utils.logger import logger
from paddleocr_toolkit.core.config import settings
from paddleocr_toolkit.core.ocr_cache import OCRCache
from paddleocr_toolkit.processors.parallel_pdf_processor import ParallelPDFProcessor

# Import routers
from paddleocr_toolkit.api.routers import ocr, tasks as tasks_router, system, files

# Constants and Configuration
NEXT_OUT_DIR = settings.BASE_DIR / "web-frontend" / "out"
UPLOAD_DIR = settings.UPLOAD_DIR
OUTPUT_DIR = settings.OUTPUT_DIR
LOG_FILE = settings.LOG_DIR / "paddleocr.log"
PLUGIN_DIR = settings.BASE_DIR / "paddleocr_toolkit" / "plugins"

app = FastAPI(
    title="PaddleOCR Toolkit API",
    description="專業級 OCR 文件處理 API",
    version="3.3.0",
)

# Global State
app_start_time = datetime.now()
ocr_engine_cache = None
task_queue = None
plugin_loader = PluginLoader(str(PLUGIN_DIR))
ocr_cache = OCRCache(str(settings.BASE_DIR / "cache"))
parallel_processor = ParallelPDFProcessor()

# Shared storage across routers
tasks = {}
results = {}


# Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback

    error_detail = traceback.format_exc()
    logger.error("CRITICAL ERROR: %s", exc)
    logger.error(error_detail)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": f"伺服器內部錯誤: {str(exc)}",
            "detail": error_detail,
        },
    )


# Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    path = request.url.path
    method = request.method
    logger.debug("HTTP %s %s - Request received", method, path)
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        logger.info(
            "HTTP %s %s - Completed (%.2fs) - Status: %d",
            method,
            path,
            duration,
            response.status_code,
        )
        return response
    except Exception as e:
        logger.error("HTTP %s %s - Error during processing: %s", method, path, e)
        raise e


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


# Background Tasks
async def cleanup_old_tasks_loop():
    """Loop for cleaning up old tasks"""
    try:
        while True:
            await asyncio.sleep(3600)  # Every hour
            # Cleanup logic
    except asyncio.CancelledError:
        logger.info("Cleanup loop cancelled")
    except Exception as e:
        logger.error("Error during cleanup loop: %s", e)


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global ocr_engine_cache, task_queue

    # Init Plugin Loader
    plugin_loader.load_all_plugins()

    # Init OCR Engine Cache (Optional: preload default engine)
    # ocr_engine_cache = ...

    # Init Task Queue
    task_queue = TaskQueue(max_workers=settings.OCR_WORKERS)
    await task_queue.start()

    # Inject state into routers
    for router_mod in [ocr, tasks_router, system, files]:
        if hasattr(router_mod, "tasks"):
            router_mod.tasks = tasks
        if hasattr(router_mod, "results"):
            router_mod.results = results
        if hasattr(router_mod, "ocr_engine_cache"):
            router_mod.ocr_engine_cache = ocr_engine_cache
        if hasattr(router_mod, "task_queue"):
            router_mod.task_queue = task_queue
        if hasattr(router_mod, "manager"):
            router_mod.manager = manager
        if hasattr(router_mod, "ocr_cache"):
            router_mod.ocr_cache = ocr_cache
        if hasattr(router_mod, "UPLOAD_DIR"):
            router_mod.UPLOAD_DIR = UPLOAD_DIR
        if hasattr(router_mod, "OUTPUT_DIR"):
            router_mod.OUTPUT_DIR = OUTPUT_DIR

    # Extra injections for ocr router
    ocr.parallel_processor = parallel_processor
    ocr.plugin_loader = plugin_loader

    # Extra injections for system router
    system.app_start_time = app_start_time
    system.plugin_loader = plugin_loader

    # Start background cleanup
    asyncio.create_task(cleanup_old_tasks_loop())
    logger.info("API Server components initialized")


# Include Routers
app.include_router(ocr.router)
app.include_router(tasks_router.router)
app.include_router(system.router)
app.include_router(files.router)

# Static Files
if NEXT_OUT_DIR.exists():
    app.mount(
        "/_next", StaticFiles(directory=str(NEXT_OUT_DIR / "_next")), name="next_static"
    )
    app.mount("/static", StaticFiles(directory=str(NEXT_OUT_DIR)), name="nextjs_root")


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    if NEXT_OUT_DIR.exists():
        index_file = NEXT_OUT_DIR / "index.html"
        if index_file.exists():
            return index_file.read_text(encoding="utf-8")
    return "<h1>PaddleOCR Toolkit API</h1><p>Frontend not found. Use /docs for API.</p>"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
