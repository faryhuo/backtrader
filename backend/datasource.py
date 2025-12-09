import yfinance as yf
import pandas as pd
import logging
import backtrader as bt

logger = logging.getLogger(__name__)

class DataLoadError(Exception):
    """Raised when market data cannot be loaded."""

def get_data(ticker, start, end):
    """
    Download data as a pandas DataFrame.
    If unavailable (e.g., network issues or bad ticker), fall back to synthetic data.
    """
    try:
        data = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        if data is None or data.empty:
            raise DataLoadError("No data returned")
        return data
    except Exception as exc:
        # Generate a simple synthetic price series to keep the pipeline alive
        dates = pd.date_range(start=start, end=end, freq="B")
        if len(dates) == 0:
            dates = pd.date_range(end=pd.Timestamp.today(), periods=200, freq="B")
        prices = pd.Series(100.0, index=dates).cumsum()  # monotonic increasing baseline
        data = pd.DataFrame(
            {
                "Open": prices * 0.999,
                "High": prices * 1.001,
                "Low": prices * 0.999,
                "Close": prices,
                "Adj Close": prices,
                "Volume": 1_000_000,
            },
            index=dates,
        )
        logger.warning("Data download failed for %s (%s-%s); using synthetic data. Cause: %s", ticker, start, end, exc)
        return data

def get_bt_feed(ticker, start, end):
    """
    Wrapper to get data as a Backtrader feed.
    """
    data = get_data(ticker, start, end)
    return bt.feeds.PandasData(dataname=data)

def get_raw_data_json(ticker, start_date, end_date):
    """
    Fetch market data and return as a list of dictionaries for the frontend.
    """
    try:
        data = get_data(ticker, start_date, end_date)
        
        # Reset index to make Date a column if it's the index
        if 'Date' not in data.columns:
            data = data.reset_index()
            # If the index name wasn't 'Date', rename the new column
            if 'index' in data.columns and 'Date' not in data.columns:
                 data.rename(columns={'index': 'Date'}, inplace=True)

        results = []
        for _, row in data.iterrows():
            # Handle different date column names if necessary (yfinance usually 'Date')
            date_val = row.get('Date')
            if pd.isna(date_val):
                continue
                
            results.append({
                "time": date_val.strftime("%Y-%m-%d"),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]) if not pd.isna(row["Volume"]) else 0
            })
            
        return results

    except Exception as exc:
        logger.error(f"Failed to fetch raw data: {exc}")
        return []
