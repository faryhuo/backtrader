"""
Task Manager - Unified background task execution with concurrency control.

This module provides:
- Task queue management
- Concurrency control (max parallel tasks)
- Task lifecycle management (submit, cancel, retry)
- WebSocket broadcast for real-time updates
- Integration with backtest, portfolio, walkforward, deep_analysis engines
"""

import asyncio
import logging
import os
from typing import Any, Callable, Dict, Optional

from src.db.storage.task import TaskStorage, get_task_storage
from src.db.models.task import TaskStatus, TaskType

logger = logging.getLogger(__name__)

# Environment variable for max concurrent tasks
MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", "3"))


class TaskManager:
    """
    Manages background task execution with concurrency control.

    Features:
    - Semaphore-based concurrency limiting
    - WebSocket event broadcasting
    - Graceful task cancellation
    - Error handling with automatic status updates
    """

    def __init__(
        self,
        max_concurrent: int = MAX_CONCURRENT_TASKS,
        storage: Optional[TaskStorage] = None,
    ):
        """
        Initialize TaskManager.

        Args:
            max_concurrent: Maximum number of concurrent tasks
            storage: Optional TaskStorage instance (uses singleton if not provided)
        """
        self.max_concurrent = max_concurrent
        self.storage = storage or get_task_storage()
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._ws_manager = None  # Lazy loaded to avoid circular imports
        logger.info(f"TaskManager initialized with max_concurrent={max_concurrent}")

    def _get_ws_manager(self):
        """Lazy load WebSocket manager to avoid circular imports."""
        if self._ws_manager is None:
            try:
                from src.service.websocket_manager import get_websocket_manager
                self._ws_manager = get_websocket_manager()
            except Exception as e:
                logger.warning(f"Could not load WebSocket manager: {e}")
        return self._ws_manager

    async def submit(
        self,
        task_type: str,
        executor: Callable,
        config: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Submit a new task for execution.

        Args:
            task_type: Type of task (backtest, portfolio, walkforward, deep_analysis)
            executor: Async callable that performs the actual work
            config: Task configuration (passed to executor)
            user_id: Optional user identifier
            name: Optional task name for display

        Returns:
            Task dictionary with task_id
        """
        # Create task record
        task = self.storage.create_task(
            task_type=task_type,
            config=config,
            user_id=user_id,
            name=name,
        )
        task_id = task["task_id"]

        # Schedule execution
        asyncio_task = asyncio.create_task(
            self._execute_with_semaphore(task_id, executor, config)
        )
        self._running_tasks[task_id] = asyncio_task

        logger.info(f"Submitted task {task_id} of type {task_type}")
        await self._broadcast_task_event(task_id, "created", task)
        return task

    async def _execute_with_semaphore(
        self,
        task_id: str,
        executor: Callable,
        config: Optional[Dict[str, Any]],
    ):
        """Execute task with semaphore for concurrency control."""
        async with self._semaphore:
            await self._execute_task(task_id, executor, config)

    async def _execute_task(
        self,
        task_id: str,
        executor: Callable,
        config: Optional[Dict[str, Any]],
    ):
        """
        Execute a task and handle status updates.

        Args:
            task_id: Task identifier
            executor: Callable that performs the actual work
            config: Configuration passed to executor
        """
        try:
            # Update status to running
            self.storage.update_status(task_id, TaskStatus.RUNNING.value, progress=0)
            self.storage.add_log(task_id, "info", "Task started")
            await self._broadcast_task_event(task_id, "started", {
                "task_id": task_id,
                "status": TaskStatus.RUNNING.value,
                "progress": 0,
            })

            # Create progress callback for executor
            async def progress_callback(progress: int, message: Optional[str] = None):
                self.storage.update_status(task_id, TaskStatus.RUNNING.value, progress=progress)
                if message:
                    self.storage.add_log(task_id, "info", message)
                await self._broadcast_task_event(task_id, "progress", {
                    "task_id": task_id,
                    "progress": progress,
                    "message": message,
                })

            # Execute the task
            if asyncio.iscoroutinefunction(executor):
                result = await executor(config, progress_callback)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: executor(config, lambda p, m=None: None)  # Sync callback
                )

            # Update status to completed
            result_id = result.get("id") if isinstance(result, dict) else None
            result_type = self._get_result_type(self.storage.get_by_id(task_id).get("task_type"))

            self.storage.update_status(
                task_id,
                TaskStatus.COMPLETED.value,
                progress=100,
                result_id=result_id,
                result_type=result_type,
            )
            self.storage.add_log(task_id, "info", "Task completed successfully")

            await self._broadcast_task_event(task_id, "completed", {
                "task_id": task_id,
                "status": TaskStatus.COMPLETED.value,
                "progress": 100,
                "result_id": result_id,
            })

            logger.info(f"Task {task_id} completed successfully")

        except asyncio.CancelledError:
            # Task was cancelled
            self.storage.update_status(task_id, TaskStatus.CANCELLED.value)
            self.storage.add_log(task_id, "warning", "Task was cancelled")
            await self._broadcast_task_event(task_id, "cancelled", {
                "task_id": task_id,
                "status": TaskStatus.CANCELLED.value,
            })
            logger.info(f"Task {task_id} was cancelled")
            raise  # Re-raise to propagate cancellation

        except Exception as e:
            # Task failed
            error_message = str(e)
            self.storage.update_status(
                task_id,
                TaskStatus.FAILED.value,
                error_message=error_message,
            )
            self.storage.add_log(task_id, "error", f"Task failed: {error_message}")
            await self._broadcast_task_event(task_id, "failed", {
                "task_id": task_id,
                "status": TaskStatus.FAILED.value,
                "error": error_message,
            })
            logger.exception(f"Task {task_id} failed: {e}")

        finally:
            # Remove from running tasks
            self._running_tasks.pop(task_id, None)

    def _get_result_type(self, task_type: Optional[str]) -> Optional[str]:
        """Map task type to result table name."""
        mapping = {
            TaskType.BACKTEST.value: "backtest_history",
            TaskType.PORTFOLIO.value: "portfolio_results",
            TaskType.WALKFORWARD.value: "walkforward_optimizations",
            TaskType.DEEP_ANALYSIS.value: "backtest_history",  # Deep analysis updates backtest
        }
        return mapping.get(task_type)

    async def cancel(self, task_id: str, user_id: Optional[str] = None) -> bool:
        """
        Cancel a running or pending task.

        Args:
            task_id: Task identifier
            user_id: Optional user for authorization

        Returns:
            True if task was cancelled, False otherwise
        """
        # Check if task is running
        if task_id in self._running_tasks:
            asyncio_task = self._running_tasks[task_id]
            asyncio_task.cancel()
            logger.info(f"Cancelled running task {task_id}")
            return True

        # Otherwise, try to cancel in storage (for pending tasks)
        cancelled = self.storage.cancel_task(task_id, user_id)
        if cancelled:
            await self._broadcast_task_event(task_id, "cancelled", {
                "task_id": task_id,
                "status": TaskStatus.CANCELLED.value,
            })
        return cancelled

    async def retry(
        self,
        task_id: str,
        executor: Callable,
        user_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retry a failed or cancelled task.

        Args:
            task_id: Original task identifier
            executor: Callable to execute the task
            user_id: Optional user for authorization

        Returns:
            New task dictionary or None if retry failed
        """
        # Get original task
        original = self.storage.get_by_id(task_id, user_id)
        if not original:
            return None

        if original["status"] not in (TaskStatus.FAILED.value, TaskStatus.CANCELLED.value):
            logger.warning(f"Cannot retry task {task_id} with status {original['status']}")
            return None

        # Create new task via storage
        new_task = self.storage.retry_task(task_id, user_id)
        if not new_task:
            return None

        new_task_id = new_task["task_id"]

        # Schedule execution
        asyncio_task = asyncio.create_task(
            self._execute_with_semaphore(new_task_id, executor, original["config"])
        )
        self._running_tasks[new_task_id] = asyncio_task

        logger.info(f"Retried task {task_id} as {new_task_id}")
        await self._broadcast_task_event(new_task_id, "created", new_task)
        return new_task

    def get_task(self, task_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get task by ID."""
        return self.storage.get_by_id(task_id, user_id)

    def list_tasks(
        self,
        user_id: Optional[str] = None,
        task_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        List tasks with filtering and pagination.

        Returns:
            Dictionary with tasks list and total count
        """
        tasks = self.storage.list_tasks(
            user_id=user_id,
            task_type=task_type,
            status=status,
            limit=limit,
            offset=offset,
        )
        total = self.storage.count_tasks(
            user_id=user_id,
            task_type=task_type,
            status=status,
        )
        return {"tasks": tasks, "total": total}

    def delete_task(self, task_id: str, user_id: Optional[str] = None, force: bool = False) -> bool:
        """Delete a task record."""
        return self.storage.delete_by_id(task_id, user_id, force=force)

    def get_running_count(self) -> int:
        """Get count of currently running tasks."""
        return len(self._running_tasks)

    def get_stats(self) -> Dict[str, Any]:
        """Get task manager statistics."""
        return {
            "max_concurrent": self.max_concurrent,
            "running_count": self.get_running_count(),
            "semaphore_available": self._semaphore._value,
            "pending_count": self.storage.count_tasks(status=TaskStatus.PENDING.value),
            "completed_today": 0,  # Date filtering not yet implemented
        }

    async def _broadcast_task_event(
        self,
        task_id: str,
        event_type: str,
        data: Dict[str, Any],
    ):
        """Broadcast task event via WebSocket."""
        ws_manager = self._get_ws_manager()
        if ws_manager:
            try:
                message = {
                    "type": f"task_{event_type}",
                    "task_id": task_id,
                    "data": data,
                }
                # Broadcast to all connected task subscribers
                # For now, we'll broadcast to a special "tasks" channel
                await ws_manager.broadcast("tasks", message)
            except Exception as e:
                logger.warning(f"Failed to broadcast task event: {e}")


# Module-level singleton
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """Get or create TaskManager singleton."""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager


__all__ = ["TaskManager", "get_task_manager", "MAX_CONCURRENT_TASKS"]
