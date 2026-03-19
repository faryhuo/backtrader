"""Tests for the BinanceStore exchange-backed implementation."""

import asyncio
from decimal import Decimal

import pytest

from src.brokers.binance_adapter.binance_store import BinanceStore


class StubClient:
    def __init__(self, api_key="", api_secret="", testnet=False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.ping_calls = 0
        self.calls = []
        self.symbol_info = {}
        self.klines_response = []
        self.ticker_response = {
            "lastPrice": "101.5",
            "bidPrice": "101.4",
            "askPrice": "101.6",
            "highPrice": "103.0",
            "lowPrice": "99.1",
            "volume": "1234.5",
            "closeTime": 1700000000000,
        }
        self.symbol_ticker_response = {"symbol": "BTCUSDT", "price": "101.5"}
        self.order_book_ticker_response = {"bidPrice": "101.4", "askPrice": "101.6"}
        self.account_response = {"balances": [{"asset": "USDT", "free": "250.0", "locked": "0"}]}
        self.open_orders_response = []
        self.all_orders_response = []
        self.my_trades_response = []
        self.created_order_response = {"orderId": 11, "status": "NEW"}
        self.cancel_order_response = {"orderId": 11, "status": "CANCELED"}
        self.get_order_response = {"orderId": 11, "status": "FILLED"}

    def ping(self):
        self.ping_calls += 1

    def get_ticker(self, **kwargs):
        self.calls.append(("get_ticker", kwargs))
        return self.ticker_response

    def get_klines(self, **kwargs):
        self.calls.append(("get_klines", kwargs))
        return self.klines_response

    def get_symbol_ticker(self, **kwargs):
        self.calls.append(("get_symbol_ticker", kwargs))
        return self.symbol_ticker_response

    def get_order_book_ticker(self, **kwargs):
        self.calls.append(("get_order_book_ticker", kwargs))
        return self.order_book_ticker_response

    def create_order(self, **kwargs):
        self.calls.append(("create_order", kwargs))
        return self.created_order_response

    def cancel_order(self, **kwargs):
        self.calls.append(("cancel_order", kwargs))
        return self.cancel_order_response

    def get_order(self, **kwargs):
        self.calls.append(("get_order", kwargs))
        return self.get_order_response

    def get_open_orders(self, **kwargs):
        self.calls.append(("get_open_orders", kwargs))
        return self.open_orders_response

    def get_all_orders(self, **kwargs):
        self.calls.append(("get_all_orders", kwargs))
        return self.all_orders_response

    def get_my_trades(self, **kwargs):
        self.calls.append(("get_my_trades", kwargs))
        return self.my_trades_response

    def get_account(self):
        self.calls.append(("get_account", {}))
        return self.account_response

    def get_symbol_info(self, symbol):
        self.calls.append(("get_symbol_info", {"symbol": symbol}))
        return self.symbol_info.get(symbol)


class StubTWM:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._alive = False
        self.stop_calls = 0
        self.join_calls = 0
        self.stop_socket_calls = []
        self.started_sockets = []

    def start(self):
        self._alive = True

    def stop(self):
        self.stop_calls += 1
        self._alive = False

    def is_alive(self):
        return self._alive

    def join(self, timeout=None):
        self.join_calls += 1
        self._alive = False

    def stop_socket(self, key):
        self.stop_socket_calls.append(key)

    def start_symbol_ticker_socket(self, **kwargs):
        self.started_sockets.append(("ticker", kwargs))
        return "ticker-key"

    def start_kline_socket(self, **kwargs):
        self.started_sockets.append(("kline", kwargs))
        return "kline-key"

    def start_user_socket(self, **kwargs):
        self.started_sockets.append(("user", kwargs))
        return "user-key"


@pytest.fixture
def client_factory(monkeypatch):
    created = []

    def _factory(*args, **kwargs):
        client = StubClient(*args, **kwargs)
        created.append(client)
        return client

    _factory.KLINE_INTERVAL_1MINUTE = "1m"
    monkeypatch.setattr("src.brokers.binance_adapter.binance_store.Client", _factory)
    return created


@pytest.fixture
def twm_factory(monkeypatch):
    created = []

    def _factory(**kwargs):
        twm = StubTWM(**kwargs)
        created.append(twm)
        return twm

    monkeypatch.setattr(
        "src.brokers.binance_adapter.binance_store.ThreadedWebsocketManager",
        _factory,
    )
    return created


@pytest.fixture
def unstarted_store():
    return BinanceStore(mode="paper", session_id="test-session-123")


@pytest.fixture
def started_store(client_factory):
    store = BinanceStore(mode="paper", session_id="test-session-123")
    store.start()
    yield store
    store.stop()


class TestBinanceStoreLifecycle:
    def test_start_paper_mode_uses_testnet_client(self, client_factory):
        store = BinanceStore(mode="paper")
        store.start()
        try:
            assert store.is_running is True
            assert client_factory[0].testnet is True
            assert client_factory[0].ping_calls == 1
        finally:
            store.stop()

    def test_start_live_mode_disables_testnet(self, client_factory):
        store = BinanceStore(mode="live")
        store.start()
        try:
            assert client_factory[0].testnet is False
        finally:
            store.stop()

    def test_get_client_raises_before_start(self, unstarted_store):
        with pytest.raises(RuntimeError, match="Store not started"):
            unstarted_store.get_client()

    def test_uses_exchange_account_data_is_true(self, unstarted_store):
        assert unstarted_store.uses_exchange_account_data() is True


class TestCallbacksAndWebsockets:
    def test_set_ticker_callback(self, started_store):
        callback = lambda _: None
        started_store.set_ticker_callback(callback)
        assert started_store._ticker_callback is callback

    def test_set_user_data_callback(self, started_store):
        callback = lambda _: None
        started_store.set_user_data_callback(callback)
        assert started_store._user_data_callback is callback

    def test_ensure_twm_uses_dedicated_event_loop(self, twm_factory, unstarted_store):
        unstarted_store._ensure_twm()

        assert len(twm_factory) == 1
        assert isinstance(twm_factory[0].kwargs["loop"], asyncio.AbstractEventLoop)
        assert twm_factory[0].kwargs["loop"] is unstarted_store._twm_loop

    def test_stop_closes_dedicated_event_loop(self, twm_factory, unstarted_store):
        unstarted_store._ensure_twm()
        loop = unstarted_store._twm_loop

        unstarted_store.stop()

        assert loop.is_closed() is True
        assert unstarted_store._twm is None
        assert unstarted_store._twm_loop is None
        assert unstarted_store._twm_started is False

    def test_ensure_twm_recreates_dead_manager(self, twm_factory, unstarted_store):
        unstarted_store._ensure_twm()
        first_twm = unstarted_store._twm
        first_loop = unstarted_store._twm_loop
        first_twm._alive = False

        unstarted_store._ensure_twm()

        assert len(twm_factory) == 2
        assert unstarted_store._twm is not first_twm
        assert unstarted_store._twm_loop is not first_loop
        assert first_loop.is_closed() is True

    def test_start_ticker_stream_starts_exchange_socket(self, client_factory, twm_factory):
        store = BinanceStore(mode="paper")
        store.start()
        try:
            store.set_ticker_callback(lambda _: None)
            store.start_ticker_stream("BTC/USDT")

            assert store._active_streams["ticker_BTC/USDT"] == "ticker-key"
            socket_type, kwargs = twm_factory[0].started_sockets[0]
            assert socket_type == "ticker"
            assert kwargs["symbol"] == "btcusdt"
        finally:
            store.stop()

    def test_ticker_stream_recovers_after_read_loop_closed(self, client_factory, twm_factory, monkeypatch):
        store = BinanceStore(mode="paper")
        store.start()
        try:
            store.set_ticker_callback(lambda _: None)
            store.start_ticker_stream("BTC/USDT")

            monkeypatch.setattr(store, "_schedule_websocket_recovery", store._recover_websocket_connection)

            first_twm = twm_factory[0]
            _socket_type, kwargs = first_twm.started_sockets[0]
            kwargs["callback"]({
                "e": "error",
                "type": "ReadLoopClosed",
                "m": "Read loop has been closed, please reset the websocket connection and listen to the message error.",
            })

            assert len(twm_factory) == 2
            assert store._twm is twm_factory[1]
            assert store._active_streams["ticker_BTC/USDT"] == "ticker-key"
        finally:
            store.stop()

    def test_start_kline_stream_is_idempotent(self, client_factory, twm_factory):
        store = BinanceStore(mode="paper")
        store.start()
        try:
            store.start_kline_stream("BTC/USDT", "1m", lambda _: None)
            store.start_kline_stream("BTC/USDT", "1m", lambda _: None)

            assert store._active_streams["kline_BTC/USDT_1m"] == "kline-key"
            assert len([item for item in twm_factory[0].started_sockets if item[0] == "kline"]) == 1
        finally:
            store.stop()

    def test_start_user_data_stream_is_idempotent(self, client_factory, twm_factory):
        store = BinanceStore(mode="paper")
        store.start()
        try:
            store.start_user_data_stream(lambda _: None)
            store.start_user_data_stream(lambda _: None)

            assert store._active_streams["user_data"] == "user-key"
            assert len([item for item in twm_factory[0].started_sockets if item[0] == "user"]) == 1
        finally:
            store.stop()

    def test_stop_stops_active_sockets_and_clears_callbacks(self, client_factory, twm_factory):
        store = BinanceStore(mode="paper")
        store.start()
        try:
            store.start_kline_stream("BTC/USDT", "1m", lambda _: None)
            twm = store._twm
        finally:
            store.stop()

        assert twm.stop_socket_calls == ["kline-key"]
        assert store._active_streams == {}
        assert store._kline_callbacks == {}


class TestMarketDataMethods:
    def test_fetch_ticker_normalizes_payload(self, started_store):
        ticker = started_store.fetch_ticker("BTC/USDT")

        assert ticker == {
            "last": 101.5,
            "bid": 101.4,
            "ask": 101.6,
            "high": 103.0,
            "low": 99.1,
            "volume": 1234.5,
            "timestamp": 1700000000000,
        }
        assert started_store.get_client().calls[-1] == ("get_ticker", {"symbol": "BTCUSDT"})

    def test_fetch_ohlcv_normalizes_bars_and_maps_since_ms(self, started_store):
        started_store.get_client().klines_response = [
            [1700000000000, "100", "105", "99", "101", "250", 0, 0, 0, 0, 0, 0],
            [1700000060000, "101", "106", "100", "102", "275", 0, 0, 0, 0, 0, 0],
        ]

        bars = started_store.fetch_ohlcv("BTC/USDT", interval="1m", limit=2, since_ms=1700000000000)

        assert bars == [
            [1700000000000, 100.0, 105.0, 99.0, 101.0, 250.0],
            [1700000060000, 101.0, 106.0, 100.0, 102.0, 275.0],
        ]
        assert started_store.get_client().calls[-1] == (
            "get_klines",
            {
                "symbol": "BTCUSDT",
                "interval": "1m",
                "limit": 2,
                "startTime": 1700000000000,
            },
        )

    def test_get_symbol_ticker_normalizes_symbol(self, started_store):
        result = started_store.get_symbol_ticker("BTC/USDT")

        assert result == {"symbol": "BTCUSDT", "price": 101.5}
        assert started_store.get_client().calls[-1] == ("get_symbol_ticker", {"symbol": "BTCUSDT"})

    def test_get_klines_returns_raw_exchange_payload(self, started_store):
        started_store.get_client().klines_response = [[1, "2", "3", "4", "5", "6", 0, 0, 0, 0, 0, 0]]

        klines = started_store.get_klines("BTCUSDT", "1m", limit=1)

        assert klines == [[1, "2", "3", "4", "5", "6", 0, 0, 0, 0, 0, 0]]


class TestTradingMethods:
    def test_create_order_normalizes_quantity_before_submit(self, started_store):
        started_store._symbol_info_cache["DOGEUSDT"] = {
            "symbol": "DOGEUSDT",
            "filters": [
                {
                    "filterType": "LOT_SIZE",
                    "minQty": "1.00000000",
                    "maxQty": "1000000.00000000",
                    "stepSize": "1.00000000",
                }
            ],
        }

        started_store.create_order("DOGE/USDT", "BUY", "MARKET", quantity=12.987)

        assert started_store.get_client().calls[-1] == (
            "create_order",
            {
                "symbol": "DOGEUSDT",
                "side": "BUY",
                "type": "MARKET",
                "quantity": "12",
            },
        )

    def test_create_limit_order_includes_price_and_tif(self, started_store):
        started_store._symbol_info_cache["BTCUSDT"] = {
            "symbol": "BTCUSDT",
            "filters": [
                {
                    "filterType": "LOT_SIZE",
                    "minQty": "0.00100000",
                    "maxQty": "100.00000000",
                    "stepSize": "0.00100000",
                }
            ],
        }

        started_store.create_order("BTCUSDT", "SELL", "LIMIT", quantity=0.1234, price=105.5)

        assert started_store.get_client().calls[-1] == (
            "create_order",
            {
                "symbol": "BTCUSDT",
                "side": "SELL",
                "type": "LIMIT",
                "quantity": "0.123",
                "price": "105.5",
                "timeInForce": "GTC",
            },
        )

    def test_cancel_get_open_orders_and_history_delegate_to_exchange(self, started_store):
        started_store.cancel_order("BTC/USDT", 11)
        started_store.get_order("BTC/USDT", 11)
        started_store.get_open_orders("BTC/USDT")
        started_store.get_all_orders("BTC/USDT", limit=50)
        started_store.get_my_trades("BTC/USDT", limit=50)
        started_store.get_account()

        assert ("cancel_order", {"symbol": "BTCUSDT", "orderId": 11}) in started_store.get_client().calls
        assert ("get_order", {"symbol": "BTCUSDT", "orderId": 11}) in started_store.get_client().calls
        assert ("get_open_orders", {"symbol": "BTCUSDT"}) in started_store.get_client().calls
        assert ("get_all_orders", {"symbol": "BTCUSDT", "limit": 50}) in started_store.get_client().calls
        assert ("get_my_trades", {"symbol": "BTCUSDT", "limit": 50}) in started_store.get_client().calls
        assert ("get_account", {}) in started_store.get_client().calls


class TestTradingRules:
    def test_get_symbol_trading_rules_prefers_notional_filter(self, started_store):
        started_store.get_client().symbol_info["BTCUSDT"] = {
            "symbol": "BTCUSDT",
            "filters": [
                {
                    "filterType": "LOT_SIZE",
                    "minQty": "0.00100000",
                    "maxQty": "100.00000000",
                    "stepSize": "0.00100000",
                },
                {
                    "filterType": "NOTIONAL",
                    "minNotional": "5.00000000",
                },
            ],
        }

        rules = started_store.get_symbol_trading_rules("BTC/USDT")

        assert rules == {
            "symbol": "BTCUSDT",
            "min_qty": "0.00100000",
            "max_qty": "100.00000000",
            "step_size": "0.00100000",
            "min_notional": "5.00000000",
        }

    def test_get_symbol_trading_rules_falls_back_to_min_notional(self, started_store):
        started_store.get_client().symbol_info["ETHUSDT"] = {
            "symbol": "ETHUSDT",
            "filters": [
                {
                    "filterType": "LOT_SIZE",
                    "minQty": "0.00100000",
                    "maxQty": "100.00000000",
                    "stepSize": "0.00100000",
                },
                {
                    "filterType": "MIN_NOTIONAL",
                    "minNotional": "10.00000000",
                },
            ],
        }

        rules = started_store.get_symbol_trading_rules("ETHUSDT")

        assert rules["min_notional"] == "10.00000000"

    def test_normalize_quantity_rejects_below_min_qty(self, unstarted_store):
        unstarted_store._client = object()
        unstarted_store._symbol_info_cache["BTCUSDT"] = {
            "symbol": "BTCUSDT",
            "filters": [
                {
                    "filterType": "LOT_SIZE",
                    "minQty": "0.00100000",
                    "maxQty": "100.00000000",
                    "stepSize": "0.00100000",
                }
            ],
        }

        with pytest.raises(ValueError, match="below Binance minQty"):
            unstarted_store.normalize_quantity("BTCUSDT", 0.0009)

    def test_normalize_quantity_rounds_down_to_step_size(self, unstarted_store):
        unstarted_store._client = object()
        unstarted_store._symbol_info_cache["DOGEUSDT"] = {
            "symbol": "DOGEUSDT",
            "filters": [
                {
                    "filterType": "LOT_SIZE",
                    "minQty": "1.00000000",
                    "maxQty": "1000000.00000000",
                    "stepSize": "1.00000000",
                }
            ],
        }

        normalized = unstarted_store.normalize_quantity("DOGEUSDT", 12.987654)

        assert normalized == Decimal("12")
