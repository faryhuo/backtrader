"""
Task Routes - REST API endpoints for task management.

Provides endpoints for:
- Listing tasks with filtering and pagination
- Getting task details
- Cancelling tasks
- Retrying failed tasks
- Deleting task records
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from src.db.models.task import TaskType, TaskStatus
from src.service.task_manager import get_task_manager
from src.utils.auth import get_current_user, get_optional_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Constants
TASK_NOT_FOUND = "Task not found"


# Request/Response Models

class TaskListQuery(BaseModel):
    """Query parameters for listing tasks."""
    task_type: Optional[str] = Field(None, description="Filter by task type (backtest, portfolio, walkforward, deep_analysis)")
    status: Optional[str] = Field(None, description="Filter by status (pending, running, completed, failed, cancelled)")
    limit: int = Field(50, ge=1, le=200, description="Maximum results to return")
    offset: int = Field(0, ge=0, description="Pagination offset")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc, desc)")


class TaskResponse(BaseModel):
    """Task response model."""
    task_id: str
    task_type: str
    status: str
    progress: int
    name: Optional[str] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    result_id: Optional[str] = None
    result_type: Optional[str] = None
    config: Optional[dict] = None
    logs: Optional[list] = None
    retry_count: int = 0


class TaskListResponse(BaseModel):
    """Response for task list endpoint."""
    tasks: list
    total: int


class TaskStatsResponse(BaseModel):
    """Response for task stats endpoint."""
    max_concurrent: int
    running_count: int
    semaphore_available: int
    pending_count: int
    completed_today: int


# Endpoints

@router.get("", response_model=TaskListResponse)
async def list_tasks(
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    user: dict = Depends(get_optional_user),
):
    """
    List tasks with optional filtering.

    **Query Parameters:**
    - **task_type**: Filter by type (backtest, portfolio, walkforward, deep_analysis)
    - **status**: Filter by status (pending, running, completed, failed, cancelled)
    - **limit**: Maximum results (default: 50, max: 200)
    - **offset**: Pagination offset
    - **sort_by**: Sort field (default: created_at)
    - **sort_order**: Sort order (asc, desc)

    **Returns:**
    - **tasks**: List of task objects
    - **total**: Total count matching filters
    """
    try:
        user_id = user.get("sub") if user else None
        manager = get_task_manager()

        # Validate task_type if provided
        if task_type and task_type not in [t.value for t in TaskType]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid task_type. Must be one of: {[t.value for t in TaskType]}"
            )

        # Validate status if provided
        if status and status not in [s.value for s in TaskStatus]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {[s.value for s in TaskStatus]}"
            )

        result = manager.list_tasks(
            user_id=user_id,
            task_type=task_type,
            status=status,
            limit=limit,
            offset=offset,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=TaskStatsResponse)
async def get_task_stats(user: dict = Depends(get_optional_user)):
    """
    Get task manager statistics.

    **Returns:**
    - **max_concurrent**: Maximum concurrent tasks allowed
    - **running_count**: Currently running tasks
    - **semaphore_available**: Available execution slots
    - **pending_count**: Tasks waiting to execute
    - **completed_today**: Tasks completed today
    """
    try:
        manager = get_task_manager()
        return manager.get_stats()
    except Exception as e:
        logger.exception(f"Failed to get task stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    user: dict = Depends(get_optional_user),
):
    """
    Get task details by ID.

    **Path Parameters:**
    - **task_id**: The unique task identifier

    **Returns:**
    Task object with full details including configuration and logs.
    """
    try:
        user_id = user.get("sub") if user else None
        manager = get_task_manager()

        task = manager.get_task(task_id, user_id)
        if not task:
            raise HTTPException(status_code=404, detail=TASK_NOT_FOUND)

        return task

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    user: dict = Depends(get_current_user),
):
    """
    Cancel a pending or running task.

    **Path Parameters:**
    - **task_id**: The unique task identifier

    **Returns:**
    - **message**: Success message
    - **task_id**: The cancelled task ID

    **Errors:**
    - 404: Task not found
    - 400: Task cannot be cancelled (already completed/failed/cancelled)
    """
    try:
        user_id = user.get("sub") if user else None
        manager = get_task_manager()

        # Check task exists
        task = manager.get_task(task_id, user_id)
        if not task:
            raise HTTPException(status_code=404, detail=TASK_NOT_FOUND)

        # Check task can be cancelled
        if task["status"] not in (TaskStatus.PENDING.value, TaskStatus.RUNNING.value):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel task with status '{task['status']}'"
            )

        cancelled = await manager.cancel(task_id, user_id)
        if not cancelled:
            raise HTTPException(status_code=400, detail="Failed to cancel task")

        return {"message": "Task cancelled", "task_id": task_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to cancel task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/retry")
async def retry_task(
    task_id: str,
    user: dict = Depends(get_current_user),
):
    """
    Retry a failed or cancelled task.

    Creates a new task with the same configuration as the original.

    **Path Parameters:**
    - **task_id**: The original task identifier

    **Returns:**
    New task object with pending status.

    **Errors:**
    - 404: Original task not found
    - 400: Task cannot be retried (not failed/cancelled)
    """
    try:
        user_id = user.get("sub") if user else None
        manager = get_task_manager()

        # Check task exists
        task = manager.get_task(task_id, user_id)
        if not task:
            raise HTTPException(status_code=404, detail=TASK_NOT_FOUND)

        # Check task can be retried
        if task["status"] not in (TaskStatus.FAILED.value, TaskStatus.CANCELLED.value):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot retry task with status '{task['status']}'. Only failed or cancelled tasks can be retried."
            )

        # Get executor for task type
        executor = _get_executor_for_task_type(task["task_type"])
        if not executor:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot retry task of type '{task['task_type']}'"
            )

        new_task = await manager.retry(task_id, executor, user_id)
        if not new_task:
            raise HTTPException(status_code=400, detail="Failed to retry task")

        return new_task

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to retry task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    force: bool = False,
    user: dict = Depends(get_current_user),
):
    """
    Delete a task record.

    Running tasks cannot be deleted unless force=true (for stuck/stale tasks).

    **Path Parameters:**
    - **task_id**: The unique task identifier

    **Query Parameters:**
    - **force**: If true, force delete even running tasks (default: false)

    **Returns:**
    - **message**: Success message
    - **task_id**: The deleted task ID

    **Errors:**
    - 404: Task not found
    - 400: Task cannot be deleted (still running)
    """
    try:
        user_id = user.get("sub") if user else None
        manager = get_task_manager()

        # Check task exists
        task = manager.get_task(task_id, user_id)
        if not task:
            raise HTTPException(status_code=404, detail=TASK_NOT_FOUND)

        # Check task is not running (unless force)
        if task["status"] == TaskStatus.RUNNING.value and not force:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete running task. Cancel it first or use force=true."
            )

        deleted = manager.delete_task(task_id, user_id, force=force)
        if not deleted:
            raise HTTPException(status_code=400, detail="Failed to delete task")

        return {"message": "Task deleted", "task_id": task_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_executor_for_task_type(task_type: str):
    """
    Get the executor function for a given task type.

    This is used when retrying tasks to execute the same operation.
    Returns None if task type is unknown or cannot be retried.
    """
    try:
        if task_type == TaskType.BACKTEST.value:
            from src.service.backtest_engine import run_backtest

            def backtest_executor(config, progress_callback):
                # run_backtest is synchronous, wrap it
                return run_backtest(
                    ticker=config.get("ticker"),
                    start_date=config.get("start_date"),
                    end_date=config.get("end_date"),
                    initial_cash=config.get("initial_cash", 100000),
                    commission=config.get("commission", 0.0005),
                    stake=config.get("stake", 100),
                    strategy_name=config.get("strategy_name"),
                    params=config.get("params"),
                )

            return backtest_executor

        elif task_type == TaskType.PORTFOLIO.value:
            from src.service.portfolio_backtest import run_portfolio_backtest

            def portfolio_executor(config, progress_callback):
                return run_portfolio_backtest(
                    tickers=config.get("tickers"),
                    weights=config.get("weights"),
                    start_date=config.get("start_date"),
                    end_date=config.get("end_date"),
                    initial_cash=config.get("initial_cash", 100000),
                    commission=config.get("commission", 0.0005),
                    stake=config.get("stake", 100),
                    strategy_name=config.get("strategy_name"),
                    params=config.get("params"),
                )

            return portfolio_executor

        elif task_type == TaskType.WALKFORWARD.value:
            from src.service.walkforward_optimizer import run_walkforward_optimization

            def walkforward_executor(config, progress_callback):
                return run_walkforward_optimization(
                    strategy_name=config.get("strategy_name"),
                    ticker=config.get("ticker"),
                    start_date=config.get("start_date"),
                    end_date=config.get("end_date"),
                    param_grid=config.get("param_grid"),
                    train_period_days=config.get("train_period_days", 180),
                    test_period_days=config.get("test_period_days", 60),
                    anchored=config.get("anchored", False),
                    optimization_metric=config.get("optimization_metric", "sharpe_ratio"),
                    initial_cash=config.get("initial_cash", 100000),
                    commission=config.get("commission", 0.0005),
                    stake=config.get("stake", 100),
                )

            return walkforward_executor

        elif task_type == TaskType.DEEP_ANALYSIS.value:
            from src.service.deep_analysis import compute_deep_analysis

            def deep_analysis_executor(config, progress_callback):
                return compute_deep_analysis(
                    backtest_id=config.get("backtest_id"),
                    benchmarks=config.get("benchmarks"),
                    rolling_window=config.get("rolling_window", 60),
                    risk_free_rate=config.get("risk_free_rate", 0.02),
                )

            return deep_analysis_executor

    except ImportError as e:
        logger.warning(f"Failed to import executor for {task_type}: {e}")

    return None


__all__ = ["router"]
