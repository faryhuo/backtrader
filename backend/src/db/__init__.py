"""
Database Package - Re-exports all models and storage classes.

Import database components from this package:
    from src.db import BacktestStorage, TradingSessionModel, ...
"""

# Storage classes (from storage subpackage)
from src.db.storage import (
    BaseStorage,
    BacktestStorage,
    SessionStorage,
    SettingsStorage,
    WalkForwardStorage,
    PortfolioStorage,
    get_portfolio_storage,
    StrategyVersionStorage,
    # Market data
    DataLoadError,
    save_to_db,
    get_data_from_db,
    get_data,
    get_bt_feed,
    get_raw_data_json,
    # Ticker metadata
    get_ticker_metadata,
)

# All models (from models package for backward compatibility)
from src.db.models import (
    # Base utilities
    Base,
    SafeJSON,
    SessionStatusEnum,
    OrderStatusEnum,
    init_database,
    # Trading models
    TradingSessionModel,
    OrderModel,
    PositionModel,
    # Backtest models
    BacktestHistoryModel,
    PortfolioResultModel,
    WalkForwardOptimizationModel,
    # Market models
    MarketDataModel,
    TickerMetadataModel,
    # User models
    UserSettingsModel,
    StrategyVersionModel,
)


__all__ = [
    # Base
    "BaseStorage",
    "Base",
    "SafeJSON",
    "init_database",
    # Enums
    "SessionStatusEnum",
    "OrderStatusEnum",
    # Trading models
    "TradingSessionModel",
    "OrderModel",
    "PositionModel",
    # Backtest models
    "BacktestHistoryModel",
    "PortfolioResultModel",
    "WalkForwardOptimizationModel",
    # Market models
    "MarketDataModel",
    "TickerMetadataModel",
    # User models
    "UserSettingsModel",
    "StrategyVersionModel",
    # Storage classes
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
