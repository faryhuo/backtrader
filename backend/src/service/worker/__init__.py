"""
Worker Module - Secure process-based isolation for strategy execution.

This module provides infrastructure for running untrusted strategy code
in isolated worker processes with resource limits.
"""

from src.service.worker.task_models import (
    BacktestTask,
    BacktestResult,
    LiveTradingTask,
    LiveTradingEvent,
    TaskStatus,
)
from src.service.worker.worker_pool import (
    WorkerPool,
    get_worker_pool,
    shutdown_worker_pool,
)

__all__ = [
    "BacktestTask",
    "BacktestResult",
    "LiveTradingTask",
    "LiveTradingEvent",
    "TaskStatus",
    "WorkerPool",
    "get_worker_pool",
    "shutdown_worker_pool",
]
