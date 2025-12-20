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
    # Market data
    "DataLoadError",
    "save_to_db",
    "get_data_from_db",
    "get_data",
    "get_bt_feed",
    "get_raw_data_json",
    # Ticker metadata
    "get_ticker_metadata",
]
