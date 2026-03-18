"""Tests for BinanceData live/historical transition helpers."""

from datetime import datetime

from src.brokers.binance_adapter.binance_data import BinanceData


class DummyStore:
    def __init__(self):
        self._running = True
        self.kline_streams = []

    @property
    def is_running(self):
        return self._running

    def start_kline_stream(self, symbol, interval, callback):
        self.kline_streams.append((symbol, interval, callback))

    def fetch_ohlcv(self, **kwargs):
        return []


class TestBinanceData:
    def test_closed_live_kline_is_buffered_once(self):
        store = DummyStore()
        data = BinanceData(store=store, symbol="BTCUSDT", timeframe="1m")

        data._on_live_kline({
            "time_ms": 1_700_000_000_000,
            "open": 100,
            "high": 110,
            "low": 95,
            "close": 105,
            "volume": 12,
            "is_closed": True,
        })
        data._on_live_kline({
            "time_ms": 1_700_000_000_000,
            "open": 100,
            "high": 110,
            "low": 95,
            "close": 105,
            "volume": 12,
            "is_closed": True,
        })

        assert len(data._live_buffer) == 1
        assert data._live_buffer[0][4] == 105.0

    def test_open_live_kline_is_ignored(self):
        store = DummyStore()
        data = BinanceData(store=store, symbol="BTCUSDT", timeframe="1m")

        data._on_live_kline({
            "time_ms": 1_700_000_000_000,
            "open": 100,
            "high": 110,
            "low": 95,
            "close": 105,
            "volume": 12,
            "is_closed": False,
        })

        assert data._live_buffer == []

    def test_datetime_to_ms_treats_naive_datetime_as_utc(self):
        dt_obj = datetime(2026, 3, 18, 11, 34, 0)

        result = BinanceData._datetime_to_ms(dt_obj)

        assert result == 1773833640000
