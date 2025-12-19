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

        df['_date'] = pd.to_datetime(df[date_col], errors='coerce').dt.strftime('%Y-%m-%d')
        df = df.dropna(subset=['_date'])
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

        df['_open'] = _num(df[open_col]) if open_col else 0.0
        df['_high'] = _num(df[high_col]) if high_col else 0.0
        df['_low'] = _num(df[low_col]) if low_col else 0.0
        df['_close'] = _num(df[close_col]) if close_col else 0.0
        df['_volume'] = _num(df[volume_col]) if volume_col else 0.0
        if adj_close_col:
            df['_adj_close'] = _num(df[adj_close_col])
        else:
            df['_adj_close'] = df['_close']

        now = datetime.utcnow()
        records = [
            {
                "ticker": ticker,
                "date": row._date,
                "open": float(row._open),
                "high": float(row._high),
                "low": float(row._low),
                "close": float(row._close),
                "volume": float(row._volume),
                "adj_close": float(row._adj_close),
                "source": source,
                "created_at": now,
                "updated_at": now,
            }
            for row in df[['_date', '_open', '_high', '_low', '_close', '_volume', '_adj_close']].itertuples(index=False)
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


# ==================== Ticker Metadata Functions ====================

def _validate_ticker_info(info: dict) -> tuple[bool, str | None]:
    """
    Validate yfinance ticker info to determine if ticker is valid.

    Args:
        info: yfinance Ticker.info dict

    Returns:
        tuple: (is_valid: bool, error_message: str | None)

    Validation criteria:
    - info must not be empty
    - Must have at least one of: longName, shortName, symbol
    - Must have at least one price field: currentPrice, regularMarketPrice, previousClose
    """
    if not info:
        return False, "No data returned from yfinance"

    # Check for essential fields
    has_name = any([
        info.get('longName'),
        info.get('shortName'),
        info.get('symbol')
    ])

    has_price = any([
        info.get('currentPrice'),
        info.get('regularMarketPrice'),
        info.get('previousClose')
    ])

    if not has_name:
        return False, "Ticker symbol not recognized"

    if not has_price:
        return False, "No price data available for this ticker"

    return True, None


def _parse_ticker_info(ticker: str, info: dict, is_valid: bool, error_msg: str | None) -> dict:
    """
    Parse yfinance info dict to our standardized format.

    Args:
        ticker: Symbol ticker
        info: yfinance Ticker.info dict
        is_valid: Validation result
        error_msg: Validation error message

    Returns:
        dict: Standardized metadata dict matching TickerMetadataModel
    """
    return {
        'ticker': ticker.upper(),
        'is_valid': is_valid,
        'validation_error': error_msg,

        # Company Basics
        'long_name': info.get('longName'),
        'short_name': info.get('shortName'),
        'sector': info.get('sector'),
        'industry': info.get('industry'),
        'country': info.get('country'),
        'website': info.get('website'),
        'long_business_summary': info.get('longBusinessSummary'),

        # Market Metrics
        'market_cap': info.get('marketCap'),
        'trailing_pe': info.get('trailingPE'),
        'forward_pe': info.get('forwardPE'),
        'price_to_book': info.get('priceToBook'),
        'beta': info.get('beta'),
        'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
        'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
        'fifty_two_week_change_percent': info.get('52WeekChange'),

        # Trading Statistics
        'current_price': info.get('currentPrice') or info.get('regularMarketPrice'),
        'previous_close': info.get('previousClose') or info.get('regularMarketPreviousClose'),
        'regular_market_open': info.get('regularMarketOpen'),
        'day_low': info.get('dayLow') or info.get('regularMarketDayLow'),
        'day_high': info.get('dayHigh') or info.get('regularMarketDayHigh'),
        'regular_market_volume': info.get('regularMarketVolume'),
        'average_volume': info.get('averageVolume'),
        'average_volume_10days': info.get('averageVolume10days'),

        # Fundamental Data
        'dividend_rate': info.get('dividendRate'),
        'dividend_yield': info.get('dividendYield'),
        'trailing_eps': info.get('trailingEps'),
        'forward_eps': info.get('forwardEps'),
        'revenue_per_share': info.get('revenuePerShare'),
        'profit_margins': info.get('profitMargins'),

        # Additional info (store overflow fields)
        'additional_info': {
            'exchange': info.get('exchange'),
            'exchange_name': info.get('fullExchangeName'),
            'currency': info.get('currency'),
            'quote_type': info.get('quoteType'),
        },

        # Cache metadata
        'source': 'yfinance',
        'cached': False,  # Fresh fetch
        'cache_age_days': 0
    }


def _save_ticker_metadata(session, metadata_dict: dict) -> bool:
    """
    Save or update ticker metadata in database (upsert).

    Args:
        session: SQLAlchemy session
        metadata_dict: Parsed metadata dict

    Returns:
        bool: True if saved successfully
    """
    from src.db.models import TickerMetadataModel

    try:
        ticker = metadata_dict['ticker']

        # Check if exists
        existing = session.query(TickerMetadataModel).filter_by(ticker=ticker).first()

        if existing:
            # Update existing record
            for key, value in metadata_dict.items():
                if key not in ['cached', 'cache_age_days']:  # Skip computed fields
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            logger.info(f"Updated ticker metadata for {ticker}")
        else:
            # Create new record
            metadata = TickerMetadataModel(**{
                k: v for k, v in metadata_dict.items()
                if k not in ['cached', 'cache_age_days']
            })
            session.add(metadata)
            logger.info(f"Created new ticker metadata for {ticker}")

        session.commit()
        return True

    except Exception as exc:
        logger.error(f"Failed to save ticker metadata: {exc}")
        session.rollback()
        return False


def _ticker_metadata_to_dict(model) -> dict:
    """
    Convert TickerMetadataModel to dict for API response.

    Args:
        model: TickerMetadataModel instance

    Returns:
        dict: Metadata dict with computed fields
    """
    cache_age = (datetime.utcnow() - model.updated_at).days if model.updated_at else None

    return {
        'ticker': model.ticker,
        'is_valid': bool(model.is_valid),
        'validation_error': model.validation_error,

        # Company Basics
        'long_name': model.long_name,
        'short_name': model.short_name,
        'sector': model.sector,
        'industry': model.industry,
        'country': model.country,
        'website': model.website,
        'long_business_summary': model.long_business_summary,

        # Market Metrics
        'market_cap': model.market_cap,
        'trailing_pe': model.trailing_pe,
        'forward_pe': model.forward_pe,
        'price_to_book': model.price_to_book,
        'beta': model.beta,
        'fifty_two_week_high': model.fifty_two_week_high,
        'fifty_two_week_low': model.fifty_two_week_low,
        'fifty_two_week_change_percent': model.fifty_two_week_change_percent,

        # Trading Statistics
        'current_price': model.current_price,
        'previous_close': model.previous_close,
        'regular_market_open': model.regular_market_open,
        'day_low': model.day_low,
        'day_high': model.day_high,
        'regular_market_volume': model.regular_market_volume,
        'average_volume': model.average_volume,
        'average_volume_10days': model.average_volume_10days,

        # Fundamental Data
        'dividend_rate': model.dividend_rate,
        'dividend_yield': model.dividend_yield,
        'trailing_eps': model.trailing_eps,
        'forward_eps': model.forward_eps,
        'revenue_per_share': model.revenue_per_share,
        'profit_margins': model.profit_margins,

        # Additional info
        'additional_info': model.additional_info,

        # Cache metadata
        'cached': True,
        'cache_age_days': cache_age
    }


def get_ticker_metadata(ticker: str, force_refresh: bool = False) -> dict:
    """
    Fetch ticker metadata from cache or yfinance.

    Args:
        ticker: Symbol ticker (e.g., 'AAPL')
        force_refresh: Force fresh fetch even if cached

    Returns:
        dict: Ticker metadata with all fields

    Flow:
    1. Check database cache
    2. If cache hit and not stale (unless force_refresh), return cached
    3. If cache miss or stale, fetch from yfinance
    4. Validate ticker (check if info is populated)
    5. Save to database
    6. Return metadata dict
    """
    from src.db.models import TickerMetadataModel

    try:
        # Initialize database
        _, SessionLocal = init_database(_DB_URL)
        session = SessionLocal()

        # Step 1: Check cache
        cached = session.query(TickerMetadataModel).filter_by(ticker=ticker.upper()).first()

        if cached and not force_refresh:
            # Check if cache is stale
            if not cached.is_stale():
                logger.info(f"Loaded ticker metadata for {ticker} from cache (age: {(datetime.utcnow() - cached.updated_at).days} days)")
                result = _ticker_metadata_to_dict(cached)
                session.close()
                return result
            else:
                logger.info(f"Cache for {ticker} is stale, refreshing...")

        # Step 2: Fetch from yfinance
        logger.info(f"Fetching fresh ticker metadata for {ticker} from yfinance")
        yf_ticker = yf.Ticker(ticker)
        info = yf_ticker.info

        # Step 3: Validate ticker
        is_valid, error_msg = _validate_ticker_info(info)

        # Step 4: Save to database (upsert pattern)
        metadata_dict = _parse_ticker_info(ticker, info, is_valid, error_msg)
        _save_ticker_metadata(session, metadata_dict)

        session.close()
        return metadata_dict

    except Exception as exc:
        logger.error(f"Failed to fetch ticker metadata for {ticker}: {exc}")
        # Return invalid ticker response
        return {
            'ticker': ticker.upper(),
            'is_valid': False,
            'validation_error': f"Failed to fetch ticker data: {str(exc)}",
            'cached': False
        }
