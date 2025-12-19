import json
from pathlib import Path

import pytest

from src.utils import config_loader


@pytest.fixture(autouse=True)
def reset_config_cache(monkeypatch):
    monkeypatch.setattr(config_loader, "_config_cache", None)
    monkeypatch.setattr(config_loader, "_config_cache_path", None)


def make_config_data():
    return {
        "version": "1.0",
        "exchanges": {
            "binance": {
                "enabled": True,
                "name": "Binance",
                "adapter": "ccxt",
                "ccxt_id": "binance",
                "markets": ["spot", "futures"],
                "default_market": "spot",
                "paper_mode": {
                    "enabled": True,
                    "sandbox_url": None,
                    "initial_balance_usdt": 10000.0,
                },
                "rate_limits": {
                    "orders_per_second": 5,
                    "requests_per_minute": 60,
                },
                "notes": "test-exchange",
            },
            "okx": {
                "enabled": False,
                "name": "OKX",
                "adapter": "ccxt",
                "ccxt_id": "okx",
                "markets": ["spot"],
                "default_market": "spot",
                "paper_mode": {
                    "enabled": True,
                    "sandbox_url": None,
                    "initial_balance_usdt": 5000.0,
                },
                "rate_limits": None,
                "notes": None,
            },
        },
        "risk_management": {
            "position_limits": {
                "max_position_size_usd": 5000.0,
                "max_positions_count": 5,
                "max_leverage": 3,
            },
            "loss_limits": {
                "max_daily_loss_usd": 500.0,
                "max_daily_loss_percent": 5.0,
                "max_drawdown_percent": 10.0,
            },
            "order_limits": {
                "min_order_size_usd": 10.0,
                "max_order_size_usd": 2000.0,
                "max_slippage_percent": 1.0,
            },
        },
        "trading_settings": {
            "default_timeframe": "1m",
            "supported_timeframes": ["1m", "1h"],
            "reconnect_on_disconnect": True,
            "max_reconnect_attempts": 3,
            "heartbeat_interval_seconds": 15,
        },
        "notifications": {
            "enabled": True,
            "channels": ["websocket"],
            "events": ["order_filled"],
        },
    }


def write_config(tmp_path: Path, data: dict) -> Path:
    config_path = tmp_path / "broker_config.json"
    config_path.write_text(json.dumps(data))
    return config_path


def test_load_broker_config_and_cache(tmp_path):
    data = make_config_data()
    config_path = write_config(tmp_path, data)

    config = config_loader.load_broker_config(config_path=config_path)
    cached = config_loader.load_broker_config(config_path=config_path)

    assert cached is config
    assert config.exchanges["binance"].ccxt_id == "binance"


def test_load_broker_config_missing_file(tmp_path):
    missing = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        config_loader.load_broker_config(config_path=missing)


def test_get_exchange_config_disabled(tmp_path):
    data = make_config_data()
    data["exchanges"]["binance"]["enabled"] = False
    config_path = write_config(tmp_path, data)
    config = config_loader.load_broker_config(config_path=config_path)

    with pytest.raises(ValueError):
        config_loader.get_exchange_config("binance", config)


def test_get_exchange_config_unsupported_adapter(tmp_path):
    data = make_config_data()
    data["exchanges"]["binance"]["adapter"] = "custom"
    config_path = write_config(tmp_path, data)
    config = config_loader.load_broker_config(config_path=config_path)

    with pytest.raises(ValueError):
        config_loader.get_exchange_config("binance", config)


def test_list_enabled_exchanges(tmp_path):
    data = make_config_data()
    data["exchanges"]["okx"]["enabled"] = True
    config_path = write_config(tmp_path, data)

    config = config_loader.load_broker_config(config_path=config_path)
    enabled = config_loader.list_enabled_exchanges(config)

    exchange_ids = {item["id"] for item in enabled}
    assert exchange_ids == {"binance", "okx"}


def test_validate_symbol_and_timeframe(tmp_path):
    data = make_config_data()
    config_path = write_config(tmp_path, data)
    config = config_loader.load_broker_config(config_path=config_path)

    assert config_loader.validate_symbol("BTC/USDT", "binance", config) is True
    with pytest.raises(ValueError):
        config_loader.validate_symbol("BTCUSDT", "binance", config)

    assert config_loader.validate_timeframe("1h", config) is True
    with pytest.raises(ValueError):
        config_loader.validate_timeframe("2h", config)


def test_reload_config_forces_reload(tmp_path):
    data = make_config_data()
    config_path = write_config(tmp_path, data)

    first = config_loader.load_broker_config(config_path=config_path)

    changed = make_config_data()
    changed["exchanges"]["binance"]["name"] = "Binance Changed"
    write_config(tmp_path, changed)

    reloaded = config_loader.load_broker_config(config_path=config_path, reload=True)
    assert reloaded is not first
    assert reloaded.exchanges["binance"].name == "Binance Changed"


