"""
Contracts Module - Shared types and constants for cross-layer communication.

This module provides low-level types that can be safely imported anywhere
without causing circular dependencies. It contains:
- Task types and status enums
- Common exception classes
- Sizer configuration types
- Backtest default values
- Protocol definitions (for type hints without runtime dependencies)

IMPORTANT: This module must NOT import from service, routes, or storage layers.
"""

from src.contracts.task import TaskType, TaskStatus
from src.contracts.exceptions import StrategyLoadError, DataLoadError
from src.contracts.sizer_config import SizerType, SizerConfig, SIZER_TYPE_LABELS
from src.contracts.defaults import (
    BacktestDefaults,
    BACKTEST_DEFAULTS,
    TIMEFRAME_OPTIONS,
    SIZER_TYPE_OPTIONS,
    OPTIMIZATION_METRIC_OPTIONS,
)

__all__ = [
    "TaskType",
    "TaskStatus",
    "StrategyLoadError",
    "DataLoadError",
    "SizerType",
    "SizerConfig",
    "SIZER_TYPE_LABELS",
    "BacktestDefaults",
    "BACKTEST_DEFAULTS",
    "TIMEFRAME_OPTIONS",
    "SIZER_TYPE_OPTIONS",
    "OPTIMIZATION_METRIC_OPTIONS",
]
