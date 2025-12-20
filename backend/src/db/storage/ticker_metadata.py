"""
Ticker Metadata - Functions for fetching and caching ticker information.

Provides ticker validation and metadata retrieval from yfinance with database caching.
"""

import logging
from datetime import datetime
from typing import Optional

import yfinance as yf

from src.config.settings import DATABASE_URL, DEFAULT_DB_URL
from src.db.models import TickerMetadataModel, init_database

logger = logging.getLogger(__name__)

# Use default local database if DATABASE_URL is not configured
_DB_URL = DATABASE_URL or DEFAULT_DB_URL


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


__all__ = [
    "_validate_ticker_info",
    "_parse_ticker_info",
    "get_ticker_metadata",
]
