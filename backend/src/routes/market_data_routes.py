"""
Market data routes.

Handles:
- Ticker info and validation
- OHLCV price data fetching
- Basic analysis
- Cache management (stats, warmup, cleanup)
- OHLCV resampling
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from src.db.storage.market_data import get_raw_data_json
from src.db.storage.data_cache import get_data_cache_storage
from src.db.storage.resampler import (
    resample_ohlcv,
    get_supported_timeframes,
    get_resample_targets,
    validate_resample_path,
)
from src.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== Pydantic Models ==========


class DataRequest(BaseModel):
    ticker: str
    start_date: str
    end_date: str


class AnalysisRequest(BaseModel):
    metrics: dict


class WarmupRequest(BaseModel):
    """Request body for data warmup."""
    tickers: List[str] = Field(..., description="List of ticker symbols to warmup")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")


class ResampleRequest(BaseModel):
    """Request body for data resampling."""
    ticker: str = Field(..., description="Ticker symbol")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    target_timeframe: str = Field(..., description="Target timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)")
    include_incomplete: bool = Field(default=False, description="Include incomplete final interval")


# ========== Ticker Data Endpoints ==========


@router.get("/ticker/{ticker}/info")
def get_ticker_info(ticker: str, user: dict = Depends(get_current_user)) -> dict:
    """Get ticker metadata and validation info."""
    from src.db.storage.ticker_metadata import get_ticker_metadata
    from src.utils.exception_handlers import TickerValidationError
    
    ticker_info = get_ticker_metadata(ticker)

    if not ticker_info.get('is_valid'):
        raise TickerValidationError(
            ticker_info.get('validation_error', 'Invalid ticker symbol')
        )

    return ticker_info


@router.get("/ticker/{ticker}/prices")
def get_ticker_prices(
    ticker: str,
    start_date: str,
    end_date: str,
    user: dict = Depends(get_current_user)
) -> dict:
    """Get OHLCV price data for a ticker within date range."""
    data = get_raw_data_json(ticker, start_date, end_date)
    return {"data": data}


# Legacy endpoint for backward compatibility
@router.post("/data")
def fetch_market_data(request: DataRequest, user: dict = Depends(get_current_user)) -> dict:
    from src.db.storage.ticker_metadata import get_ticker_metadata
    from src.utils.exception_handlers import TickerValidationError
    
    # Step 1: Get ticker metadata (validates ticker)
    ticker_info = get_ticker_metadata(request.ticker)

    # Step 2: Validate ticker
    if not ticker_info.get('is_valid'):
        raise TickerValidationError(
            ticker_info.get('validation_error', 'Invalid ticker symbol')
        )

    # Step 3: Fetch OHLCV data (existing logic)
    data = get_raw_data_json(request.ticker, request.start_date, request.end_date)

    # Step 4: Return enhanced response
    return {
        "ticker_info": ticker_info,
        "data": data
    }


# ========== Cache Management Endpoints ==========


@router.get("/cache/stats")
def get_cache_stats(user: dict = Depends(get_current_user)) -> dict:
    """
    Get cache statistics.
    
    Returns overall cache stats including total tickers, records,
    date ranges, and per-ticker summaries.
    """
    storage = get_data_cache_storage()
    return storage.get_cache_stats()


@router.get("/cache/tickers")
def get_cached_tickers(user: dict = Depends(get_current_user)) -> dict:
    """Get list of all cached ticker symbols."""
    storage = get_data_cache_storage()
    tickers = storage.get_all_cached_tickers()
    return {"tickers": tickers, "count": len(tickers)}


@router.get("/cache/{ticker}")
def get_ticker_cache_info(
    ticker: str,
    user: dict = Depends(get_current_user)
) -> dict:
    """
    Get cache information for a specific ticker.
    
    Returns record count, date range, and last updated timestamp.
    """
    from src.utils.exception_handlers import DataNotFoundError
    
    storage = get_data_cache_storage()
    info = storage.get_ticker_cache_info(ticker)
    
    if not info:
        raise DataNotFoundError(f"No cached data found for ticker: {ticker}")
    
    return info


@router.post("/cache/warmup")
def warmup_cache(
    request: WarmupRequest,
    user: dict = Depends(get_current_user)
) -> dict:
    """
    Batch warmup data for multiple tickers.
    
    Fetches and caches OHLCV data for the specified tickers and date range.
    Returns warmup results including success/failure counts and cache hit rate.
    """
    storage = get_data_cache_storage()
    result = storage.warmup_data(
        tickers=request.tickers,
        start_date=request.start_date,
        end_date=request.end_date,
    )
    return result


@router.delete("/cache/cleanup")
def cleanup_cache(
    before_date: Optional[str] = Query(None, description="Delete data before this date (YYYY-MM-DD)"),
    tickers: Optional[str] = Query(None, description="Comma-separated list of tickers to clean"),
    older_than_days: Optional[int] = Query(None, description="Delete data older than N days"),
    user: dict = Depends(get_current_user)
) -> dict:
    """
    Clean up cached data.
    
    Specify at least one filter: before_date, tickers, or older_than_days.
    Returns the number of deleted records and affected tickers.
    """
    from src.routes.common.error_utils import require_filter
    
    # Require at least one filter to prevent accidental deletion of all data
    require_filter(
        before_date, tickers, older_than_days,
        message="At least one filter (before_date, tickers, or older_than_days) is required"
    )
    
    storage = get_data_cache_storage()
    ticker_list = tickers.split(",") if tickers else None
    
    result = storage.cleanup_cache(
        before_date=before_date,
        tickers=ticker_list,
        older_than_days=older_than_days,
    )
    return result


@router.delete("/cache/{ticker}")
def delete_ticker_cache(
    ticker: str,
    user: dict = Depends(get_current_user)
) -> dict:
    """Delete all cached data for a specific ticker."""
    from src.utils.exception_handlers import DataNotFoundError
    
    storage = get_data_cache_storage()
    deleted = storage.delete_ticker_cache(ticker)
    
    if not deleted:
        raise DataNotFoundError(f"No cached data found for ticker: {ticker}")
    
    return {"message": f"Deleted cache for {ticker}", "deleted": True}


# ========== Resample Endpoints ==========


@router.get("/resample/timeframes")
def get_timeframes(user: dict = Depends(get_current_user)) -> dict:
    """
    Get supported timeframes for resampling.
    
    Returns list of supported timeframes in order from smallest to largest.
    """
    return {
        "timeframes": get_supported_timeframes(),
    }


@router.get("/resample/targets/{source_timeframe}")
def get_valid_targets(
    source_timeframe: str,
    user: dict = Depends(get_current_user)
) -> dict:
    """
    Get valid target timeframes for a given source timeframe.
    
    Only upsampling (aggregation) is supported, so returns timeframes
    that are the same size or larger than the source.
    """
    targets = get_resample_targets(source_timeframe)
    if not targets:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source timeframe: {source_timeframe}"
        )
    
    return {
        "source": source_timeframe,
        "valid_targets": targets,
    }


@router.post("/resample")
def resample_data(
    request: ResampleRequest,
    user: dict = Depends(get_current_user)
) -> dict:
    """
    Resample OHLCV data to a target timeframe.
    
    Aggregates data from the current (or detected) timeframe to the
    target timeframe using standard OHLCV aggregation rules:
    - Open: first value in interval
    - High: max value in interval
    - Low: min value in interval
    - Close: last value in interval
    - Volume: sum of values in interval
    """
    from src.db.storage.market_data import get_data
    from src.utils.exception_handlers import DataNotFoundError, ValidationError
    
    # Fetch source data
    df = get_data(request.ticker, request.start_date, request.end_date)
    
    if df is None or df.empty:
        raise DataNotFoundError(f"No data found for {request.ticker}")
    
    # Perform resampling (ValueError will be converted to ValidationError by global handler)
    try:
        resampled = resample_ohlcv(
            df,
            target_timeframe=request.target_timeframe,
            include_incomplete=request.include_incomplete,
        )
    except ValueError as ve:
        raise ValidationError(str(ve))
    
    # Convert to JSON-serializable format
    resampled = resampled.reset_index()
    
    # Rename index column if needed
    if "Date" not in resampled.columns and "date" not in resampled.columns:
        if resampled.columns[0] in ["index", "level_0"]:
            resampled = resampled.rename(columns={resampled.columns[0]: "Date"})
    
    date_col = "Date" if "Date" in resampled.columns else "date"
    
    data = []
    for _, row in resampled.iterrows():
        date_val = row.get(date_col)
        if hasattr(date_val, "strftime"):
            date_str = date_val.strftime("%Y-%m-%d %H:%M:%S")
        else:
            date_str = str(date_val)
        
        data.append({
            "time": date_str,
            "open": float(row.get("Open", row.get("open", 0))),
            "high": float(row.get("High", row.get("high", 0))),
            "low": float(row.get("Low", row.get("low", 0))),
            "close": float(row.get("Close", row.get("close", 0))),
            "volume": int(row.get("Volume", row.get("volume", 0))),
        })
    
    return {
        "ticker": request.ticker,
        "timeframe": request.target_timeframe,
        "record_count": len(data),
        "data": data,
    }


# ========== Analysis Endpoints ==========


@router.post("/analyze")
def analyze_results(request: AnalysisRequest, user: dict = Depends(get_current_user)) -> dict:
    sharpe = request.metrics.get("sharpe")
    returns = request.metrics.get("returns")
    drawdown = request.metrics.get("drawdown")

    analysis = "Based on the backtest results:\n\n"

    if returns > 0:
        analysis += f"The strategy is profitable with a return of {returns:.2f}%. "
    else:
        analysis += f"The strategy resulted in a loss of {returns:.2f}%. "

    if sharpe and sharpe > 1:
        analysis += "The Sharpe Ratio indicates good risk-adjusted returns. "
    elif sharpe:
        analysis += "The Sharpe Ratio suggests potential risk volatility. "

    analysis += f"Max drawdown was {drawdown:.2f}%. "
    analysis += "Consider optimizing the moving average periods for better performance in volatile markets."

    return {"analysis": analysis}

