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
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Any

from src.config.settings import IMAGES_DIR
from src.service.task_manager import get_task_manager
from src.routes.common.task_helpers import generate_task_name, create_task_config, map_exception_to_http
from src.routes.common.auth_dependencies import get_optional_user_id
from src.service.multi_asset_backtest import (
    run_multi_asset_backtest,
    MultiAssetBacktestError,
)
from src.db import get_portfolio_storage
from src.service.strategy_repo import list_strategies

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/portfolio", tags=["portfolio"])




# Request/Response Models
class PortfolioHistoryQuery(BaseModel):
    """Query parameters for portfolio history."""
    sort_by: str = "created_at"
    sort_order: str = "desc"
    limit: int = 50
    offset: int = 0




class RebalanceConfig(BaseModel):
    """Rebalancing configuration for portfolio."""
    frequency: str = Field(
        ...,
        description="Rebalancing frequency: monthly, monthly_first, monthly_last, quarterly, annually"
    )
    min_trade_threshold: float = Field(
        0.01,
        ge=0.0,
        le=1.0,
        description="Minimum position change % to execute trade (default 1%)"
    )
    transaction_cost_pct: float = Field(
        0.001,
        ge=0.0,
        le=0.1,
        description="Transaction cost as % of trade value (default 0.1%)"
    )

    @field_validator('frequency')
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        valid_frequencies = [
            'monthly', 'monthly_first', 'monthly_last',
            'quarterly', 'quarterly_first', 'quarterly_last',
            'annually', 'annually_first', 'annually_last'
        ]
        if v not in valid_frequencies:
            raise ValueError(f"Invalid frequency '{v}'. Must be one of: {', '.join(valid_frequencies)}")
        return v


class MultiAssetBacktestRequest(BaseModel):
    """Request model for true multi-asset backtest with unified Cerebro."""
    tickers: list[str] = Field(..., description="List of ticker symbols", min_length=1, max_length=20)
    weights: list[float] = Field(..., description="Initial allocation weights (will be normalized)")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    initial_cash: float = Field(100000.0, ge=1000, le=100000000, description="Total initial cash for portfolio")
    commission: float = Field(0.0005, ge=0, le=0.1, description="Broker commission rate")
    strategy_name: str = Field(..., description="Strategy file name (required - use multi-asset template)")
    params: dict | None = Field(None, description="Strategy parameters (applied globally)")
    rebalance_config: RebalanceConfig | None = Field(
        None,
        description="Rebalancing configuration. Example: {'frequency': 'monthly', 'min_trade_threshold': 0.01}"
    )
    optimization_method: str = Field(
        "equal_weight",
        description="Optimization method for rebalancing: equal_weight, risk_parity, min_variance, markowitz"
    )
    timeframe: str = Field("1d", description="Data interval (1d, 1h, 15m, 5m, 1m)")

    @field_validator('optimization_method')
    @classmethod
    def validate_optimization_method(cls, v: str) -> str:
        valid_methods = ['equal_weight', 'risk_parity', 'min_variance', 'markowitz']
        if v not in valid_methods:
            raise ValueError(f"Invalid optimization method '{v}'. Must be one of: {', '.join(valid_methods)}")
        return v

    @field_validator('timeframe')
    @classmethod
    def validate_timeframe(cls, v: str) -> str:
        valid_timeframes = ['1d', '1h', '15m', '5m', '1m']
        if v not in valid_timeframes:
            raise ValueError(f"Invalid timeframe '{v}'. Must be one of: {', '.join(valid_timeframes)}")
        return v




async def _multi_asset_executor(config: dict, progress_callback) -> dict:
    """
    Executor function for true multi-asset backtest tasks.

    Args:
        config: Multi-asset configuration from task
        progress_callback: Callback for progress updates

    Returns:
        Dictionary with portfolio_id and results
    """
    plot_filename = f"multi_asset_{uuid.uuid4()}.png"
    save_path = IMAGES_DIR / plot_filename

    await progress_callback(10, "Starting multi-asset backtest")

    # Run multi-asset backtest in thread pool to avoid blocking event loop
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,  # Use default ThreadPoolExecutor
        partial(
            run_multi_asset_backtest,
            tickers=config["tickers"],
            weights=config["weights"],
            start_date=config["start_date"],
            end_date=config["end_date"],
            initial_cash=config.get("initial_cash", 100000.0),
            commission=config.get("commission", 0.0005),
            strategy_name=config["strategy_name"],
            params=config.get("params"),
            rebalance_config=config.get("rebalance_config"),
            optimization_method=config.get("optimization_method", "equal_weight"),
            timeframe=config.get("timeframe", "1d"),
            save_path=save_path,
        )
    )

    await progress_callback(80, "Saving multi-asset results")

    # Prepare result for database storage
    result["plot_filename"] = plot_filename
    result["strategy_name"] = config.get("strategy_name")

    # Save to database using portfolio storage
    storage = get_portfolio_storage()

    # Build storage-compatible format
    storage_result = {
        "id": str(uuid.uuid4()),  # Generate unique portfolio ID
        "tickers": result["tickers"],
        "weights": result["weights"],
        "start_date": config["start_date"],
        "end_date": config["end_date"],
        "initial_cash": result["initial_cash"],
        "commission": config.get("commission", 0.0005),
        "strategy_name": result.get("strategy_name"),
        "params": None,  # No per-asset params
        "plot_filename": plot_filename,
        # Portfolio-level metrics
        "final_value": result["final_value"],
        "total_return": result["total_return"],
        "weighted_sharpe": result["sharpe_ratio"],
        "max_drawdown": result["max_drawdown"],
        "num_assets": result["num_assets"],
        # Multi-asset specific fields
        "equity_curve": result.get("equity_curve", {}),
        "rebalancing_events": result.get("rebalancing_events", []),
        "asset_contributions": result.get("asset_contributions", {}),
        "all_trades": result.get("all_trades", []),  # Trade log from PortfolioTradeRecorder
        "rebalance_frequency": (config.get("rebalance_config") or {}).get("frequency"),
        "optimization_method": config.get("optimization_method", "equal_weight"),
        "per_asset_params": None,
        # Individual results for UI compatibility
        "individual_results": result.get("individual_results", []),
        # Correlation and optimization
        "correlation": result.get("correlation", {}),
        "optimization": result.get("optimization", {}),
        # Additional metrics
        "portfolio_metrics": result.get("metrics", {}),
    }

    portfolio_id = storage.save_result(storage_result, user_id=config.get("user_id"))

    await progress_callback(100, "Multi-asset backtest completed")

    # Add metadata to result
    result["id"] = portfolio_id
    result["portfolio_id"] = portfolio_id
    result["plot_url"] = f"/images/{plot_filename}"

    return result


@router.post("/multi-asset/backtest")
async def multi_asset_backtest(
    request: MultiAssetBacktestRequest,
    user_id: str = Depends(get_optional_user_id)
):
    """
    Run a true multi-asset portfolio backtest with unified Cerebro.

    Features:
    - Single Backtrader Cerebro instance managing multiple data feeds
    - Periodic rebalancing with multiple optimization methods
    - Unified portfolio equity curve
    - Per-asset strategy parameter configuration
    - Transaction cost tracking

    This endpoint provides true multi-asset backtesting (not parallel backtests),
    enabling portfolio-level features like rebalancing and optimization.
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

        # Submit to TaskManager
        task_manager = get_task_manager()
        task = await task_manager.submit(
            task_type="multi_asset",
            executor=_multi_asset_executor,
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
