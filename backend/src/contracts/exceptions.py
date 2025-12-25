"""
Common Exceptions - Shared exception classes.

This module provides exception classes that can be safely imported anywhere
without causing circular dependencies. These are pure Python exceptions with
no dependencies on service, routes, or database layers.
"""


class StrategyLoadError(Exception):
    """Raised when strategy script cannot be loaded or parsed."""
    pass


class DataLoadError(Exception):
    """Raised when market data cannot be loaded from any source."""
    pass


__all__ = ["StrategyLoadError", "DataLoadError"]
