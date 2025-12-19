"""
Database Models - SQLAlchemy models for live trading persistence.

This module defines database tables for storing:
- Trading sessions
- Orders
- Positions
- Trade history
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, Integer, JSON, String, Text, TypeDecorator, UniqueConstraint, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json

Base = declarative_base()


class SafeJSON(TypeDecorator):
    """JSON type that handles NULL and empty strings gracefully."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None or value == '':
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None


class SessionStatusEnum(enum.Enum):
    """Session status enumeration."""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class OrderStatusEnum(enum.Enum):
    """Order status enumeration."""
    CREATED = "created"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"


class TradingSessionModel(Base):
    """
    Trading session database model.

    Stores information about live/paper trading sessions for
    persistence and recovery.
    """
    __tablename__ = "trading_sessions"

    # Primary key
    session_id = Column(String(36), primary_key=True, index=True)

    # User identification (optional, for multi-user deployments)
    user_id = Column(String(255), nullable=True, index=True)

    # Session configuration
    strategy_name = Column(String(255), nullable=False)
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(50), nullable=False, index=True)
    mode = Column(String(10), nullable=False)  # 'paper' or 'live'
    timeframe = Column(String(10), nullable=False)

    # Status tracking
    status = Column(Enum(SessionStatusEnum), nullable=False, index=True)

    # Timestamps
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Financial tracking
    initial_cash = Column(Float, nullable=False)
    current_cash = Column(Float, nullable=True)
    final_balance = Column(Float, nullable=True)
    total_pnl = Column(Float, default=0.0)
    commission = Column(Float, default=0.001)

    # Metrics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)

    # JSON fields for complex data
    positions = Column(SafeJSON, default=list)  # Current positions
    config = Column(SafeJSON, default=dict)  # Session configuration
    metrics = Column(SafeJSON, default=dict)  # Performance metrics

    # Error tracking
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return (
            f"<TradingSession(id={self.session_id}, "
            f"strategy={self.strategy_name}, "
            f"symbol={self.symbol}, "
            f"status={self.status.value if isinstance(self.status, SessionStatusEnum) else self.status})>"
        )


class OrderModel(Base):
    """
    Order database model.

    Tracks all orders submitted during trading sessions.
    """
    __tablename__ = "orders"

    # Primary key
    order_id = Column(String(100), primary_key=True, index=True)

    # Session reference
    session_id = Column(String(36), nullable=False, index=True)

    # Exchange order ID (from CCXT)
    exchange_order_id = Column(String(100), nullable=True, index=True)

    # Order details
    symbol = Column(String(50), nullable=False)
    side = Column(String(10), nullable=False)  # 'buy' or 'sell'
    type = Column(String(20), nullable=False)  # 'market', 'limit', etc.
    size = Column(Float, nullable=False)
    price = Column(Float, nullable=True)  # Limit price

    # Status tracking
    status = Column(Enum(OrderStatusEnum), nullable=False, index=True)
    filled_size = Column(Float, default=0.0)
    filled_price = Column(Float, nullable=True)  # Average fill price

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)
    filled_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Financial details
    commission = Column(Float, default=0.0)
    cost = Column(Float, nullable=True)  # Total cost (size * price)
    pnl = Column(Float, nullable=True)  # P&L for closing orders

    # Additional data
    metadata_json = Column("metadata", SafeJSON, default=dict)

    def __repr__(self):
        return (
            f"<Order(id={self.order_id}, "
            f"session={self.session_id}, "
            f"side={self.side}, "
            f"status={self.status.value if isinstance(self.status, OrderStatusEnum) else self.status})>"
        )


class PositionModel(Base):
    """
    Position database model.

    Tracks positions opened during trading sessions.
    """
    __tablename__ = "positions"

    # Primary key (composite)
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Session reference
    session_id = Column(String(36), nullable=False, index=True)

    # Position details
    symbol = Column(String(50), nullable=False, index=True)
    size = Column(Float, nullable=False)  # Positive for long, negative for short
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)

    # Timestamps
    opened_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

    # Financial tracking
    entry_cost = Column(Float, nullable=False)
    exit_cost = Column(Float, nullable=True)
    commission = Column(Float, default=0.0)
    pnl = Column(Float, nullable=True)
    pnl_percent = Column(Float, nullable=True)

    # Status
    is_open = Column(Integer, default=1, index=True)  # 1 for open, 0 for closed

    # Additional data
    metadata_json = Column("metadata", SafeJSON, default=dict)

    def __repr__(self):
        status = "OPEN" if self.is_open else "CLOSED"
        return (
            f"<Position(session={self.session_id}, "
            f"symbol={self.symbol}, "
            f"size={self.size}, "
            f"status={status})>"
        )


# Database initialization helper


def init_database(database_url: str, echo: bool = False):
    """
    Initialize database connection and create tables.

    Args:
        database_url: SQLAlchemy database URL
        echo: Whether to echo SQL statements (for debugging)

    Returns:
        tuple: (engine, SessionLocal)

    Example:
        engine, SessionLocal = init_database('sqlite:///trading.db')
        session = SessionLocal()
        # ... use session ...
        session.close()
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Create engine
    engine = create_engine(database_url, echo=echo)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    return engine, SessionLocal


class BacktestHistoryModel(Base):
    """
    Backtest History Model - Stores historical backtest results.

    Stores all backtest configurations, metrics, AI analysis, and plot references
    for historical tracking and comparison.
    """
    __tablename__ = "backtest_history"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Unique identifier for the backtest run
    backtest_id = Column(String(36), unique=True, nullable=False, index=True)

    # User identification (optional, for multi-user support)
    user_id = Column(String(255), nullable=True, index=True)

    # Configuration parameters
    ticker = Column(String(50), nullable=False, index=True)
    start_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    end_date = Column(String(10), nullable=False)    # YYYY-MM-DD
    initial_cash = Column(Float, nullable=False)
    commission = Column(Float, default=0.0005)
    stake = Column(Integer, default=100)
    strategy_name = Column(String(255), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Key performance metrics (denormalized for fast filtering/sorting)
    final_value = Column(Float, nullable=True)
    total_return = Column(Float, nullable=True, index=True)  # For sorting
    sharpe_ratio = Column(Float, nullable=True, index=True)  # For sorting
    max_drawdown = Column(Float, nullable=True)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)

    # Complete metrics JSON (all metrics from backtest engine)
    metrics = Column(SafeJSON, nullable=False)

    # AI Analysis - JSON format: {"model_name": "gpt-4o", "analysis_content": "..."}
    # Can store multiple analyses as a dict: {"gpt-4o": "...", "deepseek-v3.1": "..."}
    ai_analysis = Column(SafeJSON, nullable=True)

    # Strategy code snapshot (saved at backtest runtime)
    strategy_code = Column(Text, nullable=True)

    # Plot image reference
    plot_filename = Column(String(255), nullable=True)  # UUID.png

    # Strategy parameter overrides (JSON format)
    # e.g., {"fast_period": 10, "slow_period": 30}
    params = Column(SafeJSON, nullable=True)

    def __repr__(self):
        return (
            f"<BacktestHistory(id={self.backtest_id}, "
            f"ticker={self.ticker}, "
            f"strategy={self.strategy_name}, "
            f"return={self.total_return:.2f}% if self.total_return else 'N/A')>"
        )


class PortfolioResultModel(Base):
    """
    Portfolio Result Model - Stores multi-asset portfolio backtest results.

    Stores portfolio configuration, combined metrics, individual asset metrics,
    correlation analysis, and Markowitz optimization suggestions.
    """
    __tablename__ = "portfolio_results"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Unique identifier for the portfolio backtest run
    portfolio_id = Column(String(36), unique=True, nullable=False, index=True)

    # User identification (optional, for multi-user support)
    user_id = Column(String(255), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Portfolio configuration
    tickers = Column(SafeJSON, nullable=False)  # ["AAPL", "GOOGL", "MSFT"]
    weights = Column(SafeJSON, nullable=False)  # [0.4, 0.3, 0.3]
    start_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    end_date = Column(String(10), nullable=False)    # YYYY-MM-DD
    initial_cash = Column(Float, nullable=False)
    commission = Column(Float, default=0.0005)
    stake = Column(Integer, default=100)
    strategy_name = Column(String(255), nullable=True, index=True)

    # Key combined portfolio metrics (denormalized for fast querying)
    final_value = Column(Float, nullable=True)
    total_return = Column(Float, nullable=True, index=True)
    weighted_sharpe = Column(Float, nullable=True, index=True)
    max_drawdown = Column(Float, nullable=True)
    num_assets = Column(Integer, default=0)
    successful_backtests = Column(Integer, default=0)
    failed_backtests = Column(Integer, default=0)

    # Complete results (JSON format)
    portfolio_metrics = Column(SafeJSON, nullable=True)  # Combined metrics
    individual_results = Column(SafeJSON, nullable=True)  # Per-ticker metrics
    correlation_matrix = Column(SafeJSON, nullable=True)  # Correlation data
    optimization_suggestion = Column(SafeJSON, nullable=True)  # Optimal weights

    # Strategy parameters used
    params = Column(SafeJSON, nullable=True)

    # Plot image reference
    plot_filename = Column(String(255), nullable=True)

    def __repr__(self):
        tickers_str = ",".join(self.tickers[:3]) if self.tickers else "N/A"
        if self.tickers and len(self.tickers) > 3:
            tickers_str += "..."
        return (
            f"<PortfolioResult(id={self.portfolio_id}, "
            f"tickers=[{tickers_str}], "
            f"return={self.total_return:.2f}% if self.total_return else 'N/A')>"
        )

class WalkForwardOptimizationModel(Base):
    """
    Walk-Forward Optimization Model - Stores walk-forward analysis results.

    Stores parameter optimization results with train/validation split,
    including overfitting detection metrics.
    """
    __tablename__ = "walkforward_optimizations"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Unique identifier for the optimization run
    optimization_id = Column(String(36), unique=True, nullable=False, index=True)

    # User identification (optional, for multi-user support)
    user_id = Column(String(255), nullable=True, index=True)

    # Configuration parameters
    strategy_name = Column(String(255), nullable=False, index=True)
    ticker = Column(String(50), nullable=False, index=True)
    start_date = Column(String(10), nullable=False)
    end_date = Column(String(10), nullable=False)

    # Walk-forward configuration
    train_period_days = Column(Integer, nullable=False)
    test_period_days = Column(Integer, nullable=False)
    anchored = Column(Integer, default=0)  # 0 for rolling, 1 for anchored
    optimization_metric = Column(String(50), default="sharpe_ratio")

    # Backtest configuration
    initial_cash = Column(Float, nullable=False)
    commission = Column(Float, default=0.0005)
    stake = Column(Integer, default=100)

    # Parameter grid (JSON format)
    # e.g., {"fast_period": [5, 10, 20], "slow_period": [20, 30, 50]}
    param_grid = Column(SafeJSON, nullable=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Status
    status = Column(String(20), default="pending", index=True)  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)

    # Results summary (denormalized for fast querying)
    num_windows = Column(Integer, default=0)
    avg_train_performance = Column(Float, nullable=True)
    avg_test_performance = Column(Float, nullable=True)
    avg_degradation_pct = Column(Float, nullable=True)
    train_test_correlation = Column(Float, nullable=True)
    consistency_score = Column(Float, nullable=True)
    overfitting_detected = Column(Integer, default=0)  # 0 for False, 1 for True

    # Complete results (JSON format)
    # Stores all windows with train/test metrics, best params for each window
    windows = Column(SafeJSON, nullable=True)

    # Overfitting metrics (JSON format)
    overfitting_metrics = Column(SafeJSON, nullable=True)

    # Combined test metrics (JSON format)
    combined_test_metrics = Column(SafeJSON, nullable=True)

    def __repr__(self):
        return (
            f"<WalkForwardOptimization(id={self.optimization_id}, "
            f"strategy={self.strategy_name}, "
            f"ticker={self.ticker}, "
            f"status={self.status})>"
        )


class MarketDataModel(Base):
    """
    Market Data Model - Stores historical price data for symbols.

    Caches market data fetched from external sources (yfinance, etc.)
    to reduce API calls and improve performance.
    """
    __tablename__ = "market_data"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Symbol identification
    ticker = Column(String(50), nullable=False, index=True)

    # Date for this price data (trading day)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD format

    # OHLCV data
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    adj_close = Column(Float, nullable=True)  # Adjusted close (optional)

    # Metadata
    source = Column(String(50), default="yfinance")  # Data source (yfinance, ccxt, etc.)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint on ticker + date
    __table_args__ = (
        UniqueConstraint('ticker', 'date', name='uix_ticker_date'),
    )

    def __repr__(self):
        return (
            f"<MarketData(ticker={self.ticker}, "
            f"date={self.date}, "
            f"close={self.close})>"
        )


class TickerMetadataModel(Base):
    """
    Ticker Metadata Model - Caches comprehensive ticker information.

    Stores company fundamentals, market metrics, and trading statistics
    fetched from yfinance Ticker.info to reduce API calls and improve UX.
    Cache TTL is configurable (default 7 days).
    """
    __tablename__ = "ticker_metadata"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Ticker symbol (unique)
    ticker = Column(String(50), nullable=False, unique=True, index=True)

    # Company Basics
    long_name = Column(String(255), nullable=True)
    short_name = Column(String(100), nullable=True)
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    country = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    long_business_summary = Column(Text, nullable=True)

    # Market Metrics
    market_cap = Column(Float, nullable=True)
    trailing_pe = Column(Float, nullable=True)
    forward_pe = Column(Float, nullable=True)
    price_to_book = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    fifty_two_week_high = Column(Float, nullable=True)
    fifty_two_week_low = Column(Float, nullable=True)
    fifty_two_week_change_percent = Column(Float, nullable=True)

    # Trading Statistics
    current_price = Column(Float, nullable=True)
    previous_close = Column(Float, nullable=True)
    regular_market_open = Column(Float, nullable=True)
    day_low = Column(Float, nullable=True)
    day_high = Column(Float, nullable=True)
    regular_market_volume = Column(Float, nullable=True)
    average_volume = Column(Float, nullable=True)
    average_volume_10days = Column(Float, nullable=True)

    # Fundamental Data
    dividend_rate = Column(Float, nullable=True)
    dividend_yield = Column(Float, nullable=True)
    trailing_eps = Column(Float, nullable=True)
    forward_eps = Column(Float, nullable=True)
    revenue_per_share = Column(Float, nullable=True)
    profit_margins = Column(Float, nullable=True)

    # Additional Metrics (JSON for flexibility)
    additional_info = Column(SafeJSON, nullable=True)

    # Validation status
    is_valid = Column(Integer, default=1)  # 1 = valid, 0 = invalid ticker
    validation_error = Column(String(500), nullable=True)

    # Cache metadata
    source = Column(String(50), default="yfinance")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # TTL configuration - consider stale after this many days
    cache_ttl_days = Column(Integer, default=7)  # Refresh after 7 days

    def is_stale(self) -> bool:
        """Check if cache is stale based on TTL."""
        if not self.updated_at or not self.cache_ttl_days:
            return True
        age_days = (datetime.utcnow() - self.updated_at).days
        return age_days >= self.cache_ttl_days

    def __repr__(self):
        return (
            f"<TickerMetadata(ticker={self.ticker}, "
            f"name={self.long_name}, "
            f"valid={bool(self.is_valid)})>"
        )


class UserSettingsModel(Base):
    """
    User Settings Model - Stores user preferences for AI models and prompts.

    Supports both authenticated and anonymous users. Settings are per-user
    with fallback to localStorage on frontend if DB operations fail.
    """
    __tablename__ = "user_settings"

    # Primary key (auto-increment for simpler management)
    id = Column(Integer, primary_key=True, autoincrement=True)

    # User identification (nullable for anonymous users)
    # For authenticated users: Logto 'sub' claim (e.g., "auth0|123456")
    # For anonymous: NULL (single row for all anonymous users)
    user_id = Column(String(255), nullable=True, unique=True, index=True)

    # AI Model Configuration
    # Comma-separated list of model names (e.g., "gpt-5.1,deepseek-v3.1")
    # Max length: 500 chars (supports ~50 models at 10 chars each)
    selected_models = Column(String(500), nullable=False, default="gpt-5.1,deepseek-v3.1")

    # AI Prompt Templates
    code_analysis_prompt = Column(Text, nullable=False, default="Please analyze the following Backtrader strategy code. Explain its logic, potential pitfalls, and suggest improvements:\n\n{code}")
    code_rewrite_prompt = Column(Text, nullable=False, default="Please rewrite and optimize the following Backtrader strategy code to follow best practices and fix potential issues. Return ONLY the python code, no markdown formatting or explanation:\n\n{code}")
    full_strategy_analysis_prompt = Column(Text, nullable=False, default="Please analyze the trading strategy based on the following configurations, source code, performance metrics, the attached equity curve chart, and the recent trading logs.\n\n{contextText}\n\n{metricsText}\n\n{logsText}\n\nProvide a comprehensive assessment including:\n1. Overall Performance: Is it profitable and consistent?\n2. Risk Profile: analysis of drawdowns and volatility.\n3. Strengths & Weaknesses: What is working well and what isn't?\n4. Suggestions: Recommendations for improvement.\n5. Code Analysis: Comments on the strategy logic.\n6. Always return with Chinese.\n7. 不需要对策略代码逻辑进行点评")

    # ========== ENCRYPTED CREDENTIALS ==========
    # Note: All credential fields are encrypted using Fernet encryption
    # Values are stored as base64-encoded ciphertext

    # OpenAI Configuration (encrypted)
    openai_api_key = Column(Text, nullable=True)  # Encrypted API key
    openai_base_url = Column(String(500), nullable=True)  # Base URL (not encrypted)

    # Logto Authentication Configuration (encrypted where sensitive)
    logto_issuer = Column(String(500), nullable=True)  # Issuer URL (not encrypted)
    logto_jwks_uri = Column(String(500), nullable=True)  # JWKS URI (not encrypted)
    logto_audience = Column(String(500), nullable=True)  # Audience (not encrypted)
    logto_required_scopes = Column(String(500), nullable=True)  # Space-separated scopes (not encrypted)
    enable_login = Column(Boolean, nullable=True)  # Enable/disable login (not encrypted)

    # Proxy Configuration (not encrypted - just URLs)
    http_proxy = Column(String(500), nullable=True)
    https_proxy = Column(String(500), nullable=True)

    # CCXT Exchange Credentials (JSON field for flexible structure)
    # Structure: {
    #   "binance": {
    #     "paper": {"api_key": "encrypted...", "secret": "encrypted..."},
    #     "live": {"api_key": "encrypted...", "secret": "encrypted..."}
    #   },
    #   "okx": {
    #     "paper": {"api_key": "encrypted...", "secret": "encrypted...", "passphrase": "encrypted..."},
    #     "live": {...}
    #   }
    # }
    ccxt_credentials = Column(JSON, nullable=True)

    # Timestamps for auditing
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return (
            f"<UserSettings(user_id={self.user_id}, "
            f"models={self.selected_models})>"
        )


# Default database path for local development
DEFAULT_DB_PATH = "sqlite:///trading_sessions.db"
