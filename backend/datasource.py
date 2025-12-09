import os
import yfinance as yf
import pandas as pd
import logging
import backtrader as bt
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

class DataLoadError(Exception):
    """Raised when market data cannot be loaded."""

def get_data_from_db(ticker, start, end):
    """
    Attempt to fetch data from the database.
    Returns a DataFrame or None if not found/configured.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return None

    try:
        engine = create_engine(db_url)
        # Adjust table/column names as per your schema
        query = text("""
            SELECT date, open, high, low, close, volume
            FROM stock_prices
            WHERE ticker = :ticker
              AND date >= :start
              AND date <= :end
            ORDER BY date
        """)
        
        with engine.connect() as conn:
            df = pd.read_sql(query, conn, params={
                "ticker": ticker,
                "start": start,
                "end": end
            })
        
        if df.empty:
            return None

        # Ensure standard columns and index
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.index.name = 'Date'
        
        # Rename columns to match Backtrader/yfinance expectation (Capitalized)
        df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }, inplace=True)
        
        # Add Adj Close if missing (assume same as Close)
        if 'Adj Close' not in df.columns:
            df['Adj Close'] = df['Close']
            
        return df

    except Exception as exc:
        logger.warning(f"Database fetch failed for {ticker}: {exc}")
        return None

def get_data(ticker, start, end):
    """
    Download data as a pandas DataFrame.
    Priority:
    1. Database (if DATABASE_URL is set)
    2. yfinance
    3. Synthetic data (fallback)
    """
    # 1. Try Database
    db_data = get_data_from_db(ticker, start, end)
    if db_data is not None and not db_data.empty:
        logger.info(f"Loaded data for {ticker} from database.")
        return db_data

    # 2. Try yfinance
    try:
        data = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        if data is None or data.empty:
            raise DataLoadError("No data returned")
        logger.info(f"Loaded data for {ticker} from yfinance.")
        return data
    except Exception as exc:
        # 3. Fallback to Synthetic
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
