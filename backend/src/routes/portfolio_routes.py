"""
Portfolio Routes - API endpoints for multi-asset portfolio backtesting.

This module provides REST API endpoints for:
- Running portfolio backtests
- Listing portfolio history
- Retrieving portfolio details
"""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from src.config.settings import IMAGES_DIR
from src.routes.settings_routes import get_current_user
from src.service.portfolio_backtest import (
    run_portfolio_backtest,
    PortfolioBacktestError,
)
from src.db.portfolio_storage import get_portfolio_storage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


# Request/Response Models
class PortfolioBacktestRequest(BaseModel):
    """Request model for portfolio backtest."""
    tickers: list[str] = Field(..., description="List of ticker symbols", min_length=1)
    weights: list[float] = Field(..., description="Portfolio weights (will be normalized)")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    initial_cash: float = Field(100000.0, description="Total initial cash for portfolio")
    commission: float = Field(0.0005, description="Broker commission rate")
    stake: int = Field(100, description="Fixed stake per trade")
    strategy_name: str | None = Field(None, description="Strategy to use for all tickers")
    params: dict | None = Field(None, description="Strategy parameters")


class PortfolioHistoryQuery(BaseModel):
    """Query parameters for portfolio history."""
    sort_by: str = "created_at"
    sort_order: str = "desc"
    limit: int = 50
    offset: int = 0


@router.post("/backtest")
async def portfolio_backtest(request: PortfolioBacktestRequest, user: dict = Depends(get_current_user)):
    """
    Run a portfolio backtest with multiple tickers.
    
    - Runs backtests in parallel for each ticker
    - Combines results into portfolio-level metrics
    - Calculates correlation matrix between assets
    - Provides Markowitz optimization suggestions
    """
    try:
        # Validate inputs
        if len(request.tickers) != len(request.weights):
            raise HTTPException(
                status_code=400,
                detail="Number of tickers must match number of weights"
            )
        
        if len(request.tickers) < 1:
            raise HTTPException(
                status_code=400,
                detail="At least one ticker is required"
            )
        
        # Generate save path for portfolio chart
        import uuid
        plot_filename = f"portfolio_{uuid.uuid4()}.png"
        save_path = IMAGES_DIR / plot_filename
        
        # Run portfolio backtest
        result = run_portfolio_backtest(
            tickers=request.tickers,
            weights=request.weights,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_cash=request.initial_cash,
            commission=request.commission,
            stake=request.stake,
            strategy_name=request.strategy_name,
            params=request.params,
            save_path=save_path,
        )
        
        # Save to database
        user_id = user.get("sub") if user else None
        storage = get_portfolio_storage()
        storage.save_result(result, user_id=user_id)
        
        # Add plot URL to result
        result["plot_url"] = f"/images/{plot_filename}"
        
        return result
    
    except PortfolioBacktestError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Portfolio backtest failed: {e}")
        raise HTTPException(status_code=500, detail=f"Portfolio backtest failed: {str(e)}")


@router.get("/history")
async def get_portfolio_history(
    sort_by: str = "created_at",
    sort_order: str = "desc",
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(get_current_user)
):
    """
    List portfolio backtest history.
    
    Returns summary information for each portfolio backtest.
    """
    try:
        user_id = user.get("sub") if user else None
        storage = get_portfolio_storage()
        
        results = storage.list_history(
            user_id=user_id,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        
        return {"results": results, "count": len(results)}
    
    except Exception as e:
        logger.exception(f"Failed to fetch portfolio history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{portfolio_id}")
async def get_portfolio_detail(portfolio_id: str, user: dict = Depends(get_current_user)):
    """
    Get detailed portfolio result by ID.
    
    Includes all metrics, correlation matrix, and optimization suggestions.
    """
    try:
        user_id = user.get("sub") if user else None
        storage = get_portfolio_storage()
        
        result = storage.get_by_id(portfolio_id, user_id=user_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Portfolio result not found")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to fetch portfolio detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{portfolio_id}")
async def delete_portfolio_record(portfolio_id: str, user: dict = Depends(get_current_user)):
    """
    Delete a portfolio backtest record.
    """
    try:
        user_id = user.get("sub") if user else None
        storage = get_portfolio_storage()
        
        deleted = storage.delete_by_id(portfolio_id, user_id=user_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Portfolio result not found")
        
        return {"message": "Deleted successfully", "portfolio_id": portfolio_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete portfolio record: {e}")
        raise HTTPException(status_code=500, detail=str(e))
