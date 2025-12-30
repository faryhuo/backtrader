"""
Portfolio module - Centralized components for multi-asset portfolio backtesting.

This module provides:
- TradeRecorder: Unified trade recording service
- BacktestConfig: Configuration validation
- CerebroBuilder: Fluent builder for Backtrader Cerebro
- ResultExtractor: Structured result extraction
- ChartGenerator: Chart generation from Cerebro
- EventBus: Event-based communication between components
- ResultAggregator: Clean interface for result aggregation
"""

from .trade_recorder import TradeRecorder, TradeRecord, TradeTrigger
from .backtest_config import (
    BacktestConfig,
    MAX_TICKERS,
    SUPPORTED_TIMEFRAMES,
)
from .cerebro_builder import CerebroBuilder
from .result_extractor import ResultExtractor
from .chart_generator import ChartGenerator
from .events import (
    PortfolioEventType,
    PortfolioEvent,
    InitialPositionsEvent,
    TradeExecutedEvent,
    PortfolioValueEvent,
    PortfolioEventBus,
)
from .result_aggregator import PortfolioResultAggregator

__all__ = [
    # Trade recording
    "TradeRecorder",
    "TradeRecord",
    "TradeTrigger",
    # Configuration
    "BacktestConfig",
    "MAX_TICKERS",
    "SUPPORTED_TIMEFRAMES",
    # Building and extraction
    "CerebroBuilder",
    "ResultExtractor",
    "ChartGenerator",
    # Events
    "PortfolioEventType",
    "PortfolioEvent",
    "InitialPositionsEvent",
    "TradeExecutedEvent",
    "PortfolioValueEvent",
    "PortfolioEventBus",
    # Result aggregation
    "PortfolioResultAggregator",
]
