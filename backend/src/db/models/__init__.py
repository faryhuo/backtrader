"""
Database Models Package - Re-exports all models for backward compatibility.

Import all models from this package:
    from src.db.models import BacktestHistoryModel, TradingSessionModel, ...
"""

# Base utilities
from src.db.models.base import (
    Base,
    SafeJSON,
    SessionStatusEnum,
    OrderStatusEnum,
    init_database,
)

# Trading models
from src.db.models.trading import (
    TradingSessionModel,
    OrderModel,
    PositionModel,
)

# Backtest models
from src.db.models.backtest import (
    BacktestHistoryModel,
    PortfolioResultModel,
    WalkForwardOptimizationModel,
)

# Market models
from src.db.models.market import (
    MarketDataModel,
    TickerMetadataModel,
)

# User models
from src.db.models.user import (
    UserSettingsModel,
    StrategyVersionModel,
)


__all__ = [
    # Base utilities
    "Base",
    "SafeJSON",
    "SessionStatusEnum",
    "OrderStatusEnum",
    "init_database",
    # Trading
    "TradingSessionModel",
    "OrderModel",
    "PositionModel",
    # Backtest
    "BacktestHistoryModel",
    "PortfolioResultModel",
    "WalkForwardOptimizationModel",
    # Market
    "MarketDataModel",
    "TickerMetadataModel",
    # User
    "UserSettingsModel",
    "StrategyVersionModel",
]
