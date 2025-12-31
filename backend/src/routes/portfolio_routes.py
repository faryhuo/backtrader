"""
Portfolio Routes - API endpoints for multi-asset portfolio backtesting.

This module provides REST API endpoints for:
- Running portfolio backtests
- Listing portfolio history
- Retrieving portfolio details
"""

import logging

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, field_validator
from typing import Any

from src.service.task_manager import get_task_manager
from src.service.executors import get_executor
from src.routes.common.task_helpers import generate_task_name, create_task_config, map_exception_to_http
from src.routes.common.auth_dependencies import get_optional_user_id
from src.service.multi_asset_backtest import MultiAssetBacktestError
from src.db import get_portfolio_storage
from src.service.strategy_repo import list_strategies
from src.contracts.defaults import BACKTEST_DEFAULTS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/portfolio", tags=["portfolio"])




# Request/Response Models
class PortfolioHistoryQuery(BaseModel):
    """Query parameters for portfolio history."""
    sort_by: str = "created_at"
    sort_order: str = "desc"
    limit: int = 50
    offset: int = 0







class MultiAssetBacktestRequest(BaseModel):
    """Request model for true multi-asset backtest with unified Cerebro."""
    tickers: list[str] = Field(..., description="List of ticker symbols", min_length=1, max_length=20)
    weights: list[float] = Field(..., description="Initial allocation weights (will be normalized)")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    initial_cash: float = Field(BACKTEST_DEFAULTS.INITIAL_CASH, ge=1000, le=100000000, description="Total initial cash for portfolio")
    commission: float = Field(BACKTEST_DEFAULTS.COMMISSION, ge=0, le=0.1, description="Broker commission rate")
    strategy_name: str = Field(..., description="Strategy file name (required - use multi-asset template)")
    params: dict | None = Field(None, description="Strategy parameters (applied globally)")
    timeframe: str = Field(BACKTEST_DEFAULTS.TIMEFRAME, description="Data interval (1d, 1h, 15m, 5m, 1m)")



    @field_validator('timeframe')
    @classmethod
    def validate_timeframe(cls, v: str) -> str:
        valid_timeframes = ['1d', '1h', '15m', '5m', '1m']
        if v not in valid_timeframes:
            raise ValueError(f"Invalid timeframe '{v}'. Must be one of: {', '.join(valid_timeframes)}")
        return v




@router.post("/multi-asset/backtest")
async def multi_asset_backtest(
    request: MultiAssetBacktestRequest,
    user_id: str = Depends(get_optional_user_id)
):
    """
    Run a true multi-asset portfolio backtest with unified Cerebro.

    Features:
    - Single Backtrader Cerebro instance managing multiple data feeds
    - Unified portfolio equity curve
    - Per-asset strategy parameter configuration
    - Transaction cost tracking

    This endpoint provides true multi-asset backtesting (not parallel backtests),
    enabling portfolio-level features and comprehensive performance tracking.
    """
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

    if len(request.tickers) > 20:
        raise HTTPException(
            status_code=400,
            detail="Maximum 20 tickers allowed (memory limit)"
        )

    # Validate strategy exists
    available_strategies = list_strategies()
    if request.strategy_name not in available_strategies:
        raise HTTPException(
            status_code=400,
            detail=f"Strategy '{request.strategy_name}' not found. Available strategies: {', '.join(available_strategies)}"
        )

    try:
        # Create task configuration
        task_config = create_task_config(request, "multi_asset")
        task_config["user_id"] = user_id
        task_config["params"] = request.params or {}

        # Generate task name
        task_name = generate_task_name("multi_asset", task_config)

        # Submit to TaskManager using executor from registry
        task_manager = get_task_manager()
        task = await task_manager.submit(
            task_type="multi_asset",
            executor=get_executor("multi_asset"),
            config=task_config,
            user_id=user_id,
            name=task_name,
        )

        return {
            "task_id": task["task_id"],
            "status": task["status"],
            "message": "Multi-asset backtest task submitted successfully",
        }

    except Exception as e:
        logger.exception(f"Multi-asset backtest submission failed: {e}")
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

    Includes all metrics, equity curve, and asset contributions.
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
