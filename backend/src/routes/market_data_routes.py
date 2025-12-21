"""
Market data routes.

Handles:
- Ticker info and validation
- OHLCV price data fetching
- Basic analysis
"""
import logging

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.db.storage.market_data import get_raw_data_json
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


# ========== Ticker Data Endpoints ==========


@router.get("/ticker/{ticker}/info")
def get_ticker_info(ticker: str, user: dict = Depends(get_current_user)) -> dict:
    """Get ticker metadata and validation info."""
    try:
        from src.db.storage.ticker_metadata import get_ticker_metadata
        ticker_info = get_ticker_metadata(ticker)

        if not ticker_info.get('is_valid'):
            raise HTTPException(
                status_code=400,
                detail=ticker_info.get('validation_error', 'Invalid ticker symbol')
            )

        return ticker_info
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ticker/{ticker}/prices")
def get_ticker_prices(
    ticker: str,
    start_date: str,
    end_date: str,
    user: dict = Depends(get_current_user)
) -> dict:
    """Get OHLCV price data for a ticker within date range."""
    try:
        data = get_raw_data_json(ticker, start_date, end_date)
        return {"data": data}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# Legacy endpoint for backward compatibility
@router.post("/data")
def fetch_market_data(request: DataRequest, user: dict = Depends(get_current_user)) -> dict:
    try:
        # Step 1: Get ticker metadata (validates ticker)
        from src.db.storage.ticker_metadata import get_ticker_metadata
        ticker_info = get_ticker_metadata(request.ticker)

        # Step 2: Validate ticker
        if not ticker_info.get('is_valid'):
            raise HTTPException(
                status_code=400,
                detail=ticker_info.get('validation_error', 'Invalid ticker symbol')
            )

        # Step 3: Fetch OHLCV data (existing logic)
        data = get_raw_data_json(request.ticker, request.start_date, request.end_date)

        # Step 4: Return enhanced response
        return {
            "ticker_info": ticker_info,
            "data": data
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


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
