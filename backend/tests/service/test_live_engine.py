import types

import pytest

from src.service import live_engine


def test_build_components_ccxt(monkeypatch):
    calls = {"store_start": 0}

    class StubStore:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def start(self):
            calls["store_start"] += 1

    class StubBroker:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class StubData:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    ex_config = types.SimpleNamespace(adapter="ccxt", ccxt_id="binance", default_market="spot", markets=["spot"])
    monkeypatch.setattr(live_engine, "get_exchange_config", lambda exchange, config: ex_config)
    monkeypatch.setattr(live_engine, "CCXTStore", StubStore)
    monkeypatch.setattr(live_engine, "CCXTBroker", StubBroker)
    monkeypatch.setattr(live_engine, "CCXTData", StubData)

    store, broker, data, adapter = live_engine._build_components(
        exchange="binance",
        mode="paper",
        symbol="BTC/USDT",
        timeframe="1m",
        initial_cash=100,
        commission=0.0,
        session_id="s1",
        config={},
        user_id="u1",
    )

    assert calls["store_start"] == 1
    assert adapter == "ccxt"
    assert isinstance(store, StubStore)
    assert isinstance(broker, StubBroker)
    assert isinstance(data, StubData)


def test_build_components_ibkr(monkeypatch):
    class StubIBKR:
        def __init__(self, mode):
            self.mode = mode

        def start(self):
            return None

        def get_broker(self, initial_cash, commission):
            return object()

        def get_data(self, symbol, timeframe):
            return object()

    ex_config = types.SimpleNamespace(adapter="ibkr", ccxt_id=None, default_market="spot", markets=["spot"])
    monkeypatch.setattr(live_engine, "get_exchange_config", lambda exchange, config: ex_config)
    monkeypatch.setattr(live_engine, "IBKRStore", StubIBKR)

    store, broker, data, adapter = live_engine._build_components(
        exchange="ibkr",
        mode="paper",
        symbol="AAPL-STK-SMART-USD",
        timeframe="1m",
        initial_cash=100,
        commission=0.0,
        session_id="s1",
        config={},
        user_id=None,
    )

    assert adapter == "ibkr"
    assert isinstance(store, StubIBKR)
    assert broker is not None
    assert data is not None


def test_build_components_unknown_adapter(monkeypatch):
    ex_config = types.SimpleNamespace(adapter="nope", ccxt_id=None, default_market="spot", markets=["spot"])
    monkeypatch.setattr(live_engine, "get_exchange_config", lambda exchange, config: ex_config)
    with pytest.raises(live_engine.LiveTradingError):
        live_engine._build_components(
            exchange="x",
            mode="paper",
            symbol="BTC/USDT",
            timeframe="1m",
            initial_cash=100,
            commission=0.0,
            session_id=None,
            config={},
            user_id=None,
        )


def test_safe_returns_stop_handles_zero_division(monkeypatch):
    def raise_zero(self):
        raise ZeroDivisionError()

    monkeypatch.setattr(live_engine.bt.analyzers.Returns, "stop", raise_zero)
    analyzer = object.__new__(live_engine.SafeReturns)
    analyzer.rets = {}
    live_engine.SafeReturns.stop(analyzer)
    assert analyzer.rets["rnorm100"] == 0.0
