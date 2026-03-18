"""
Binance Adapter - Direct Binance API integration for Backtrader.

Architecture follows the standard Backtrader adapter split:
- `binance_store.py`: connection layer, market/trading API access, paper state
- `binance_data.py`: Backtrader data feed that loads OHLCV bars from the store
- `binance_broker.py`: Backtrader broker that routes orders through the store
- `common.py`: shared constants and pure helpers used by the three runtime modules
"""

from .binance_broker import BinanceBroker
from .binance_data import BinanceData
from .binance_store import BinanceStore
from .common import TIMEFRAME_INTERVALS, TIMEFRAME_SECONDS, normalize_symbol

__all__ = [
    'BinanceStore',
    'BinanceData',
    'BinanceBroker',
    'normalize_symbol',
    'TIMEFRAME_INTERVALS',
    'TIMEFRAME_SECONDS',
]
