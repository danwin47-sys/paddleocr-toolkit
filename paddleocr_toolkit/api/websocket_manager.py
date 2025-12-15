#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket連線管理器
處理實時進度更新
"""

import asyncio
import json
from typing import Dict, Set

from fastapi import WebSocket


class ConnectionManager:
    """WebSocket連線管理器"""

    def __init__(self):
        # 儲存所有活動連線 {task_id: set of websockets}
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        """
        接受新的WebSocket連線

        Args:
            websocket: WebSocket連線
            task_id: 任務ID
        """
        await websocket.accept()

        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()

        self.active_connections[task_id].add(websocket)
        print(f"WebSocket連線建立: 任務 {task_id}")

    def disconnect(self, websocket: WebSocket, task_id: str):
        """
        移除WebSocket連線

        Args:
            websocket: WebSocket連線
            task_id: 任務ID
        """
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)

            # 如果該任務沒有連線了，移除字典項
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]

        print(f"WebSocket連線關閉: 任務 {task_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        發送訊息給特定連線

        Args:
            message: 訊息字典
            websocket: WebSocket連線
        """
        await websocket.send_json(message)

    async def broadcast_to_task(self, task_id: str, message: dict):
        """
        廣播訊息給特定任務的所有連線

        Args:
            task_id: 任務ID
            message: 訊息字典
        """
        if task_id not in self.active_connections:
            return

        # 建立要移除的連線列表
        disconnected = set()

        for connection in self.active_connections[task_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"發送失敗: {e}")
                disconnected.add(connection)

        # 移除斷開的連線
        for connection in disconnected:
            self.active_connections[task_id].discard(connection)

    async def send_progress_update(
        self, task_id: str, progress: float, status: str, message: str = ""
    ):
        """
        發送進度更新

        Args:
            task_id: 任務ID
            progress: 進度 (0-100)
            status: 狀態
            message: 訊息
        """
        update = {
            "type": "progress",
            "task_id": task_id,
            "progress": progress,
            "status": status,
            "message": message,
            "timestamp": time.time(),
        }

        await self.broadcast_to_task(task_id, update)

    async def send_completion(self, task_id: str, results: any):
        """
        發送完成訊息

        Args:
            task_id: 任務ID
            results: 結果
        """
        completion = {
            "type": "completion",
            "task_id": task_id,
            "status": "completed",
            "progress": 100,
            "results": results,
            "timestamp": time.time(),
        }

        await self.broadcast_to_task(task_id, completion)

    async def send_error(self, task_id: str, error: str):
        """
        發送錯誤訊息

        Args:
            task_id: 任務ID
            error: 錯誤訊息
        """
        error_msg = {
            "type": "error",
            "task_id": task_id,
            "status": "failed",
            "error": error,
            "timestamp": time.time(),
        }

        await self.broadcast_to_task(task_id, error_msg)

    def get_connection_count(self, task_id: str = None) -> int:
        """
        取得連線數量

        Args:
            task_id: 任務ID（可選）

        Returns:
            連線數量
        """
        if task_id:
            return len(self.active_connections.get(task_id, set()))
        else:
            return sum(len(conns) for conns in self.active_connections.values())


# 全域連線管理器實例
manager = ConnectionManager()


# 使用範例
if __name__ == "__main__":
    print("WebSocket連線管理器")
    print("支援:")
    print("  • 多任務並行")
    print("  • 實時進度推送")
    print("  • 自動重連處理")
