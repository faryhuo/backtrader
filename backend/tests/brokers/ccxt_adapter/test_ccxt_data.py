import backtrader as bt
import pytest

from src.brokers.ccxt_adapter.ccxt_data import CCXTData, _map_to_bt_timeframe


@pytest.mark.parametrize(
    "tf,expected",
    [
        ("1m", (bt.TimeFrame.Minutes, 1)),
        ("15m", (bt.TimeFrame.Minutes, 15)),
        ("1h", (bt.TimeFrame.Minutes, 60)),
        ("2d", (bt.TimeFrame.Days, 2)),
        ("1w", (bt.TimeFrame.Weeks, 1)),
        ("1M", (bt.TimeFrame.Months, 1)),
    ],
)
def test_map_to_bt_timeframe(tf, expected):
    assert _map_to_bt_timeframe(tf) == expected


def test_ccxtdata_init_rejects_unsupported_timeframe():
    class StubStore:
        def get_exchange(self):
            return object()

    with pytest.raises(ValueError):
        CCXTData(store=StubStore(), symbol="BTC/USDT", ccxt_timeframe="not-supported")
