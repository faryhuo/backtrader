"""
Tests for BinanceStore — the core connection layer for the Binance adapter.

Tests cover:
- Initialization and lifecycle (paper/live modes)
- Ticker callback registration
- fetch_ticker (normalized output)
- fetch_ohlcv (normalized output)
- Paper trading helpers (orders, balances)
- Symbol normalization (BTC/USDT → BTCUSDT)
"""

import pytest

from src.brokers.binance_adapter.binance_store import BinanceStore


# ─────────────────────────── Fixtures ───────────────────────────


@pytest.fixture
def paper_store():
    """Create a paper-mode BinanceStore (no real API calls)."""
    store = BinanceStore(mode="paper", session_id="test-session-123")
    store.start()
    yield store
    store.stop()


@pytest.fixture
def unstarted_store():
    """Create a BinanceStore that hasn't been started."""
    return BinanceStore(mode="paper")


# ─────────────────────────── Initialization ───────────────────────────


class TestBinanceStoreInit:
    def test_paper_mode_init(self, paper_store):
        assert paper_store.is_paper_mode() is True
        assert paper_store.is_running is True
        assert paper_store.mode == "paper"

    def test_default_paper_balance(self, paper_store):
        assert paper_store.get_paper_balance("USDT") == 10000.0

    def test_unstarted_store_not_running(self, unstarted_store):
        assert unstarted_store.is_running is False

    def test_get_client_raises_before_start(self, unstarted_store):
        with pytest.raises(RuntimeError, match="Store not started"):
            unstarted_store.get_client()

    def test_start_stop_lifecycle(self):
        store = BinanceStore(mode="paper")
        assert store.is_running is False
        store.start()
        assert store.is_running is True
        store.stop()
        assert store.is_running is False

    def test_double_start_is_idempotent(self, paper_store):
        paper_store.start()  # second call
        assert paper_store.is_running is True


# ─────────────────────────── Callback Registration ───────────────────────────


class TestCallbacks:
    def test_set_ticker_callback(self, paper_store):
        callback = lambda x: None
        paper_store.set_ticker_callback(callback)
        assert paper_store._ticker_callback is callback

    def test_set_user_data_callback(self, paper_store):
        callback = lambda x: None
        paper_store.set_user_data_callback(callback)
        assert paper_store._user_data_callback is callback


# ─────────────────────────── fetch_ticker ───────────────────────────


class TestFetchTicker:
    def test_paper_mode_returns_normalized_dict(self, paper_store):
        ticker = paper_store.fetch_ticker("BTC/USDT")
        assert 'last' in ticker
        assert 'bid' in ticker
        assert 'ask' in ticker
        assert 'high' in ticker
        assert 'low' in ticker
        assert 'volume' in ticker
        assert 'timestamp' in ticker

    def test_paper_mode_price_is_reasonable(self, paper_store):
        ticker = paper_store.fetch_ticker("BTCUSDT")
        # Should be near 75000 (the base price for BTC)
        assert 74000 < ticker['last'] < 76000

    def test_bid_ask_spread(self, paper_store):
        ticker = paper_store.fetch_ticker("BTCUSDT")
        assert ticker['bid'] < ticker['ask']
        assert ticker['bid'] < ticker['last']
        assert ticker['ask'] > ticker['last']

    def test_symbol_normalization(self, paper_store):
        """Both BTC/USDT and BTCUSDT should work."""
        t1 = paper_store.fetch_ticker("BTC/USDT")
        t2 = paper_store.fetch_ticker("BTCUSDT")
        assert abs(t1['last'] - t2['last']) < 500  # Both near 75000


# ─────────────────────────── fetch_ohlcv ───────────────────────────


class TestFetchOHLCV:
    def test_returns_correct_number_of_bars(self, paper_store):
        bars = paper_store.fetch_ohlcv("BTC/USDT", interval="1m", limit=50)
        assert len(bars) == 50

    def test_bar_format_is_normalized(self, paper_store):
        bars = paper_store.fetch_ohlcv("BTC/USDT", interval="1m", limit=5)
        assert len(bars) > 0
        bar = bars[0]
        # Each bar should be [timestamp_ms, open, high, low, close, volume]
        assert len(bar) == 6
        assert isinstance(bar[0], int)       # timestamp
        assert isinstance(bar[1], float)     # open
        assert isinstance(bar[2], float)     # high
        assert isinstance(bar[3], float)     # low
        assert isinstance(bar[4], float)     # close
        assert isinstance(bar[5], float)     # volume

    def test_bars_are_time_ordered(self, paper_store):
        bars = paper_store.fetch_ohlcv("BTC/USDT", interval="1m", limit=10)
        timestamps = [b[0] for b in bars]
        assert timestamps == sorted(timestamps)

    def test_high_gte_low(self, paper_store):
        bars = paper_store.fetch_ohlcv("BTC/USDT", interval="5m", limit=10)
        for bar in bars:
            assert bar[2] >= bar[3], f"High {bar[2]} should be >= Low {bar[3]}"


# ─────────────────────────── get_symbol_ticker ───────────────────────────


class TestGetSymbolTicker:
    def test_paper_mode(self, paper_store):
        result = paper_store.get_symbol_ticker("BTCUSDT")
        assert 'symbol' in result
        assert 'price' in result
        assert result['symbol'] == 'BTCUSDT'

    def test_symbol_normalization(self, paper_store):
        result = paper_store.get_symbol_ticker("BTC/USDT")
        assert result['symbol'] == 'BTCUSDT'


# ─────────────────────────── Paper Trading ───────────────────────────


class TestPaperTrading:
    def test_set_and_get_balance(self, paper_store):
        paper_store.set_paper_balance("BTC", 1.5)
        assert paper_store.get_paper_balance("BTC") == 1.5

    def test_default_balance_for_unknown_asset(self, paper_store):
        assert paper_store.get_paper_balance("XRP") == 0.0

    def test_create_market_order_updates_balances(self, paper_store):
        initial_usdt = paper_store.get_paper_balance("USDT")
        order = paper_store.create_order(
            symbol="BTCUSDT", side="BUY", order_type="MARKET",
            quantity=0.01
        )
        assert order['status'] == 'FILLED'
        assert paper_store.get_paper_balance("BTC") > 0
        assert paper_store.get_paper_balance("USDT") < initial_usdt

    def test_create_limit_order_stays_new(self, paper_store):
        order = paper_store.create_order(
            symbol="BTCUSDT", side="BUY", order_type="LIMIT",
            quantity=0.01, price=70000.0
        )
        assert order['status'] == 'NEW'

    def test_cancel_paper_order(self, paper_store):
        order = paper_store.create_order(
            symbol="BTCUSDT", side="BUY", order_type="LIMIT",
            quantity=0.01, price=70000.0
        )
        result = paper_store.cancel_order("BTCUSDT", order['orderId'])
        assert result['status'] == 'CANCELED'

    def test_get_order(self, paper_store):
        order = paper_store.create_order(
            symbol="BTCUSDT", side="BUY", order_type="MARKET",
            quantity=0.01
        )
        result = paper_store.get_order("BTCUSDT", order['orderId'])
        assert result['orderId'] == order['orderId']

    def test_get_open_orders(self, paper_store):
        paper_store.create_order(
            symbol="BTCUSDT", side="BUY", order_type="LIMIT",
            quantity=0.01, price=70000.0
        )
        opens = paper_store.get_open_orders()
        assert len(opens) >= 1

    def test_get_account(self, paper_store):
        account = paper_store.get_account()
        assert 'balances' in account
        usdt_balance = next(
            b for b in account['balances'] if b['asset'] == 'USDT'
        )
        assert float(usdt_balance['free']) == 10000.0

    def test_sell_market_order_requires_balance(self, paper_store):
        with pytest.raises(ValueError, match="Insufficient paper balance"):
            paper_store.create_order(
                symbol="BTCUSDT", side="SELL", order_type="MARKET",
                quantity=0.01
            )


# ─────────────────────────── get_klines (raw format) ───────────────────────────


class TestGetKlines:
    def test_returns_raw_12_element_format(self, paper_store):
        klines = paper_store.get_klines("BTCUSDT", "1m", limit=5)
        assert len(klines) == 5
        assert len(klines[0]) == 12  # Raw Binance format

    def test_prices_are_strings_in_raw_format(self, paper_store):
        klines = paper_store.get_klines("BTCUSDT", "1m", limit=1)
        # Raw Binance format has string prices
        assert isinstance(klines[0][1], str)  # open price as string


# ─────────────────────────── WebSocket (paper mode skips) ───────────────────────────


class TestWebSocketPaperMode:
    def test_start_ticker_stream_is_noop(self, paper_store):
        """In paper mode, starting ticker stream should be a no-op."""
        paper_store.set_ticker_callback(lambda x: None)
        paper_store.start_ticker_stream("BTCUSDT")
        assert len(paper_store._active_streams) == 0

    def test_start_kline_stream_is_noop(self, paper_store):
        paper_store.start_kline_stream("BTCUSDT", "1m", lambda x: None)
        assert len(paper_store._active_streams) == 0

    def test_start_user_data_stream_is_noop(self, paper_store):
        paper_store.start_user_data_stream(lambda x: None)
        assert 'user_data' not in paper_store._active_streams
