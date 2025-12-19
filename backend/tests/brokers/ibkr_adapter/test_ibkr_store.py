import sys
import types

import pytest

from src.brokers.ibkr_adapter.ibkr_store import IBKRStore, IBKRStoreError, parse_timeframe


def test_parse_timeframe_valid_and_invalid():
    tf, compression = parse_timeframe("1m")
    assert compression == 1

    with pytest.raises(ValueError):
        parse_timeframe("2m")


def test_ibkr_store_start_stop_uses_stubbed_ibstore(monkeypatch):
    disconnected = {"ok": False}

    class StubConn:
        def disconnect(self):
            disconnected["ok"] = True

    class StubIBStore:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.conn = StubConn()

        def getbroker(self):
            return types.SimpleNamespace(setcash=lambda *_: None, setcommission=lambda **_: None)

        def getdata(self, **kwargs):
            return object()

    stub_module = types.SimpleNamespace(IBStore=StubIBStore)
    monkeypatch.setitem(sys.modules, "backtrader.stores.ibstore", stub_module)

    store = IBKRStore(mode="paper", host="127.0.0.1", port=4001, client_id=1)
    store.start()
    assert store._store is not None

    store.stop()
    assert disconnected["ok"] is True
    assert store._store is None


def test_ibkr_store_get_data_requires_start():
    store = IBKRStore(mode="paper")
    with pytest.raises(IBKRStoreError):
        store.get_data("AAPL-STK-SMART-USD", timeframe="1m")

