# -*- coding: utf-8 -*-
"""
System Router - Health, Metrics, and Queue Status Endpoints
"""
from datetime import datetime
from typing import Dict, Any

import psutil
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from paddleocr_toolkit.utils.logger import logger

router = APIRouter(tags=["system"])

# These will be injected from main.py
app_start_time: datetime = None
ocr_engine_cache = None
task_queue = None
results: Dict[str, Any] = {}
manager = None  # WebSocket manager
plugin_loader = None


@router.get("/api/plugins")
async def list_plugins():
    """
    List all loaded plugins

    Returns:
        list: List of plugin information
    """
    if not plugin_loader:
        return []

    plugins = []
    for name, plugin in plugin_loader.get_all_plugins().items():
        plugins.append(
            {
                "name": name,
                "version": getattr(plugin, "version", "unknown"),
                "description": getattr(plugin, "description", ""),
                "enabled": True,
            }
        )
    return plugins


@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """
    WebSocket endpoint for real-time log streaming
    """
    if manager is None:
        await websocket.accept()
        await websocket.send_json({"error": "WebSocket manager not initialized"})
        await websocket.close()
        return

    await manager.connect(websocket, "logs")
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, "logs")
    except Exception as e:
        logger.error(f"WebSocket Error (Logs): {e}")
        manager.disconnect(websocket, "logs")


@router.get("/health")
@router.get("/api/health")
async def health_check():
    """
    System health check endpoint

    Returns:
        dict: System health status information
    """
    uptime_seconds = (datetime.now() - app_start_time).total_seconds()

    return {
        "status": "healthy",
        "version": "3.3.0",
        "uptime_seconds": round(uptime_seconds, 2),
        "components": {
            "ocr_engine": "ready" if ocr_engine_cache else "not_loaded",
            "websocket": "active",
            "file_system": "ok",
            "task_queue": "active" if task_queue else "not_initialized",
        },
        "stats": {
            "total_tasks": len(results),
            "active_ws_connections": len(manager.active_connections) if manager else 0,
            "log_ws_connections": len(manager.log_connections) if manager else 0,
        },
    }


@router.get("/api/metrics")
async def get_metrics():
    """
    System performance metrics

    Returns:
        dict: CPU, memory, disk usage information
    """
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=0.5)

    # Memory information
    memory = psutil.virtual_memory()

    # Disk information
    disk = psutil.disk_usage(".")

    # Current process information
    current_process = psutil.Process()
    process_memory = current_process.memory_info()

    return {
        "cpu": {
            "percent": round(cpu_percent, 2),
            "count": psutil.cpu_count(),
            "count_logical": psutil.cpu_count(logical=True),
        },
        "memory": {
            "total_mb": round(memory.total / 1024 / 1024, 2),
            "available_mb": round(memory.available / 1024 / 1024, 2),
            "used_mb": round(memory.used / 1024 / 1024, 2),
            "percent": round(memory.percent, 2),
            "process_mb": round(process_memory.rss / 1024 / 1024, 2),
        },
        "disk": {
            "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
            "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
            "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
            "percent": round(disk.percent, 2),
        },
        "tasks": {
            "total": len(results),
            "completed": len(
                [r for r in results.values() if r.get("status") == "completed"]
            ),
            "processing": len(
                [r for r in results.values() if r.get("status") == "processing"]
            ),
            "error": len([r for r in results.values() if r.get("status") == "error"]),
        },
    }


@router.get("/api/queue/status")
async def get_queue_status():
    """
    Task queue status

    Returns:
        dict: Queue status information
    """
    if not task_queue:
        return {
            "error": "Task queue not initialized",
            "queue_size": 0,
            "active_tasks": 0,
        }

    status = task_queue.get_status()
    return status
