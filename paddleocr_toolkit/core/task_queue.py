#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任務佇列系統
用於限制並發 OCR 任務數量，防止資源競爭
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """任務優先級"""

    LOW = 0
    NORMAL = 1
    HIGH = 2


@dataclass(order=True)
class QueuedTask:
    """佇列中的任務"""

    priority: int = field(compare=True)
    task_id: str = field(compare=False)
    func: Callable = field(compare=False)
    created_at: datetime = field(default_factory=datetime.now, compare=False)

    def __post_init__(self):
        # 反轉優先級以便高優先級先執行
        self.priority = -self.priority


class TaskQueue:
    """
    任務佇列管理器

    限制同時執行的任務數量，支援優先級佇列
    """

    def __init__(self, max_workers: int = 2):
        """
        初始化任務佇列

        Args:
            max_workers: 最大並發工作者數量
        """
        self.max_workers = max_workers
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.active_tasks: set = set()
        self.workers: list = []
        self.total_processed: int = 0
        self.total_failed: int = 0

        logger.info(f"TaskQueue initialized with {max_workers} workers")

    async def add_task(
        self, task_id: str, func: Callable, priority: TaskPriority = TaskPriority.NORMAL
    ) -> None:
        """
        添加任務到佇列

        Args:
            task_id: 任務唯一識別碼
            func: 要執行的異步函式
            priority: 任務優先級
        """
        task = QueuedTask(priority=priority.value, task_id=task_id, func=func)

        await self.queue.put(task)
        queue_size = self.queue.qsize()
        logger.info(
            f"Task {task_id} added to queue (priority={priority.name}, queue_size={queue_size})"
        )

    async def worker(self, worker_id: int):
        """
        工作協程

        Args:
            worker_id: 工作者識別碼
        """
        logger.info(f"Worker {worker_id} started")

        while True:
            task: QueuedTask = await self.queue.get()
            self.active_tasks.add(task.task_id)

            wait_time = (datetime.now() - task.created_at).total_seconds()
            logger.info(
                f"Worker {worker_id} processing task {task.task_id} "
                f"(waited {wait_time:.2f}s)"
            )

            try:
                await task.func()
                self.total_processed += 1
                logger.info(f"Task {task.task_id} completed successfully")
            except Exception as e:
                self.total_failed += 1
                logger.error(f"Task {task.task_id} failed: {e}", exc_info=True)
            finally:
                self.active_tasks.discard(task.task_id)
                self.queue.task_done()

    async def start(self):
        """啟動工作協程池"""
        self.workers = [
            asyncio.create_task(self.worker(i)) for i in range(self.max_workers)
        ]
        logger.info(f"Started {self.max_workers} worker tasks")

    async def stop(self):
        """停止所有工作協程"""
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("All workers stopped")

    def get_status(self) -> dict:
        """
        獲取佇列狀態

        Returns:
            佇列狀態資訊
        """
        return {
            "queue_size": self.queue.qsize(),
            "active_tasks": len(self.active_tasks),
            "max_workers": self.max_workers,
            "total_processed": self.total_processed,
            "total_failed": self.total_failed,
        }
