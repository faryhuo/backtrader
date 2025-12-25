"""
Contracts Module - Shared types and constants for cross-layer communication.

This module provides low-level types that can be safely imported anywhere
without causing circular dependencies. It contains:
- Task types and status enums
- Common exception classes
- Protocol definitions (for type hints without runtime dependencies)

IMPORTANT: This module must NOT import from service, routes, or storage layers.
"""

from src.contracts.task import TaskType, TaskStatus
from src.contracts.exceptions import StrategyLoadError, DataLoadError

__all__ = [
    "TaskType",
    "TaskStatus",
    "StrategyLoadError",
    "DataLoadError",
]
