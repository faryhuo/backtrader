"""
Centralized dependency providers for route handlers.

Uses lru_cache for singleton behavior with clear lifecycle management.
All storage dependencies should be injected via these providers.
"""
from functools import lru_cache

from src.db.storage.backtest import BacktestStorage
from src.db.storage.settings import SettingsStorage
from src.db.storage.strategy_version import StrategyVersionStorage
from src.db.storage.user_auth import UserAuthStorage


@lru_cache(maxsize=1)
def get_backtest_storage() -> BacktestStorage:
    """Singleton BacktestStorage provider."""
    return BacktestStorage()


@lru_cache(maxsize=1)
def get_settings_storage() -> SettingsStorage:
    """Singleton SettingsStorage provider."""
    return SettingsStorage()


@lru_cache(maxsize=1)
def get_version_storage() -> StrategyVersionStorage:
    """Singleton StrategyVersionStorage provider."""
    return StrategyVersionStorage()


@lru_cache(maxsize=1)
def get_user_auth_storage() -> UserAuthStorage:
    """Singleton system user storage provider."""
    return UserAuthStorage()
