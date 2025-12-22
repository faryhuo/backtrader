"""
OHLCV Resampler - Resample market data to different timeframes.

Supports downsampling (aggregating) from lower to higher timeframes:
- 1m → 5m → 15m → 30m → 1h → 4h → 1d → 1w

Data Consistency Strategy:
1. Aggregation Rules:
   - Open: First value in the interval
   - High: Maximum value in the interval
   - Low: Minimum value in the interval
   - Close: Last value in the interval
   - Volume: Sum of all values in the interval

2. Boundary Alignment:
   - Hour bars: Aligned to HH:00:00
   - Day bars: Aligned to 00:00:00 UTC (or specified timezone)
   - Week bars: Aligned to Monday

3. Incomplete Interval Handling:
   - Default: Drop incomplete intervals
   - Optional: Include incomplete with `include_incomplete=True`

4. Timezone:
   - Input data should have timezone-aware or UTC DatetimeIndex
   - Output preserves input timezone
"""

import logging
from typing import Literal, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# Supported timeframes
TimeFrame = Literal["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]

# Mapping from timeframe string to pandas resample rule
RESAMPLE_RULES: dict[str, str] = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1h": "1h",
    "4h": "4h",
    "1d": "1D",
    "1w": "1W-MON",  # Week starting Monday
}

# Timeframe ordering (smaller to larger)
TIMEFRAME_ORDER: list[str] = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]

# Minutes per timeframe (for validation)
TIMEFRAME_MINUTES: dict[str, int] = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
    "1w": 10080,
}


def validate_resample_path(source: str, target: str) -> bool:
    """
    Validate that resampling path is valid (only upsampling allowed).
    
    Args:
        source: Source timeframe (e.g., "1m")
        target: Target timeframe (e.g., "1h")
    
    Returns:
        True if valid (target >= source), False otherwise
    """
    if source not in TIMEFRAME_MINUTES or target not in TIMEFRAME_MINUTES:
        return False
    
    return TIMEFRAME_MINUTES[target] >= TIMEFRAME_MINUTES[source]


def get_timeframe_minutes(timeframe: str) -> int:
    """Get the number of minutes in a timeframe."""
    return TIMEFRAME_MINUTES.get(timeframe, 1)


def resample_ohlcv(
    df: pd.DataFrame,
    target_timeframe: str,
    source_timeframe: Optional[str] = None,
    include_incomplete: bool = False,
) -> pd.DataFrame:
    """
    Resample OHLCV data to a target timeframe.
    
    Args:
        df: DataFrame with OHLCV data and DatetimeIndex
        target_timeframe: Target timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
        source_timeframe: Source timeframe for validation (optional)
        include_incomplete: Include incomplete final interval
    
    Returns:
        Resampled DataFrame
    
    Raises:
        ValueError: If target timeframe is invalid or smaller than source
    
    Example:
        >>> df = get_data("AAPL", "2024-01-01", "2024-01-31")  # 1m data
        >>> df_hourly = resample_ohlcv(df, "1h")
        >>> df_daily = resample_ohlcv(df, "1d")
    """
    # Validate target timeframe
    if target_timeframe not in RESAMPLE_RULES:
        raise ValueError(
            f"Invalid target timeframe '{target_timeframe}'. "
            f"Supported: {', '.join(RESAMPLE_RULES.keys())}"
        )
    
    # Validate source timeframe if provided
    if source_timeframe:
        if not validate_resample_path(source_timeframe, target_timeframe):
            raise ValueError(
                f"Cannot resample from {source_timeframe} to {target_timeframe}. "
                "Only upsampling (aggregation) is supported."
            )
    
    # Ensure DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        # Try to convert
        if "Date" in df.columns:
            df = df.set_index("Date")
        elif "date" in df.columns:
            df = df.set_index("date")
        df.index = pd.to_datetime(df.index)
    
    # Normalize column names to lowercase
    df = df.copy()
    df.columns = df.columns.str.lower()
    
    # Ensure required columns exist
    required = ["open", "high", "low", "close", "volume"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Get resample rule
    rule = RESAMPLE_RULES[target_timeframe]
    
    # Define aggregation rules
    agg_dict = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }
    
    # Add adj_close if present
    if "adj close" in df.columns:
        df = df.rename(columns={"adj close": "adj_close"})
    if "adj_close" in df.columns:
        agg_dict["adj_close"] = "last"
    
    # Perform resampling
    # Use closed='left', label='left' for standard OHLCV convention
    resampled = df.resample(rule, closed="left", label="left").agg(agg_dict)
    
    # Drop incomplete final interval if requested
    # An interval is considered incomplete if the last data point doesn't reach
    # close to the end of the interval (within one source interval)
    if not include_incomplete and len(resampled) > 0:
        last_resampled_ts = resampled.index[-1]
        last_source_ts = df.index.max()
        expected_end = _get_interval_end(last_resampled_ts, target_timeframe)
        
        # Estimate source interval from actual data
        if len(df) > 1:
            source_interval = (df.index[1] - df.index[0]).total_seconds() / 60
        else:
            source_interval = 1  # Default to 1 minute
        
        # Consider complete if last source bar is within one source interval of expected end
        # This handles the case where 09:00-09:59 (60 1-min bars) forms a complete hour
        tolerance = pd.Timedelta(minutes=source_interval)
        if last_source_ts + tolerance < expected_end:
            # Last interval is incomplete, drop it
            resampled = resampled.iloc[:-1]
    
    # Drop rows with NaN (incomplete intervals at the start or gaps)
    resampled = resampled.dropna(subset=["open", "close"])
    
    # Restore capitalized column names for consistency
    resampled.columns = resampled.columns.str.title()
    resampled = resampled.rename(columns={
        "Adj_Close": "Adj Close",
    })
    
    logger.info(
        f"Resampled {len(df)} bars to {len(resampled)} {target_timeframe} bars"
    )
    
    return resampled


def _get_interval_end(timestamp: pd.Timestamp, timeframe: str) -> pd.Timestamp:
    """
    Calculate the expected end of an interval given its start.
    
    Args:
        timestamp: Start of the interval
        timeframe: Timeframe string
    
    Returns:
        Expected end timestamp of the interval
    """
    minutes = TIMEFRAME_MINUTES.get(timeframe, 1)
    return timestamp + pd.Timedelta(minutes=minutes)


def resample_to_daily(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convenience function to resample any timeframe to daily.
    
    Args:
        df: OHLCV DataFrame with DatetimeIndex
    
    Returns:
        Daily OHLCV DataFrame
    """
    return resample_ohlcv(df, "1d")


def resample_to_hourly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convenience function to resample any timeframe to hourly.
    
    Args:
        df: OHLCV DataFrame with DatetimeIndex
    
    Returns:
        Hourly OHLCV DataFrame
    """
    return resample_ohlcv(df, "1h")


def get_supported_timeframes() -> list[str]:
    """Get list of supported timeframes in order."""
    return TIMEFRAME_ORDER.copy()


def get_resample_targets(source_timeframe: str) -> list[str]:
    """
    Get valid target timeframes for a given source.
    
    Args:
        source_timeframe: Source timeframe
    
    Returns:
        List of valid target timeframes (same or larger)
    """
    if source_timeframe not in TIMEFRAME_ORDER:
        return []
    
    source_idx = TIMEFRAME_ORDER.index(source_timeframe)
    return TIMEFRAME_ORDER[source_idx:]


__all__ = [
    "TimeFrame",
    "RESAMPLE_RULES",
    "TIMEFRAME_ORDER",
    "TIMEFRAME_MINUTES",
    "validate_resample_path",
    "get_timeframe_minutes",
    "resample_ohlcv",
    "resample_to_daily",
    "resample_to_hourly",
    "get_supported_timeframes",
    "get_resample_targets",
]
