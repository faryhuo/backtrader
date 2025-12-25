"""
Task Contracts - Shared task type and status enums.

This module provides low-level types that can be safely imported anywhere
without causing circular dependencies. These are pure Python enums with
no dependencies on service, routes, or database layers.
"""

from enum import Enum


class TaskType(str, Enum):
    """Supported task types."""
    BACKTEST = "backtest"
    PORTFOLIO = "portfolio"
    WALKFORWARD = "walkforward"
    DEEP_ANALYSIS = "deep_analysis"


class TaskStatus(str, Enum):
    """Task status values."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


__all__ = ["TaskType", "TaskStatus"]
