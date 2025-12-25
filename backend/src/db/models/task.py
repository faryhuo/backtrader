"""
Task Model - SQLAlchemy model for background task management.

This module defines the database table for tracking:
- Task status, progress, and timing
- Task type (backtest, portfolio, walkforward, deep_analysis)
- Links to result records
- Error messages and logs
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from src.db.models.base import Base, SafeJSON
from src.contracts.task import TaskType, TaskStatus


class TaskModel(Base):
    """
    Task Model - Tracks background task execution.

    Provides unified management for all async tasks including:
    - Backtests
    - Portfolio backtests
    - Walk-forward optimizations
    - Deep analysis computations
    """
    __tablename__ = "tasks"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Unique task identifier
    task_id = Column(String(36), unique=True, nullable=False, index=True)

    # Task type
    task_type = Column(String(50), nullable=False, index=True)

    # Task status
    status = Column(String(20), default=TaskStatus.PENDING.value, nullable=False, index=True)

    # Progress (0-100)
    progress = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Duration in seconds (computed when completed)
    duration_seconds = Column(Float, nullable=True)

    # Error message for failed tasks
    error_message = Column(Text, nullable=True)

    # Link to result record
    result_id = Column(String(36), nullable=True, index=True)
    result_type = Column(String(50), nullable=True)  # Table name: backtest_history, portfolio_results, etc.

    # User identification
    user_id = Column(String(255), nullable=True, index=True)

    # Task configuration snapshot (JSON)
    config = Column(SafeJSON, nullable=True)

    # Task name/description for display
    name = Column(String(255), nullable=True)

    # Execution logs (JSON array)
    logs = Column(SafeJSON, nullable=True)

    # Retry count
    retry_count = Column(Integer, default=0)

    def __repr__(self):
        return (
            f"<Task(id={self.task_id}, "
            f"type={self.task_type}, "
            f"status={self.status}, "
            f"progress={self.progress}%)>"
        )


__all__ = [
    "TaskModel",
    "TaskType",
    "TaskStatus",
]
