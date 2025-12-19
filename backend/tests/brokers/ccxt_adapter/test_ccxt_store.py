import asyncio
import types

import pytest

from src.brokers.ccxt_adapter.ccxt_store import CCXTStore


def test_get_exchange_raises_when_not_started():
    store = CCXTStore(exchange_id="binance", mode="paper")
    with pytest.raises(RuntimeError):
        store.get_exchange()


def test_run_coroutine_raises_when_loop_not_running():
    store = CCXTStore(exchange_id="binance", mode="paper")
    with pytest.raises(RuntimeError):
        store.run_coroutine(asyncio.sleep(0))


def test_load_credentials_uses_config_manager(monkeypatch):
    store = CCXTStore(exchange_id="binance", mode="paper", user_id="u1")

    class StubConfigManager:
        def __init__(self, user_id=None):
            self.user_id = user_id

        def get_ccxt_credentials(self, exchange, mode):
            assert exchange == "binance"
            assert mode == "paper"
            return {"api_key": "k", "secret": "s", "passphrase": None}

    monkeypatch.setattr("src.brokers.ccxt_adapter.ccxt_store.ConfigManager", StubConfigManager, raising=False)
    store._load_credentials()
    assert store.api_key == "k"
    assert store.secret == "s"


def test_init_exchange_sets_binance_testnet_urls(monkeypatch):
    store = CCXTStore(exchange_id="binance", mode="paper", config={"default_market": "spot"})
    store.api_key = "k"
    store.secret = "s"
    store.passphrase = None

    class FakeExchange:
        def __init__(self, config):
            self.config = config
            self.options = {}
            self.urls = {"api": {}}
            self.markets = {}

        def set_sandbox_mode(self, enabled):
            self.sandbox = enabled

    fake_ccxt = types.SimpleNamespace(binance=FakeExchange)
    monkeypatch.setattr("src.brokers.ccxt_adapter.ccxt_store.ccxt", fake_ccxt)

    store._init_exchange()
    assert store._exchange is not None
    assert store._exchange.sandbox is True
    assert store._exchange.urls["api"]["public"].startswith("https://testnet.binance.vision/")

