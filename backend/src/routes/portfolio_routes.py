"""
Portfolio Routes - API endpoints for multi-asset portfolio backtesting.

This module provides REST API endpoints for:
- Running portfolio backtests
- Listing portfolio history
- Retrieving portfolio details
"""

import asyncio
import logging
import uuid
from functools import partial
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from src.config.settings import IMAGES_DIR
from src.service.task_manager import get_task_manager
from src.routes.common.task_helpers import generate_task_name, create_task_config, map_exception_to_http
from src.routes.common.auth_dependencies import get_optional_user_id
from src.service.portfolio_backtest import (
    run_portfolio_backtest,
    PortfolioBacktestError,
)
from src.db import get_portfolio_storage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/portfolio", tags=["portfolio"])





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


async def _portfolio_executor(config: dict, progress_callback) -> dict:
    """
    Executor function for portfolio backtest tasks.
    
    Args:
        config: Portfolio configuration from task
        progress_callback: Callback for progress updates
        
    Returns:
        Dictionary with portfolio_id and results
    """
    plot_filename = f"portfolio_{uuid.uuid4()}.png"
    save_path = IMAGES_DIR / plot_filename
    
    await progress_callback(10, "Starting portfolio backtest")
    
    # Run portfolio backtest in thread pool to avoid blocking event loop
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,  # Use default ThreadPoolExecutor
        partial(
            run_portfolio_backtest,
            tickers=config["tickers"],
            weights=config["weights"],
            start_date=config["start_date"],
            end_date=config["end_date"],
            initial_cash=config.get("initial_cash", 100000.0),
            commission=config.get("commission", 0.0005),
            stake=config.get("stake", 100),
            strategy_name=config.get("strategy_name"),
            params=config.get("params"),
            save_path=save_path,
        )
    )
    
    await progress_callback(80, "Saving portfolio results")
    
    # Save to database
    result["plot_filename"] = plot_filename
    storage = get_portfolio_storage()
    portfolio_id = storage.save_result(result, user_id=config.get("user_id"))
    
    await progress_callback(100, "Portfolio backtest completed")
    
    # Add additional metadata to result
    result["id"] = portfolio_id
    result["portfolio_id"] = portfolio_id
    result["plot_url"] = f"/images/{plot_filename}"
    
    return result


@router.post("/backtest")
async def portfolio_backtest(request: PortfolioBacktestRequest, user_id: str = Depends(get_optional_user_id)):
    """
    Run a portfolio backtest with multiple tickers.
    
    - Runs backtests in parallel for each ticker
    - Combines results into portfolio-level metrics
    - Calculates correlation matrix between assets
    - Provides Markowitz optimization suggestions
    """
    # Validate inputs first
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

    try:
        # Create task configuration
        task_config = create_task_config(request, "portfolio")
        task_config["user_id"] = user_id
        
        # Generate task name
        task_name = generate_task_name("portfolio", task_config)
        
        # Submit to TaskManager
        task_manager = get_task_manager()
        task = await task_manager.submit(
            task_type="portfolio",
            executor=_portfolio_executor,
            config=task_config,
            user_id=user_id,
            name=task_name,
        )
        
        return {
            "task_id": task["task_id"],
            "status": task["status"],
            "message": "Portfolio backtest task submitted successfully",
        }
    
    except Exception as e:
        logger.exception(f"Portfolio backtest submission failed: {e}")
        http_exc = map_exception_to_http(e)
        raise http_exc


@router.get("/history")
async def get_portfolio_history(
    sort_by: str = "created_at",
    sort_order: str = "desc",
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(get_optional_user_id)
):
    """
    List portfolio backtest history.
    
    Returns summary information for each portfolio backtest.
    """
    try:
        
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
async def get_portfolio_detail(portfolio_id: str, user_id: str = Depends(get_optional_user_id)):
    """
    Get detailed portfolio result by ID.
    
    Includes all metrics, correlation matrix, and optimization suggestions.
    """
    try:
        
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
async def delete_portfolio_record(portfolio_id: str, user_id: str = Depends(get_optional_user_id)):
    """
    Delete a portfolio backtest record.
    """
    try:
        
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
