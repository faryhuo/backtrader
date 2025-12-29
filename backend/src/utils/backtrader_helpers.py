"""
Backtrader Helper Utilities - Safe accessors for Backtrader internal attributes.

This module encapsulates access to Backtrader's internal structure to:
- Centralize private attribute access patterns
- Provide type-safe accessors with fallbacks
- Enable easier testing and mocking
- Isolate Backtrader version-specific behavior

Common patterns replaced:
- hasattr(data, '_name') -> get_data_name(data)
- feed._dataname -> get_dataframe(feed)
- order.data._name -> get_ticker_from_order(order)
"""

from typing import Optional, Dict, Any
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def get_data_name(data) -> str:
    """
    Safely get the name of a Backtrader data feed.

    Backtrader stores the name in the `_name` attribute, which is set
    when adding data via `cerebro.adddata(feed, name="AAPL")`.

    Args:
        data: Backtrader data feed (bt.feeds.DataBase or similar)

    Returns:
        The data feed name, or "UNKNOWN" if not available

    Examples:
        >>> feed = bt.feeds.PandasData(dataname=df)
        >>> cerebro.adddata(feed, name="AAPL")
        >>> get_data_name(feed)
        'AAPL'
    """
    # Primary: Check _name attribute (most common case)
    if hasattr(data, '_name') and data._name:
        return str(data._name)

    # Fallback: Check params.name
    if hasattr(data, 'p') and hasattr(data.p, 'name') and data.p.name:
        return str(data.p.name)

    # Fallback: Check params.dataname for filename-based data
    if hasattr(data, 'p') and hasattr(data.p, 'dataname'):
        dataname = data.p.dataname
        if isinstance(dataname, str):
            # Extract filename without extension
            import os
            return os.path.splitext(os.path.basename(dataname))[0]

    return "UNKNOWN"


def get_dataframe(feed) -> Optional[pd.DataFrame]:
    """
    Safely extract the underlying DataFrame from a Backtrader feed.

    Handles both direct `_dataname` access and parameter-based access
    for PandasData and similar feeds.

    Args:
        feed: Backtrader data feed

    Returns:
        The underlying pandas DataFrame, or None if not available

    Examples:
        >>> feed = bt.feeds.PandasData(dataname=df)
        >>> get_dataframe(feed)
        <pandas.DataFrame>
    """
    # Primary: Direct _dataname access (for PandasData)
    if hasattr(feed, '_dataname') and feed._dataname is not None:
        dataname = feed._dataname
        if isinstance(dataname, pd.DataFrame):
            return dataname

    # Fallback: Check params.dataname
    if hasattr(feed, 'p') and hasattr(feed.p, 'dataname'):
        dataname = feed.p.dataname
        if isinstance(dataname, pd.DataFrame):
            return dataname

    return None


def get_ticker_from_order(order, fallback: str = "UNKNOWN") -> str:
    """
    Get ticker name from a Backtrader order's data feed.

    Args:
        order: Backtrader order object
        fallback: Value to return if ticker cannot be determined

    Returns:
        The ticker symbol from the order's data feed

    Examples:
        >>> order = strategy.buy(data=strategy.datas[0], size=100)
        >>> get_ticker_from_order(order)
        'AAPL'
    """
    if hasattr(order, 'data') and order.data is not None:
        return get_data_name(order.data)
    return fallback


def get_ticker_from_data_mapping(
    order,
    ticker_data: Dict[str, Any],
    fallback: str = "UNKNOWN"
) -> str:
    """
    Get ticker name by matching order's data feed against a ticker mapping.

    This is useful when the data feed doesn't have a _name attribute,
    but you have a mapping of ticker -> data feed.

    Args:
        order: Backtrader order object
        ticker_data: Dictionary mapping ticker symbols to data feeds
        fallback: Value to return if ticker cannot be determined

    Returns:
        The ticker symbol, or fallback if not found

    Examples:
        >>> ticker_data = {"AAPL": data1, "GOOGL": data2}
        >>> order = strategy.buy(data=data1, size=100)
        >>> get_ticker_from_data_mapping(order, ticker_data)
        'AAPL'
    """
    # First try direct name extraction
    ticker = get_ticker_from_order(order, fallback=None)
    if ticker and ticker != "UNKNOWN":
        return ticker

    # Fall back to matching against ticker_data mapping
    if hasattr(order, 'data') and order.data is not None:
        for ticker, data in ticker_data.items():
            if data == order.data:
                return ticker

    return fallback


def get_data_dates(feed) -> Optional[set]:
    """
    Extract the set of dates from a Backtrader data feed.

    Args:
        feed: Backtrader data feed

    Returns:
        Set of dates in the data feed, or None if extraction fails

    Examples:
        >>> feed = bt.feeds.PandasData(dataname=df)
        >>> dates = get_data_dates(feed)
        >>> len(dates)
        252
    """
    df = get_dataframe(feed)
    if df is not None and hasattr(df, 'index'):
        try:
            # Handle DatetimeIndex
            if hasattr(df.index, 'date'):
                return set(df.index.date)
            # Handle regular index
            return set(df.index)
        except Exception as e:
            logger.warning(f"Failed to extract dates from data feed: {e}")

    return None


def get_close_price(data, offset: int = 0) -> Optional[float]:
    """
    Safely get the close price from a Backtrader data feed.

    Args:
        data: Backtrader data feed
        offset: Bar offset (0 = current bar, -1 = previous bar)

    Returns:
        The close price, or None if not available
    """
    try:
        if hasattr(data, 'close') and len(data) > abs(offset):
            return float(data.close[offset])
    except (IndexError, TypeError):
        pass
    return None


def get_current_position_size(broker, data) -> int:
    """
    Get the current position size for a data feed.

    Args:
        broker: Backtrader broker instance
        data: Backtrader data feed

    Returns:
        Position size (positive for long, negative for short, 0 for flat)
    """
    try:
        position = broker.getposition(data)
        if position:
            return int(position.size)
    except Exception as e:
        logger.warning(f"Failed to get position size: {e}")
    return 0


def safe_get_analyzer_result(
    strategy,
    analyzer_name: str,
    key: str,
    default: Any = None
) -> Any:
    """
    Safely get a result from a named analyzer.

    Args:
        strategy: Backtrader strategy instance
        analyzer_name: Name of the analyzer (as specified in _name parameter)
        key: Key to extract from analyzer results
        default: Default value if key not found

    Returns:
        The analyzer result value, or default if not available

    Examples:
        >>> result = safe_get_analyzer_result(strategy, "portfolio_value", "equity_curve", {})
    """
    try:
        if hasattr(strategy, 'analyzers'):
            analyzer = getattr(strategy.analyzers, analyzer_name, None)
            if analyzer is not None:
                analysis = analyzer.get_analysis()
                if isinstance(analysis, dict):
                    return analysis.get(key, default)
    except Exception as e:
        logger.warning(f"Failed to get analyzer result {analyzer_name}.{key}: {e}")

    return default


def get_sharpe_ratio(strategy, default: float = 0.0) -> float:
    """
    Safely extract Sharpe ratio from strategy's SharpeRatio analyzer.

    Args:
        strategy: Backtrader strategy instance
        default: Default value if Sharpe ratio not available

    Returns:
        Sharpe ratio value
    """
    try:
        if hasattr(strategy, 'analyzers') and hasattr(strategy.analyzers, 'sharpe'):
            sharpe_analysis = strategy.analyzers.sharpe.get_analysis()
            sharpe_value = sharpe_analysis.get('sharperatio', default)
            if sharpe_value is not None and not (
                isinstance(sharpe_value, float) and (sharpe_value != sharpe_value)  # NaN check
            ):
                return float(sharpe_value)
    except Exception as e:
        logger.warning(f"Failed to get Sharpe ratio: {e}")

    return default


def get_max_drawdown(strategy, default: float = 0.0) -> float:
    """
    Safely extract max drawdown from strategy's DrawDown analyzer.

    Args:
        strategy: Backtrader strategy instance
        default: Default value if drawdown not available

    Returns:
        Max drawdown as a decimal (e.g., 0.15 for 15%)
    """
    try:
        if hasattr(strategy, 'analyzers') and hasattr(strategy.analyzers, 'drawdown'):
            drawdown_analysis = strategy.analyzers.drawdown.get_analysis()
            max_dd = drawdown_analysis.get('max', {}).get('drawdown', default)
            if max_dd is not None:
                return float(max_dd) / 100.0  # Convert percentage to decimal
    except Exception as e:
        logger.warning(f"Failed to get max drawdown: {e}")

    return default


__all__ = [
    "get_data_name",
    "get_dataframe",
    "get_ticker_from_order",
    "get_ticker_from_data_mapping",
    "get_data_dates",
    "get_close_price",
    "get_current_position_size",
    "safe_get_analyzer_result",
    "get_sharpe_ratio",
    "get_max_drawdown",
]
