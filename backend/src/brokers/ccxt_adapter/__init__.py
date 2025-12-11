"""
CCXT adapter for Backtrader live trading.

This package provides Backtrader-compatible Store, Broker, and Data classes
that connect to cryptocurrency exchanges via the CCXT library.
"""

from src.utils.dns_compat import ensure_aiodns_pycares_compat

ensure_aiodns_pycares_compat()

from .ccxt_store import CCXTStore
from .ccxt_broker import CCXTBroker
from .ccxt_data import CCXTData

__all__ = ['CCXTStore', 'CCXTBroker', 'CCXTData']
