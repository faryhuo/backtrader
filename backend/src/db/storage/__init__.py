"""
Storage Package - Re-exports all storage classes and data modules.

Import storage classes from this package:
    from src.db.storage import BacktestStorage, SessionStorage, ...
"""

from src.db.storage.base import BaseStorage
from src.db.storage.backtest import BacktestStorage
from src.db.storage.session import SessionStorage
from src.db.storage.settings import SettingsStorage
from src.db.storage.walkforward import WalkForwardStorage
from src.db.storage.portfolio import PortfolioStorage, get_portfolio_storage
from src.db.storage.strategy_version import StrategyVersionStorage
from src.db.storage.task import TaskStorage, get_task_storage

# Market data functions
from src.db.storage.market_data import (
    DataLoadError,
    save_to_db,
    get_data_from_db,
    get_data,
    get_bt_feed,
    get_raw_data_json,
)

# Ticker metadata functions
from src.db.storage.ticker_metadata import (
    get_ticker_metadata,
)

# Data cache management
from src.db.storage.data_cache import (
    DataCacheStorage,
    get_data_cache_storage,
)

# OHLCV resampling
from src.db.storage.resampler import (
    resample_ohlcv,
    resample_to_daily,
    resample_to_hourly,
    validate_resample_path,
    get_supported_timeframes,
    get_resample_targets,
)

__all__ = [
    # Storage classes
    "BaseStorage",
    "BacktestStorage",
    "SessionStorage",
    "SettingsStorage",
    "WalkForwardStorage",
    "PortfolioStorage",
    "get_portfolio_storage",
    "StrategyVersionStorage",
    "TaskStorage",
    "get_task_storage",
    # Market data
    "DataLoadError",
    "save_to_db",
    "get_data_from_db",
    "get_data",
    "get_bt_feed",
    "get_raw_data_json",
    # Ticker metadata
    "get_ticker_metadata",
    # Data cache management
    "DataCacheStorage",
    "get_data_cache_storage",
    # OHLCV resampling
    "resample_ohlcv",
    "resample_to_daily",
    "resample_to_hourly",
    "validate_resample_path",
    "get_supported_timeframes",
    "get_resample_targets",
]
