"""
Ticker Metadata - Functions for fetching and caching ticker information.

Provides ticker validation, cached metadata retrieval, and lightweight
instrument catalog search for UI pickers.
"""

import logging
from datetime import datetime
from typing import Optional

import yfinance as yf
from sqlalchemy import or_

from src.config.settings import DATABASE_URL, DEFAULT_DB_URL
from src.db.models import TickerMetadataModel, init_database

logger = logging.getLogger(__name__)

# Use default local database if DATABASE_URL is not configured
_DB_URL = DATABASE_URL or DEFAULT_DB_URL

INSTRUMENT_TYPE_QUOTE_TYPE_MAP = {
    "stock": {"equity"},
    "etf": {"etf"},
    "index": {"index"},
    "forex": {"currency"},
    "crypto": {"cryptocurrency", "crypto"},
    "futures": {"future"},
    "fund": {"mutualfund", "fund"},
}


def _normalize_quote_type(quote_type: str | None) -> str | None:
    normalized = str(quote_type or "").strip().lower()
    return normalized or None


def _matches_instrument_type(quote_type: str | None, instrument_type: str | None) -> bool:
    normalized_type = (instrument_type or "").strip().lower()
    if not normalized_type or normalized_type == "all":
        return True

    normalized_quote_type = _normalize_quote_type(quote_type)
    return bool(normalized_quote_type and normalized_quote_type in INSTRUMENT_TYPE_QUOTE_TYPE_MAP.get(normalized_type, set()))


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


def search_instrument_catalog(
    query: str = "",
    instrument_type: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """
    Search cached ticker metadata for instrument picker suggestions.

    The cache is populated from Yahoo Finance metadata, so this function is best
    effort only. It intentionally returns a compact UI-focused payload.
    """
    _, SessionLocal = init_database(_DB_URL)
    session = SessionLocal()
    normalized_query = (query or "").strip().upper()
    normalized_type = (instrument_type or "").strip().lower() or None
    matched_quote_types = INSTRUMENT_TYPE_QUOTE_TYPE_MAP.get(normalized_type)

    try:
        db_query = session.query(TickerMetadataModel).filter(
            TickerMetadataModel.is_valid == 1
        )

        if normalized_query:
            like_query = f"%{normalized_query}%"
            db_query = db_query.filter(
                or_(
                    TickerMetadataModel.ticker.ilike(like_query),
                    TickerMetadataModel.long_name.ilike(like_query),
                    TickerMetadataModel.short_name.ilike(like_query),
                )
            )

        candidates = (
            db_query.order_by(TickerMetadataModel.updated_at.desc())
            .limit(max(limit * 5, 50))
            .all()
        )

        results: list[dict] = []
        for item in candidates:
            additional_info = item.additional_info or {}
            quote_type = str(additional_info.get("quote_type") or "").strip().lower()
            if matched_quote_types and quote_type not in matched_quote_types:
                continue

            results.append({
                "code": item.ticker,
                "label": item.long_name or item.short_name or item.ticker,
                "instrument_type": normalized_type or quote_type or "unknown",
                "exchange": additional_info.get("exchange_name") or additional_info.get("exchange"),
                "currency": additional_info.get("currency"),
                "quote_type": quote_type or None,
                "source": item.source,
            })

            if len(results) >= limit:
                break

        return results
    finally:
        session.close()


def search_yahoo_instruments(
    query: str,
    instrument_type: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """
    Search Yahoo Finance directly for instrument suggestions.
    """
    normalized_query = (query or "").strip()
    if not normalized_query:
        return []

    try:
        search = yf.Search(
            normalized_query,
            max_results=max(limit * 3, 20),
            news_count=0,
            lists_count=0,
            recommended=0,
            include_research=False,
            include_nav_links=False,
            raise_errors=False,
        )
        quotes = getattr(search, "quotes", None) or []
    except Exception as exc:
        logger.warning(f"Yahoo instrument search failed for '{normalized_query}': {exc}")
        return []

    results: list[dict] = []
    for item in quotes:
        symbol = item.get("symbol")
        if not symbol:
            continue

        quote_type = _normalize_quote_type(item.get("quoteType") or item.get("typeDisp"))
        if not _matches_instrument_type(quote_type, instrument_type):
            continue

        results.append({
            "code": symbol,
            "label": item.get("shortname") or item.get("longname") or item.get("dispSecIndFlag") or symbol,
            "instrument_type": (instrument_type or quote_type or "unknown"),
            "exchange": item.get("exchange") or item.get("exchDisp"),
            "currency": item.get("currency"),
            "quote_type": quote_type,
            "source": "yahoo",
        })

        if len(results) >= limit:
            break

    return results


__all__ = [
    "_validate_ticker_info",
    "_parse_ticker_info",
    "get_ticker_metadata",
    "search_instrument_catalog",
    "search_yahoo_instruments",
]
