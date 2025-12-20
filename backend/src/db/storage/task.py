"""
Task Storage - CRUD operations for task management.

Provides:
- Create, read, update, delete operations for tasks
- Status and progress updates
- Filtering and pagination
- Cancel and retry functionality
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.db.storage.base import BaseStorage
from src.db.models.task import TaskModel, TaskStatus, TaskType

logger = logging.getLogger(__name__)


class TaskStorage(BaseStorage):
    """
    Storage layer for task management.

    Handles all database operations for the tasks table.
    """

    def create_task(
        self,
        task_type: str,
        config: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new task in pending status.

        Args:
            task_type: Type of task (backtest, portfolio, walkforward, deep_analysis)
            config: Task configuration dictionary
            user_id: Optional user identifier
            name: Optional task name for display

        Returns:
            Dictionary with task details
        """
        task_id = str(uuid.uuid4())

        with self.session_scope() as db:
            task = TaskModel(
                task_id=task_id,
                task_type=task_type,
                status=TaskStatus.PENDING.value,
                progress=0,
                config=config,
                user_id=user_id,
                name=name or f"{task_type} task",
                logs=[],
                retry_count=0,
            )
            db.add(task)
            # Commit happens automatically via session_scope

            logger.info(f"Created task {task_id} of type {task_type}")
            return self._task_to_dict(task)

    def get_by_id(
        self,
        task_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get task by ID.

        Args:
            task_id: Task identifier
            user_id: Optional user filter

        Returns:
            Task dictionary or None if not found
        """
        with self.session_scope() as db:
            query = db.query(TaskModel).filter(TaskModel.task_id == task_id)
            if user_id:
                query = query.filter(TaskModel.user_id == user_id)

            task = query.first()
            return self._task_to_dict(task) if task else None

    def list_tasks(
        self,
        user_id: Optional[str] = None,
        task_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> List[Dict[str, Any]]:
        """
        List tasks with optional filtering.

        Args:
            user_id: Filter by user
            task_type: Filter by task type
            status: Filter by status
            limit: Maximum results
            offset: Pagination offset
            sort_by: Sort field
            sort_order: 'asc' or 'desc'

        Returns:
            List of task dictionaries
        """
        with self.session_scope() as db:
            query = db.query(TaskModel)

            # Apply filters
            if user_id:
                query = query.filter(TaskModel.user_id == user_id)
            if task_type:
                query = query.filter(TaskModel.task_type == task_type)
            if status:
                query = query.filter(TaskModel.status == status)

            # Apply sorting
            sort_column = getattr(TaskModel, sort_by, TaskModel.created_at)
            if sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))

            # Apply pagination
            query = query.offset(offset).limit(limit)

            tasks = query.all()
            return [self._task_to_dict(t) for t in tasks]

    def count_tasks(
        self,
        user_id: Optional[str] = None,
        task_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """Count tasks matching filters."""
        with self.session_scope() as db:
            query = db.query(TaskModel)

            if user_id:
                query = query.filter(TaskModel.user_id == user_id)
            if task_type:
                query = query.filter(TaskModel.task_type == task_type)
            if status:
                query = query.filter(TaskModel.status == status)

            return query.count()

    def update_status(
        self,
        task_id: str,
        status: str,
        progress: Optional[int] = None,
        error_message: Optional[str] = None,
        result_id: Optional[str] = None,
        result_type: Optional[str] = None,
    ) -> bool:
        """
        Update task status and progress.

        Args:
            task_id: Task identifier
            status: New status value
            progress: Optional progress percentage (0-100)
            error_message: Optional error message for failed status
            result_id: Optional link to result record
            result_type: Optional result table name

        Returns:
            True if task was updated, False if not found
        """
        with self.session_scope() as db:
            task = db.query(TaskModel).filter(TaskModel.task_id == task_id).first()
            if not task:
                return False

            old_status = task.status
            task.status = status

            if progress is not None:
                task.progress = min(100, max(0, progress))

            if error_message is not None:
                task.error_message = error_message

            if result_id is not None:
                task.result_id = result_id

            if result_type is not None:
                task.result_type = result_type

            # Set started_at when transitioning to running
            if status == TaskStatus.RUNNING.value and old_status == TaskStatus.PENDING.value:
                task.started_at = datetime.now(timezone.utc)

            # Set completed_at and duration when task ends
            if status in (TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value):
                task.completed_at = datetime.now(timezone.utc)
                if task.started_at:
                    # Ensure started_at is timezone-aware for duration calculation
                    started = task.started_at
                    if started.tzinfo is None:
                        started = started.replace(tzinfo=timezone.utc)
                    task.duration_seconds = (task.completed_at - started).total_seconds()

            logger.info(f"Updated task {task_id} status: {old_status} -> {status}")
            return True

    def add_log(self, task_id: str, level: str, message: str) -> bool:
        """
        Add a log entry to the task.

        Args:
            task_id: Task identifier
            level: Log level (info, warning, error)
            message: Log message

        Returns:
            True if log was added, False if task not found
        """
        with self.session_scope() as db:
            task = db.query(TaskModel).filter(TaskModel.task_id == task_id).first()
            if not task:
                return False

            logs = task.logs or []
            logs.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": level,
                "message": message,
            })
            task.logs = logs

            return True

    def cancel_task(self, task_id: str, user_id: Optional[str] = None) -> bool:
        """
        Cancel a pending or running task.

        Args:
            task_id: Task identifier
            user_id: Optional user filter for authorization

        Returns:
            True if task was cancelled, False otherwise
        """
        with self.session_scope() as db:
            query = db.query(TaskModel).filter(TaskModel.task_id == task_id)
            if user_id:
                query = query.filter(TaskModel.user_id == user_id)

            task = query.first()
            if not task:
                return False

            # Can only cancel pending or running tasks
            if task.status not in (TaskStatus.PENDING.value, TaskStatus.RUNNING.value):
                logger.warning(f"Cannot cancel task {task_id} with status {task.status}")
                return False

            task.status = TaskStatus.CANCELLED.value
            task.completed_at = datetime.now(timezone.utc)
            if task.started_at:
                task.duration_seconds = (task.completed_at - task.started_at).total_seconds()

            logger.info(f"Cancelled task {task_id}")
            return True

    def retry_task(self, task_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retry a failed or cancelled task by creating a new task with same config.

        Args:
            task_id: Task identifier to retry
            user_id: Optional user filter

        Returns:
            New task dictionary or None if original not found/not retryable
        """
        with self.session_scope() as db:
            query = db.query(TaskModel).filter(TaskModel.task_id == task_id)
            if user_id:
                query = query.filter(TaskModel.user_id == user_id)

            original = query.first()
            if not original:
                return None

            # Can only retry failed or cancelled tasks
            if original.status not in (TaskStatus.FAILED.value, TaskStatus.CANCELLED.value):
                logger.warning(f"Cannot retry task {task_id} with status {original.status}")
                return None

            # Create new task with same config
            new_task_id = str(uuid.uuid4())
            new_task = TaskModel(
                task_id=new_task_id,
                task_type=original.task_type,
                status=TaskStatus.PENDING.value,
                progress=0,
                config=original.config,
                user_id=original.user_id,
                name=original.name,
                logs=[],
                retry_count=original.retry_count + 1,
            )
            db.add(new_task)

            logger.info(f"Retried task {task_id} as new task {new_task_id}")
            return self._task_to_dict(new_task)

    def delete_by_id(self, task_id: str, user_id: Optional[str] = None, force: bool = False) -> bool:
        """
        Delete a task record.

        Args:
            task_id: Task identifier
            user_id: Optional user filter
            force: If True, force delete even running tasks (for stuck/stale tasks)

        Returns:
            True if deleted, False if not found
        """
        with self.session_scope() as db:
            query = db.query(TaskModel).filter(TaskModel.task_id == task_id)
            if user_id:
                query = query.filter(TaskModel.user_id == user_id)

            task = query.first()
            if not task:
                return False

            # Don't delete running tasks unless force is True
            if task.status == TaskStatus.RUNNING.value and not force:
                logger.warning(f"Cannot delete running task {task_id}")
                return False

            db.delete(task)
            logger.info(f"Deleted task {task_id}" + (" (forced)" if force else ""))
            return True

    def get_running_count(self, user_id: Optional[str] = None) -> int:
        """Get count of currently running tasks."""
        return self.count_tasks(user_id=user_id, status=TaskStatus.RUNNING.value)

    def get_pending_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pending tasks ordered by creation time."""
        return self.list_tasks(
            status=TaskStatus.PENDING.value,
            limit=limit,
            sort_by="created_at",
            sort_order="asc",
        )

    def _task_to_dict(self, task: TaskModel) -> Dict[str, Any]:
        """Convert TaskModel to dictionary."""
        return {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "status": task.status,
            "progress": task.progress,
            "name": task.name,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "duration_seconds": task.duration_seconds,
            "error_message": task.error_message,
            "result_id": task.result_id,
            "result_type": task.result_type,
            "user_id": task.user_id,
            "config": task.config,
            "logs": task.logs,
            "retry_count": task.retry_count,
        }


# Module-level singleton
_task_storage: Optional[TaskStorage] = None


def get_task_storage() -> TaskStorage:
    """Get or create TaskStorage singleton."""
    global _task_storage
    if _task_storage is None:
        _task_storage = TaskStorage()
    return _task_storage


__all__ = ["TaskStorage", "get_task_storage"]
