"""
EODHD Data - Functions for fetching market data from EODHD API.

Provides data loading from EODHD as an alternative data source.
"""

import logging
from datetime import datetime
from typing import Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)

# EODHD API base URL
EODHD_API_URL = "https://eodhd.com/api"


class EODHDError(Exception):
    """Raised when EODHD API request fails."""
    pass


def fetch_from_eodhd(
    ticker: str,
    start: str,
    end: str,
    api_key: str,
) -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV data from EODHD API.

    Args:
        ticker: Symbol ticker (e.g., 'AAPL.US' for US stocks)
        start: Start date string (YYYY-MM-DD)
        end: End date string (YYYY-MM-DD)
        api_key: EODHD API key

    Returns:
        pd.DataFrame: DataFrame with OHLCV data matching yfinance format,
                     or None if fetch fails

    Note:
        EODHD uses exchange suffixes:
        - US stocks: AAPL.US
        - UK stocks: BP.LSE
        - A-shares: 600519.SHG (Shanghai), 000001.SHE (Shenzhen)
    """
    if not api_key:
        logger.warning("EODHD API key not configured")
        return None

    # Normalize ticker format for EODHD
    # If no exchange suffix, assume US stock
    if '.' not in ticker:
        eodhd_ticker = f"{ticker}.US"
    else:
        eodhd_ticker = ticker

    url = f"{EODHD_API_URL}/eod/{eodhd_ticker}"
    params = {
        "api_token": api_key,
        "from": start,
        "to": end,
        "fmt": "json",
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        if not data or isinstance(data, dict) and data.get("error"):
            error_msg = data.get("error", "No data returned") if isinstance(data, dict) else "Empty response"
            logger.warning(f"EODHD returned error for {ticker}: {error_msg}")
            return None

        # Convert to DataFrame
        df = pd.DataFrame(data)

        if df.empty:
            logger.warning(f"EODHD returned empty data for {ticker}")
            return None

        # Rename columns to match yfinance format
        column_mapping = {
            "date": "Date",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "adjusted_close": "Adj Close",
            "volume": "Volume",
        }

        df = df.rename(columns=column_mapping)

        # Ensure required columns exist
        required_cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
        for col in required_cols:
            if col not in df.columns:
                logger.warning(f"EODHD missing column {col} for {ticker}")
                return None

        # Set Date as index
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        df.index.name = "Date"

        # Ensure Adj Close exists
        if "Adj Close" not in df.columns:
            df["Adj Close"] = df["Close"]

        # Convert to float
        for col in ["Open", "High", "Low", "Close", "Adj Close", "Volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        logger.info(f"Loaded {len(df)} records from EODHD for {ticker}")
        return df

    except requests.exceptions.Timeout:
        logger.warning(f"EODHD request timeout for {ticker}")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"EODHD request failed for {ticker}: {e}")
        return None
    except Exception as e:
        logger.error(f"EODHD unexpected error for {ticker}: {e}")
        return None


__all__ = [
    "EODHDError",
    "fetch_from_eodhd",
]
