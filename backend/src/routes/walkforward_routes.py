"""
Walk-Forward Optimization API Routes

Provides endpoints for:
- Creating and running walk-forward optimizations
- Listing optimization results
- Retrieving detailed optimization results
- Deleting optimizations
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from src.db import WalkForwardStorage
from src.service.walkforward_optimizer import WalkForwardOptimizer
from src.utils.auth import get_current_user, get_optional_user
from src.utils.request_context import get_request_id, set_trace_id

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize storage
storage = WalkForwardStorage()


def _get_task_storage():
    """Lazy import to avoid circular dependency."""
    from src.db.storage.task import get_task_storage
    return get_task_storage()


def _get_task_status():
    """Lazy import to avoid circular dependency."""
    from src.db.models.task import TaskStatus
    return TaskStatus


# Request/Response Models

class WalkForwardOptimizationRequest(BaseModel):
    """Request model for creating a walk-forward optimization."""
    strategy_name: str = Field(..., description="Name of the strategy to optimize")
    ticker: str = Field(..., description="Symbol to backtest")
    start_date: str = Field(..., description="Overall start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="Overall end date (YYYY-MM-DD)")
    param_grid: Dict[str, List[Any]] = Field(
        ...,
        description="Parameter grid to optimize, e.g., {'fast_period': [5, 10, 20], 'slow_period': [20, 30, 50]}"
    )
    train_period_days: int = Field(365, description="Training window size in days", ge=30)
    test_period_days: int = Field(90, description="Test window size in days", ge=7)
    anchored: bool = Field(False, description="If True, use anchored window; if False, use rolling window")
    optimization_metric: str = Field("sharpe_ratio", description="Metric to optimize (sharpe_ratio, total_return, profit_factor)")
    initial_cash: float = Field(100000.0, description="Initial cash for backtesting", gt=0)
    commission: float = Field(0.0005, description="Commission rate", ge=0)
    stake: int = Field(100, description="Position size", gt=0)


class WalkForwardOptimizationResponse(BaseModel):
    """Response model for optimization creation."""
    optimization_id: str
    status: str
    message: str
    task_id: Optional[str] = None


class WalkForwardListResponse(BaseModel):
    """Response model for listing optimizations."""
    optimizations: List[Dict[str, Any]]
    total: int


# Helper Functions

def run_optimization_task(
    optimization_id: str,
    task_id: str,
    strategy_name: str,
    ticker: str,
    start_date: str,
    end_date: str,
    param_grid: Dict[str, List[Any]],
    train_period_days: int,
    test_period_days: int,
    anchored: bool,
    optimization_metric: str,
    initial_cash: float,
    commission: float,
    stake: int,
):
    """
    Background task to run walk-forward optimization.

    Updates database with progress and results.
    """
    task_storage = _get_task_storage()
    task_status_enum = _get_task_status()

    try:
        # Update status to running
        storage.update_optimization_status(optimization_id, "running")
        task_storage.update_status(task_id, task_status_enum.RUNNING.value, progress=10)

        logger.info(f"Starting walk-forward optimization {optimization_id}")

        # Create optimizer
        optimizer = WalkForwardOptimizer(
            strategy_name=strategy_name,
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            param_grid=param_grid,
            initial_cash=initial_cash,
            commission=commission,
            stake=stake,
            train_period_days=train_period_days,
            test_period_days=test_period_days,
            anchored=anchored,
        )

        task_storage.update_status(task_id, task_status_enum.RUNNING.value, progress=30)

        # Run walk-forward analysis
        result = optimizer.run_walkforward(
            optimization_metric=optimization_metric,
            optimization_id=optimization_id,
        )

        task_storage.update_status(task_id, task_status_enum.RUNNING.value, progress=90)

        # Save results to database
        storage.save_optimization_result(result)

        # Mark task as completed
        task_storage.update_status(
            task_id, task_status_enum.COMPLETED.value,
            progress=100,
            result_id=optimization_id,
            result_type="walkforward",
        )

        logger.info(f"Walk-forward optimization {optimization_id} completed successfully")

    except Exception as e:
        logger.error(f"Walk-forward optimization {optimization_id} failed: {e}", exc_info=True)
        storage.update_optimization_status(
            optimization_id,
            "failed",
            error_message=str(e),
        )
        task_storage.update_status(
            task_id, task_status_enum.FAILED.value,
            progress=100,
            error_message=str(e),
        )


# API Endpoints

@router.post("/walkforward/start", response_model=WalkForwardOptimizationResponse)
async def start_walkforward_optimization(
    request: WalkForwardOptimizationRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_optional_user),
):
    """
    Start a new walk-forward optimization.

    The optimization runs in the background. Use the returned optimization_id
    to check status and retrieve results.

    **Parameters:**
    - **strategy_name**: Name of the strategy file (without .py extension)
    - **ticker**: Symbol to backtest (e.g., "AAPL", "BTC/USDT")
    - **start_date**: Overall start date in YYYY-MM-DD format
    - **end_date**: Overall end date in YYYY-MM-DD format
    - **param_grid**: Dictionary mapping parameter names to lists of values to test
    - **train_period_days**: Size of training window in days (default: 365)
    - **test_period_days**: Size of test window in days (default: 90)
    - **anchored**: Use anchored (True) or rolling (False) windows (default: False)
    - **optimization_metric**: Metric to optimize - sharpe_ratio, total_return, or profit_factor (default: sharpe_ratio)
    - **initial_cash**: Initial cash for backtesting (default: 100000)
    - **commission**: Commission rate (default: 0.0005)
    - **stake**: Position size (default: 100)

    **Returns:**
    - **optimization_id**: Unique ID for this optimization run
    - **status**: Current status (pending)
    - **message**: Success message

    **Example:**
    ```json
    {
      "strategy_name": "sma_cross",
      "ticker": "AAPL",
      "start_date": "2020-01-01",
      "end_date": "2023-12-31",
      "param_grid": {
        "fast_period": [5, 10, 20],
        "slow_period": [20, 30, 50]
      },
      "train_period_days": 365,
      "test_period_days": 90,
      "anchored": false,
      "optimization_metric": "sharpe_ratio"
    }
    ```
    """
    try:
        # Generate optimization ID
        optimization_id = str(uuid.uuid4())
        set_trace_id(optimization_id)  # Set trace ID for logging correlation
        
        request_id = get_request_id()
        logger.info(
            f"[{request_id}] Starting walk-forward optimization trace_id={optimization_id} "
            f"strategy={request.strategy_name} ticker={request.ticker}"
        )

        # Get user ID if authenticated
        user_id = user.get("sub") if user else None

        # Create task record
        task_storage = _get_task_storage()
        task_name = f"Walk-Forward: {request.strategy_name} on {request.ticker}"
        task_config = {
            "strategy_name": request.strategy_name,
            "ticker": request.ticker,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "param_grid": request.param_grid,
            "train_period_days": request.train_period_days,
            "test_period_days": request.test_period_days,
        }
        task = task_storage.create_task(
            task_type="walkforward",
            config=task_config,
            user_id=user_id,
            name=task_name,
        )
        task_id = task["task_id"]

        # Create optimization record in database
        storage.create_optimization(
            optimization_id=optimization_id,
            strategy_name=request.strategy_name,
            ticker=request.ticker,
            start_date=request.start_date,
            end_date=request.end_date,
            param_grid=request.param_grid,
            train_period_days=request.train_period_days,
            test_period_days=request.test_period_days,
            anchored=request.anchored,
            optimization_metric=request.optimization_metric,
            initial_cash=request.initial_cash,
            commission=request.commission,
            stake=request.stake,
            user_id=user_id,
        )

        # Start background task
        background_tasks.add_task(
            run_optimization_task,
            optimization_id=optimization_id,
            task_id=task_id,
            strategy_name=request.strategy_name,
            ticker=request.ticker,
            start_date=request.start_date,
            end_date=request.end_date,
            param_grid=request.param_grid,
            train_period_days=request.train_period_days,
            test_period_days=request.test_period_days,
            anchored=request.anchored,
            optimization_metric=request.optimization_metric,
            initial_cash=request.initial_cash,
            commission=request.commission,
            stake=request.stake,
        )

        logger.info(f"Started walk-forward optimization {optimization_id}")

        return WalkForwardOptimizationResponse(
            optimization_id=optimization_id,
            status="pending",
            message="Walk-forward optimization started successfully",
            task_id=task_id,
        )

    except Exception as e:
        logger.error(f"Failed to start walk-forward optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/walkforward/list", response_model=WalkForwardListResponse)
async def list_walkforward_optimizations(
    ticker: Optional[str] = None,
    strategy_name: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    limit: int = 100,
    offset: int = 0,
    user: dict = Depends(get_optional_user),
):
    """
    List walk-forward optimizations with optional filtering.

    **Query Parameters:**
    - **ticker**: Filter by ticker symbol (optional)
    - **strategy_name**: Filter by strategy name (optional)
    - **status**: Filter by status - pending, running, completed, failed (optional)
    - **sort_by**: Field to sort by - created_at, avg_test_performance, consistency_score (default: created_at)
    - **sort_order**: Sort order - asc or desc (default: desc)
    - **limit**: Maximum number of records to return (default: 100)
    - **offset**: Number of records to skip for pagination (default: 0)

    **Returns:**
    - **optimizations**: List of optimization records with summary data
    - **total**: Total count of matching records
    """
    try:
        user_id = user.get("sub") if user else None

        result = storage.list_optimizations(
            ticker=ticker,
            strategy_name=strategy_name,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
            user_id=user_id,
        )

        return WalkForwardListResponse(**result)

    except Exception as e:
        logger.error(f"Failed to list walk-forward optimizations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/walkforward/{optimization_id}")
async def get_walkforward_optimization(
    optimization_id: str,
    user: dict = Depends(get_optional_user),
):
    """
    Get detailed results for a specific walk-forward optimization.

    **Path Parameters:**
    - **optimization_id**: The unique optimization ID

    **Returns:**
    Detailed optimization results including:
    - Configuration parameters
    - All walk-forward windows with train/test metrics
    - Best parameters for each window
    - Overfitting detection metrics
    - Combined test performance metrics
    """
    try:
        user_id = user.get("sub") if user else None

        result = storage.get_optimization(
            optimization_id=optimization_id,
            user_id=user_id,
        )

        if not result:
            raise HTTPException(status_code=404, detail="Optimization not found")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get walk-forward optimization {optimization_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/walkforward/{optimization_id}")
async def delete_walkforward_optimization(
    optimization_id: str,
    user: dict = Depends(get_optional_user),
):
    """
    Delete a walk-forward optimization.

    **Path Parameters:**
    - **optimization_id**: The unique optimization ID

    **Returns:**
    - **message**: Success message
    """
    try:
        user_id = user.get("sub") if user else None

        success = storage.delete_optimization(
            optimization_id=optimization_id,
            user_id=user_id,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Optimization not found")

        return {"message": "Optimization deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete walk-forward optimization {optimization_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/walkforward/{optimization_id}/status")
async def get_walkforward_status(
    optimization_id: str,
    user: dict = Depends(get_optional_user),
):
    """
    Get the current status of a walk-forward optimization.

    **Path Parameters:**
    - **optimization_id**: The unique optimization ID

    **Returns:**
    - **optimization_id**: The optimization ID
    - **status**: Current status (pending, running, completed, failed)
    - **error_message**: Error message if status is failed (optional)
    - **progress**: Progress information if available (optional)
    """
    try:
        user_id = user.get("sub") if user else None

        result = storage.get_optimization(
            optimization_id=optimization_id,
            user_id=user_id,
        )

        if not result:
            raise HTTPException(status_code=404, detail="Optimization not found")

        return {
            "optimization_id": result["optimization_id"],
            "status": result["status"],
            "error_message": result.get("error_message"),
            "num_windows": result.get("num_windows", 0),
            "created_at": result.get("created_at"),
            "completed_at": result.get("completed_at"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status for walk-forward optimization {optimization_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["router"]
