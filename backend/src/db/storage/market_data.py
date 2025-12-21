"""
Market Data - Functions for fetching and storing market OHLCV data.

Provides data loading from yfinance with database caching.
"""

import logging
from datetime import datetime
from typing import Optional

import backtrader as bt
import pandas as pd
import yfinance as yf
from sqlalchemy import text, select

from src.config.settings import DATABASE_URL, DEFAULT_DB_URL
from src.db.models import MarketDataModel, init_database

logger = logging.getLogger(__name__)

# Use default local database if DATABASE_URL is not configured
_DB_URL = DATABASE_URL or DEFAULT_DB_URL

_ENGINE = None
_SESSION_LOCAL = None


def _get_engine_and_session():
    global _ENGINE, _SESSION_LOCAL
    if _ENGINE is None or _SESSION_LOCAL is None:
        _ENGINE, _SESSION_LOCAL = init_database(_DB_URL)
    return _ENGINE, _SESSION_LOCAL


class DataLoadError(Exception):
    """Raised when market data cannot be loaded."""


def save_to_db(ticker: str, data: pd.DataFrame, source: str = "yfinance") -> bool:
    """
    Save market data to database.

    Args:
        ticker: Symbol ticker
        data: DataFrame with OHLCV data (must have Date index)
        source: Data source name (default: yfinance)

    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        _, SessionLocal = _get_engine_and_session()
        session = SessionLocal()

        df = data.copy()
        if df.index.name == 'Date' or ('Date' not in df.columns and 'date' not in df.columns):
            df = df.reset_index()

        date_col = 'Date' if 'Date' in df.columns else ('date' if 'date' in df.columns else None)
        if date_col is None:
            raise ValueError("Missing Date/date column in data")

        # Use 'tmp_' prefix instead of '_' prefix for temp columns
        # because pandas itertuples() cannot create named attributes for underscore-prefixed names
        df['tmp_date'] = pd.to_datetime(df[date_col], errors='coerce').dt.strftime('%Y-%m-%d')
        df = df.dropna(subset=['tmp_date'])
        if df.empty:
            session.close()
            return False

        def _pick_col(*names: str) -> Optional[str]:
            for name in names:
                if name in df.columns:
                    return name
            return None

        open_col = _pick_col('Open', 'open')
        high_col = _pick_col('High', 'high')
        low_col = _pick_col('Low', 'low')
        close_col = _pick_col('Close', 'close')
        volume_col = _pick_col('Volume', 'volume')
        adj_close_col = _pick_col('Adj Close', 'adj_close', 'AdjClose', 'adjclose')

        def _num(series: pd.Series) -> pd.Series:
            return pd.to_numeric(series, errors='coerce').fillna(0.0)

        df['tmp_open'] = _num(df[open_col]) if open_col else 0.0
        df['tmp_high'] = _num(df[high_col]) if high_col else 0.0
        df['tmp_low'] = _num(df[low_col]) if low_col else 0.0
        df['tmp_close'] = _num(df[close_col]) if close_col else 0.0
        df['tmp_volume'] = _num(df[volume_col]) if volume_col else 0.0
        if adj_close_col:
            df['tmp_adj_close'] = _num(df[adj_close_col])
        else:
            df['tmp_adj_close'] = df['tmp_close']

        now = datetime.utcnow()
        records = [
            {
                "ticker": ticker,
                "date": row.tmp_date,
                "open": float(row.tmp_open),
                "high": float(row.tmp_high),
                "low": float(row.tmp_low),
                "close": float(row.tmp_close),
                "volume": float(row.tmp_volume),
                "adj_close": float(row.tmp_adj_close),
                "source": source,
                "created_at": now,
                "updated_at": now,
            }
            for row in df[['tmp_date', 'tmp_open', 'tmp_high', 'tmp_low', 'tmp_close', 'tmp_volume', 'tmp_adj_close']].itertuples(index=False)
        ]

        dialect_name = session.get_bind().dialect.name
        if dialect_name == "sqlite":
            from sqlalchemy.dialects.sqlite import insert as sqlite_insert

            stmt = sqlite_insert(MarketDataModel.__table__).on_conflict_do_nothing(
                index_elements=["ticker", "date"]
            )
            with session.begin():
                result = session.execute(stmt, records)
            saved_count = result.rowcount if result.rowcount is not None and result.rowcount >= 0 else len(records)
            skipped_count = max(0, len(records) - saved_count)
        else:
            min_date = df['_date'].min()
            max_date = df['_date'].max()
            with session.begin():
                existing_dates = {
                    date for (date,) in session.execute(
                        select(MarketDataModel.date).where(
                            MarketDataModel.ticker == ticker,
                            MarketDataModel.date >= min_date,
                            MarketDataModel.date <= max_date,
                        )
                    ).all()
                }
                new_records = [r for r in records if r["date"] not in existing_dates]
                skipped_count = len(records) - len(new_records)
                if new_records:
                    session.execute(MarketDataModel.__table__.insert(), new_records)
                    saved_count = len(new_records)
                else:
                    saved_count = 0

        logger.info(f"Saved {saved_count} records to DB for {ticker} (skipped {skipped_count} existing)")
        session.close()

        return saved_count > 0

    except Exception as exc:
        logger.error(f"Failed to save data to database for {ticker}: {exc}")
        return False


def get_data_from_db(ticker: str, start: str, end: str) -> Optional[pd.DataFrame]:
    """
    Attempt to fetch data from the database.
    Returns a DataFrame or None if not found/configured.
    """
    try:
        engine, _ = _get_engine_and_session()
        # Query from new market_data table
        query = text("""
            SELECT date, open, high, low, close, volume, adj_close
            FROM market_data
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
            'volume': 'Volume',
            'adj_close': 'Adj Close'
        }, inplace=True)

        # Add Adj Close if missing (assume same as Close)
        if 'Adj Close' not in df.columns or df['Adj Close'].isna().all():
            df['Adj Close'] = df['Close']

        logger.info(f"Loaded {len(df)} records from database for {ticker}")
        return df

    except Exception as exc:
        logger.warning(f"Database fetch failed for {ticker}: {exc}")
        return None


def get_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    """
    Download data as a pandas DataFrame.
    """

    data = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    if data is None or data.empty:
        db_data = get_data_from_db(ticker, start, end)
        if db_data is not None and not db_data.empty:
            logger.info(f"Loaded data for {ticker} from database.")
            return db_data
        else:
            raise DataLoadError("No data returned")

    logger.info(f"Loaded data for {ticker} from yfinance.")

    # Save to database for future use
    save_to_db(ticker, data, source="yfinance")

    return data


def get_bt_feed(ticker: str, start: str, end: str) -> bt.feeds.PandasData:
    """
    Wrapper to get data as a Backtrader feed.
    """
    data = get_data(ticker, start, end)
    return bt.feeds.PandasData(dataname=data)


def get_raw_data_json(ticker: str, start_date: str, end_date: str):
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


__all__ = [
    "DataLoadError",
    "save_to_db",
    "get_data_from_db",
    "get_data",
    "get_bt_feed",
    "get_raw_data_json",
]
