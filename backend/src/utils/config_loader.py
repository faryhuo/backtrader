"""
Configuration Loader - Load and validate broker configuration.

This module loads broker_config.json and provides typed access to
exchange settings, risk limits, and trading parameters.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError

from src.config.settings import CONFIG_DIR

logger = logging.getLogger(__name__)


# Pydantic models for configuration validation


class PaperModeConfig(BaseModel):
    """Paper trading configuration."""
    enabled: bool = True
    sandbox_url: Optional[str] = None
    initial_balance_usdt: float = 10000.0


class RateLimits(BaseModel):
    """Exchange rate limits."""
    orders_per_second: int = 10
    requests_per_minute: int = 1200


class ExchangeConfig(BaseModel):
    """Exchange-specific configuration."""
    enabled: bool = True
    name: str
    adapter: str = "ccxt"
    ccxt_id: str
    markets: List[str]
    default_market: str = "spot"
    paper_mode: PaperModeConfig
    rate_limits: Optional[RateLimits] = None
    notes: Optional[str] = None


class PositionLimits(BaseModel):
    """Position size limits."""
    max_position_size_usd: float = 5000.0
    max_positions_count: int = 5
    max_leverage: int = 1


class LossLimits(BaseModel):
    """Loss limit configuration."""
    max_daily_loss_usd: float = 500.0
    max_daily_loss_percent: float = 5.0
    max_drawdown_percent: float = 10.0


class OrderLimits(BaseModel):
    """Order size limits."""
    min_order_size_usd: float = 10.0
    max_order_size_usd: float = 5000.0
    max_slippage_percent: float = 1.0


class RiskManagement(BaseModel):
    """Risk management configuration."""
    position_limits: PositionLimits
    loss_limits: LossLimits
    order_limits: OrderLimits


class TradingSettings(BaseModel):
    """General trading settings."""
    default_timeframe: str = "1m"
    supported_timeframes: List[str] = Field(
        default=["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
    )
    reconnect_on_disconnect: bool = True
    max_reconnect_attempts: int = 5
    heartbeat_interval_seconds: int = 30


class NotificationSettings(BaseModel):
    """Notification configuration."""
    enabled: bool = True
    channels: List[str] = ["websocket"]
    events: List[str] = Field(
        default=["order_filled", "position_opened", "position_closed", "error", "risk_alert"]
    )


class BrokerConfig(BaseModel):
    """Complete broker configuration."""
    version: str = "1.0"
    exchanges: Dict[str, ExchangeConfig]
    risk_management: RiskManagement
    trading_settings: TradingSettings
    notifications: NotificationSettings
    description: Optional[str] = None
    instructions: Optional[Dict] = None


# Configuration cache
_config_cache: Optional[BrokerConfig] = None
_config_cache_path: Optional[Path] = None


def load_broker_config(config_path: Optional[Path] = None, reload: bool = False) -> BrokerConfig:
    """
    Load and validate broker configuration from JSON file.

    Args:
        config_path: Path to broker_config.json (default: CONFIG_DIR/broker_config.json)
        reload: Force reload even if cached

    Returns:
        BrokerConfig: Validated configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValidationError: If config is invalid
        json.JSONDecodeError: If JSON is malformed
    """
    global _config_cache, _config_cache_path

    # Use default path if not specified
    if config_path is None:
        config_path = CONFIG_DIR / "broker_config.json"

    # Return cached config if available and not forcing reload
    if not reload and _config_cache and _config_cache_path == config_path:
        return _config_cache

    # Check file exists
    if not config_path.exists():
        raise FileNotFoundError(
            f"Broker configuration not found at {config_path}. "
            f"Copy broker_config.template.json to broker_config.json and customize."
        )

    logger.info(f"Loading broker configuration from {config_path}")

    try:
        # Load JSON
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        # Validate with Pydantic
        config = BrokerConfig(**config_data)

        # Cache for future use
        _config_cache = config
        _config_cache_path = config_path

        # Log loaded configuration
        enabled_exchanges = [
            ex_id for ex_id, ex_config in config.exchanges.items()
            if ex_config.enabled
        ]
        logger.info(f"Loaded configuration v{config.version}")
        logger.info(f"Enabled exchanges: {', '.join(enabled_exchanges)}")

        return config

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {config_path}: {e}")
        raise

    except ValidationError as e:
        logger.error(f"Invalid configuration structure: {e}")
        raise


def get_exchange_config(exchange_id: str, config: Optional[BrokerConfig] = None) -> ExchangeConfig:
    """
    Get configuration for specific exchange.

    Args:
        exchange_id: Exchange identifier (e.g., 'binance')
        config: Broker config (loads default if not provided)

    Returns:
        ExchangeConfig: Exchange configuration

    Raises:
        ValueError: If exchange not found or not enabled
    """
    if config is None:
        config = load_broker_config()

    exchange_id = exchange_id.lower()

    if exchange_id not in config.exchanges:
        raise ValueError(
            f"Exchange '{exchange_id}' not found in configuration. "
            f"Available: {', '.join(config.exchanges.keys())}"
        )

    ex_config = config.exchanges[exchange_id]

    if not ex_config.enabled:
        raise ValueError(f"Exchange '{exchange_id}' is disabled in configuration")

    # Basic adapter validation to avoid unsupported integrations
    if ex_config.adapter.lower() not in {"ccxt", "ibkr"}:
        raise ValueError(
            f"Exchange '{exchange_id}' uses unsupported adapter '{ex_config.adapter}'. "
            "Supported adapters: ccxt, ibkr"
        )

    return ex_config


def list_enabled_exchanges(config: Optional[BrokerConfig] = None) -> List[Dict]:
    """
    List all enabled exchanges.

    Args:
        config: Broker config (loads default if not provided)

    Returns:
        List of exchange info dicts
    """
    if config is None:
        config = load_broker_config()

    exchanges = []
    for ex_id, ex_config in config.exchanges.items():
        if ex_config.enabled:
            exchanges.append({
                'id': ex_id,
                'name': ex_config.name,
                'adapter': ex_config.adapter,
                'ccxt_id': ex_config.ccxt_id,
                'markets': ex_config.markets,
                'default_market': ex_config.default_market,
                'paper_mode_available': ex_config.paper_mode.enabled
            })

    return exchanges


def get_risk_config(config: Optional[BrokerConfig] = None) -> RiskManagement:
    """
    Get risk management configuration.

    Args:
        config: Broker config (loads default if not provided)

    Returns:
        RiskManagement: Risk configuration
    """
    if config is None:
        config = load_broker_config()

    return config.risk_management


def validate_symbol(
    symbol: str,
    exchange_id: str,
    config: Optional[BrokerConfig] = None
) -> bool:
    """
    Validate that symbol format is correct.

    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        exchange_id: Exchange to validate for
        config: Broker config (loads default if not provided)

    Returns:
        bool: True if valid

    Raises:
        ValueError: If symbol format is invalid
    """
    # Basic format check
    if '/' not in symbol:
        raise ValueError(
            f"Invalid symbol format: '{symbol}'. "
            f"Expected format: 'BASE/QUOTE' (e.g., 'BTC/USDT')"
        )

    parts = symbol.split('/')
    if len(parts) != 2:
        raise ValueError(f"Invalid symbol format: '{symbol}'")

    base, quote = parts
    if not base or not quote:
        raise ValueError(f"Invalid symbol: empty base or quote in '{symbol}'")

    # Check if exchange exists (will raise if not)
    get_exchange_config(exchange_id, config)

    return True


def validate_timeframe(
    timeframe: str,
    config: Optional[BrokerConfig] = None
) -> bool:
    """
    Validate that timeframe is supported.

    Args:
        timeframe: Timeframe string (e.g., '1m', '1h')
        config: Broker config (loads default if not provided)

    Returns:
        bool: True if valid

    Raises:
        ValueError: If timeframe not supported
    """
    if config is None:
        config = load_broker_config()

    supported = config.trading_settings.supported_timeframes

    if timeframe not in supported:
        raise ValueError(
            f"Timeframe '{timeframe}' not supported. "
            f"Supported: {', '.join(supported)}"
        )

    return True


def reload_config() -> BrokerConfig:
    """
    Force reload configuration from disk.

    Returns:
        BrokerConfig: Freshly loaded configuration
    """
    return load_broker_config(reload=True)
