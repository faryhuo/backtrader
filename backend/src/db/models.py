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

from sqlalchemy import Column, DateTime, Enum, Float, Integer, JSON, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


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
    positions = Column(JSON, default=list)  # Current positions
    config = Column(JSON, default=dict)  # Session configuration
    metrics = Column(JSON, default=dict)  # Performance metrics

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
    metadata_json = Column("metadata", JSON, default=dict)

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
    metadata_json = Column("metadata", JSON, default=dict)

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


# Default database path for local development
DEFAULT_DB_PATH = "sqlite:///trading_sessions.db"
