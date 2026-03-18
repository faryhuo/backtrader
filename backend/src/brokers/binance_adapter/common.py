"""
Shared helpers for the Binance Backtrader adapter.

The adapter keeps the runtime split into three primary modules:
- `binance_store.py`: exchange connectivity and paper-trading state
- `binance_data.py`: Backtrader data feed integration
- `binance_broker.py`: Backtrader broker/order lifecycle integration

This module only holds cross-cutting constants and pure helper functions so
those three modules can stay focused on their own responsibilities.
"""

from __future__ import annotations

import re
from typing import Tuple

import backtrader as bt
from binance.client import Client

TIMEFRAME_INTERVALS = {
    "1m": Client.KLINE_INTERVAL_1MINUTE,
    "3m": Client.KLINE_INTERVAL_3MINUTE,
    "5m": Client.KLINE_INTERVAL_5MINUTE,
    "15m": Client.KLINE_INTERVAL_15MINUTE,
    "30m": Client.KLINE_INTERVAL_30MINUTE,
    "1h": Client.KLINE_INTERVAL_1HOUR,
    "2h": Client.KLINE_INTERVAL_2HOUR,
    "4h": Client.KLINE_INTERVAL_4HOUR,
    "6h": Client.KLINE_INTERVAL_6HOUR,
    "8h": Client.KLINE_INTERVAL_8HOUR,
    "12h": Client.KLINE_INTERVAL_12HOUR,
    "1d": Client.KLINE_INTERVAL_1DAY,
    "1w": Client.KLINE_INTERVAL_1WEEK,
    "1M": Client.KLINE_INTERVAL_1MONTH,
}

TIMEFRAME_SECONDS = {
    "1m": 60,
    "3m": 180,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "2h": 7200,
    "4h": 14400,
    "6h": 21600,
    "8h": 28800,
    "12h": 43200,
    "1d": 86400,
    "3d": 259200,
    "1w": 604800,
    "1M": 2592000,
}


def normalize_symbol(symbol: str) -> str:
    """Normalize symbols like `BTC/USDT` into Binance's `BTCUSDT` format."""
    return symbol.replace("/", "").upper()


def map_to_bt_timeframe(timeframe: str) -> Tuple[int, int]:
    """Map `1m`/`1h` style strings into Backtrader timeframe/compression."""
    match = re.match(r"(\d+)([a-zA-Z]+)", timeframe)
    if not match:
        return bt.TimeFrame.Minutes, 1

    quantity, unit = int(match.group(1)), match.group(2)
    if unit == "m":
        return bt.TimeFrame.Minutes, quantity
    if unit == "h":
        return bt.TimeFrame.Minutes, quantity * 60
    if unit == "d":
        return bt.TimeFrame.Days, quantity
    if unit == "w":
        return bt.TimeFrame.Weeks, quantity
    if unit == "M":
        return bt.TimeFrame.Months, quantity
    return bt.TimeFrame.Minutes, 1


def data_symbol(data) -> str:
    """Extract the symbol identifier from a Backtrader data feed."""
    if hasattr(data, "_symbol"):
        return data._symbol
    if hasattr(data, "_name"):
        return data._name
    raise ValueError("Data feed has no symbol")
