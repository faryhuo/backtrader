"""
IBKR adapter for Backtrader live trading.

This module wraps Backtrader's built-in IBStore to align with the same
Store/Broker/Data pattern used by the CCXT adapter, enabling seamless
switching between paper/live IBKR sessions and crypto CCXT sessions.
"""

from .ibkr_store import IBKRStore, parse_timeframe

__all__ = ["IBKRStore", "parse_timeframe"]
