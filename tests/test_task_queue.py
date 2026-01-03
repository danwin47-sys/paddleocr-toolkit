# -*- coding: utf-8 -*-
"""
Task Queue Tests
"""
import asyncio
import pytest
from datetime import datetime
from paddleocr_toolkit.core.task_queue import TaskQueue, TaskPriority, QueuedTask


@pytest.mark.asyncio
class TestTaskQueue:
    async def test_queued_task_priority_inversion(self):
        """Test that priority is negated in QueuedTask for descending order in PriorityQueue"""
        task = QueuedTask(priority=1, task_id="t1", func=lambda: None)
        assert task.priority == -1

        task_high = QueuedTask(
            priority=TaskPriority.HIGH.value, task_id="high", func=lambda: None
        )
        assert task_high.priority == -2

    async def test_add_task_and_get_status(self):
        """Test adding tasks and checking queue status"""
        tq = TaskQueue(max_workers=2)

        async def mock_func():
            pass

        await tq.add_task("task1", mock_func, TaskPriority.NORMAL)
        await tq.add_task("task2", mock_func, TaskPriority.HIGH)

        status = tq.get_status()
        assert status["queue_size"] == 2
        assert status["max_workers"] == 2
        assert status["active_tasks"] == 0

    async def test_worker_processing_success(self):
        """Test that workers process tasks from the queue"""
        tq = TaskQueue(max_workers=1)

        # Track execution
        executed = []

        async def mock_func():
            executed.append(True)

        await tq.add_task("task_exec", mock_func)

        # Start workers
        await tq.start()

        # Wait for queue to empty
        await asyncio.wait_for(tq.queue.join(), timeout=2.0)

        assert len(executed) == 1
        assert tq.total_processed == 1
        assert tq.get_status()["active_tasks"] == 0

        await tq.stop()

    async def test_worker_processing_failure(self):
        """Test that workers handle task failures gracefully"""
        tq = TaskQueue(max_workers=1)

        async def fail_func():
            raise ValueError("Task Failed")

        await tq.add_task("task_fail", fail_func)
        await tq.start()

        await asyncio.wait_for(tq.queue.join(), timeout=2.0)

        assert tq.total_failed == 1
        assert tq.total_processed == 0

        await tq.stop()

    async def test_priority_execution_order(self):
        """Test that higher priority tasks are processed first"""
        # We need a queue with many tasks and workers stopped or slow to observe order
        tq = TaskQueue(max_workers=0)  # No workers yet

        results = []

        def make_func(val):
            async def f():
                results.append(val)

            return f

        # Add Low, then High, then Normal
        await tq.add_task("low", make_func("low"), TaskPriority.LOW)
        await tq.add_task("high", make_func("high"), TaskPriority.HIGH)
        await tq.add_task("normal", make_func("normal"), TaskPriority.NORMAL)

        # Start 1 worker to process sequentially
        tq.max_workers = 1
        await tq.start()

        await asyncio.wait_for(tq.queue.join(), timeout=2.0)

        # Expected order: high (-2), normal (-1), low (0)
        assert results == ["high", "normal", "low"]

        await tq.stop()
