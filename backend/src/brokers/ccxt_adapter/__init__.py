"""
CCXT adapter for Backtrader live trading.

This package provides Backtrader-compatible Store, Broker, and Data classes
that connect to cryptocurrency exchanges via the CCXT library.
"""

import warnings

from src.utils.dns_compat import ensure_aiodns_pycares_compat

# Ensure aiodns/pycares compatibility is patched before any CCXT import.
ensure_aiodns_pycares_compat()

# Suppress noisy protobuf runtime_version warnings emitted by upstream stubs.
warnings.filterwarnings(
    "once",
    message=r"Protobuf gencode version .*runtime version .*",
    category=UserWarning,
    module=r"google\.protobuf\.runtime_version"
)

from .ccxt_store import CCXTStore
from .ccxt_broker import CCXTBroker
from .ccxt_data import CCXTData

__all__ = ['CCXTStore', 'CCXTBroker', 'CCXTData']
