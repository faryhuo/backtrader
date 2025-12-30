"""
Centralized Default Configuration Values.

This module provides a single source of truth for all backtest-related
default values used across routes, task models, and frontend.

IMPORTANT: This module must NOT import from service, routes, or storage layers.
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class BacktestDefaults:
    """
    Centralized backtest default configuration values.
    
    These defaults are used by:
    - Route request models (backtest_routes, walkforward_routes, portfolio_routes)
    - Task models for worker IPC
    - Frontend form initialization (via /site/defaults endpoint)
    """
    # Core backtest parameters
    INITIAL_CASH: float = 100000.0
    COMMISSION: float = 0.0005
    STAKE: int = 100
    TIMEFRAME: str = "1d"
    
    # Position sizing
    SIZER_TYPE: str = "fixed_size"
    SIZER_PERCENT: float = 10.0
    SIZER_RISK_PERCENT: float = 2.0
    
    # Walk-forward optimization
    TRAIN_PERIOD_DAYS: int = 365
    TEST_PERIOD_DAYS: int = 90
    ANCHORED: bool = False
    OPTIMIZATION_METRIC: str = "sharpe_ratio"
    
    # Live trading (different defaults)
    LIVE_INITIAL_CASH: float = 10000.0
    LIVE_COMMISSION: float = 0.001


# Singleton instance for import
BACKTEST_DEFAULTS = BacktestDefaults()

# Valid options for user-selectable fields
TIMEFRAME_OPTIONS: List[str] = ["1d", "1h", "15m", "5m", "1m"]

SIZER_TYPE_OPTIONS: List[str] = [
    "fixed_size",
    "percent_sizer", 
    "all_in_sizer",
    "risk_sizer",
    "kelly_sizer",
]

OPTIMIZATION_METRIC_OPTIONS: List[str] = [
    "sharpe_ratio",
    "total_return",
    "profit_factor",
]


__all__ = [
    "BacktestDefaults",
    "BACKTEST_DEFAULTS",
    "TIMEFRAME_OPTIONS",
    "SIZER_TYPE_OPTIONS",
    "OPTIMIZATION_METRIC_OPTIONS",
]
