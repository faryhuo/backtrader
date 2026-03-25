"""
Base Models - Core SQLAlchemy utilities and shared components.

This module contains:
- Base declarative class
- SafeJSON type decorator
- Database initialization function
- Common enums
"""

import enum
import json
from datetime import datetime
from threading import Lock
from typing import Optional

from sqlalchemy import (
    Column, DateTime, Enum, Float, Integer, String, Text, TypeDecorator,
    create_engine, event
)
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

_DB_CACHE_LOCK = Lock()
_DB_CACHE: dict[tuple[str, bool], tuple[Engine, sessionmaker]] = {}


def _configure_sqlite_engine(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA temp_store=MEMORY")
        finally:
            cursor.close()


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
    cache_key = (database_url, bool(echo))
    with _DB_CACHE_LOCK:
        cached = _DB_CACHE.get(cache_key)
        if cached is not None:
            return cached

        engine_kwargs = {"echo": echo, "pool_pre_ping": True}
        if database_url.startswith("sqlite"):
            engine_kwargs["connect_args"] = {"check_same_thread": False}

        engine = create_engine(database_url, **engine_kwargs)
        if database_url.startswith("sqlite"):
            _configure_sqlite_engine(engine)

        Base.metadata.create_all(bind=engine)
        _apply_runtime_migrations(engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        _DB_CACHE[cache_key] = (engine, SessionLocal)
        return engine, SessionLocal


def _apply_runtime_migrations(engine: Engine) -> None:
    """Apply lightweight schema migrations for deployments without Alembic."""
    inspector = inspect(engine)
    try:
        columns = {column["name"] for column in inspector.get_columns("user_settings")}
    except Exception:
        return

    alter_statements: list[str] = []
    if "ai_provider" not in columns:
        alter_statements.append("ALTER TABLE user_settings ADD COLUMN ai_provider VARCHAR(50)")
    if "ai_provider_priority" not in columns:
        alter_statements.append("ALTER TABLE user_settings ADD COLUMN ai_provider_priority TEXT")
    if "ai_provider_configs" not in columns:
        alter_statements.append("ALTER TABLE user_settings ADD COLUMN ai_provider_configs TEXT")

    if not alter_statements:
        return

    with engine.begin() as connection:
        for statement in alter_statements:
            connection.execute(text(statement))


__all__ = [
    "Base",
    "SafeJSON",
    "SessionStatusEnum",
    "OrderStatusEnum",
    "init_database",
]
