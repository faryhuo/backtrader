"""
Market Models - SQLAlchemy models for market data persistence.

This module defines database tables for storing:
- Market data (OHLCV)
- Ticker metadata
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, UniqueConstraint

from src.db.models.base import Base, SafeJSON


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


__all__ = [
    "MarketDataModel",
    "TickerMetadataModel",
]
