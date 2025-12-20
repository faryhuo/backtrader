"""
Backtest execution and history routes.

Handles:
- Running backtests
- Backtest history CRUD
- AI analysis updates
"""
import uuid
import logging

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.config.settings import IMAGES_DIR
from src.service.backtest_engine import (
    run_backtest,
    get_user_strategy_code,
    StrategyLoadError,
)
from src.service.deep_analysis import (
    compute_deep_analysis,
    DeepAnalysisError,
    DEFAULT_BENCHMARKS,
)
from src.db.storage.market_data import DataLoadError
from src.db.storage.backtest import BacktestStorage
from src.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize backtest storage (module-level singleton)
_backtest_storage = None


def get_backtest_storage():
    """Get or create backtest storage singleton."""
    global _backtest_storage
    if _backtest_storage is None:
        _backtest_storage = BacktestStorage()
    return _backtest_storage


def _get_task_storage():
    """Lazy import to avoid circular dependency."""
    from src.db.storage.task import get_task_storage
    return get_task_storage()


def _get_task_status():
    """Lazy import to avoid circular dependency."""
    from src.db.models.task import TaskStatus
    return TaskStatus


# ========== Pydantic Models ==========


class BacktestRequest(BaseModel):
    ticker: str
    start_date: str
    end_date: str
    initial_cash: float
    commission: float | None = 0.0005
    stake: int | None = 100
    strategy_name: str | None = None
    params: dict | None = None  # Strategy parameter overrides


class BacktestHistoryQuery(BaseModel):
    ticker: str | None = None
    strategy_name: str | None = None
    start_date: str | None = None  # Filter by run date
    end_date: str | None = None
    sort_by: str = "created_at"  # created_at, total_return, sharpe_ratio
    sort_order: str = "desc"  # asc or desc
    limit: int = 50
    offset: int = 0


class AIAnalysisUpdate(BaseModel):
    model_name: str
    analysis: str


class DeepAnalysisConfig(BaseModel):
    benchmarks: list[str] | None = None  # Default: ["SPY", "000300.SS"]
    rolling_window: int = 60
    risk_free_rate: float = 0.02


# ========== Backtest Execution Endpoints ==========


@router.post("/backtest")
async def backtest(request: BacktestRequest, user: dict = Depends(get_current_user)) -> dict:
    # Generate unique ID for this backtest
    backtest_id = str(uuid.uuid4())
    filename = f"{backtest_id}.png"
    save_path = IMAGES_DIR / filename
    user_id = user.get("sub") if user else None

    # Create task record (lazy import to avoid circular dependency)
    task_storage = _get_task_storage()
    TaskStatus = _get_task_status()

    task_name = f"Backtest {request.ticker} - {request.strategy_name or 'Default'}"
    task_config = {
        "ticker": request.ticker,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "initial_cash": request.initial_cash,
        "strategy_name": request.strategy_name,
    }
    task = task_storage.create_task(
        task_type="backtest",
        config=task_config,
        user_id=user_id,
        name=task_name,
    )
    task_id = task["task_id"]

    try:
        # Update task to running
        task_storage.update_status(task_id, TaskStatus.RUNNING.value, progress=10)

        # Get strategy code before running backtest
        strategy_code = None
        if request.strategy_name:
            try:
                strategy_code = get_user_strategy_code(request.strategy_name)
            except Exception as e:
                logger.warning(f"Failed to get strategy code for {request.strategy_name}: {e}")

        task_storage.update_status(task_id, TaskStatus.RUNNING.value, progress=20)

        metrics = run_backtest(
            ticker=request.ticker,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_cash=request.initial_cash,
            commission=request.commission if request.commission is not None else 0.0005,
            stake=request.stake if request.stake is not None else 100,
            strategy_name=request.strategy_name,
            save_path=save_path,
            params=request.params,
        )

        if metrics is None:
            task_storage.update_status(
                task_id, TaskStatus.FAILED.value,
                progress=100,
                error_message="Backtest failed - no metrics returned"
            )
            raise HTTPException(status_code=500, detail="Backtest failed")

        task_storage.update_status(task_id, TaskStatus.RUNNING.value, progress=80)

        response = {
            "backtest_id": backtest_id,
            "task_id": task_id,
            "metrics": metrics,
            "plot_url": f"/images/{filename}",
        }

        # Save to database
        try:
            storage = get_backtest_storage()

            config = {
                "ticker": request.ticker,
                "start_date": request.start_date,
                "strategy_code": strategy_code,
                "end_date": request.end_date,
                "initial_cash": request.initial_cash,
                "commission": request.commission if request.commission is not None else 0.0005,
                "stake": request.stake if request.stake is not None else 100,
                "strategy_name": request.strategy_name,
                "params": request.params,
            }

            storage.save_backtest(
                backtest_id=backtest_id,
                config=config,
                metrics=metrics,
                plot_filename=filename,
                ai_analysis=None,
                strategy_code=strategy_code,
                user_id=user_id,
            )

            # Update task to completed with result link
            task_storage.update_status(
                task_id,
                TaskStatus.COMPLETED.value,
                progress=100,
                result_id=backtest_id,
                result_type="backtest",
            )

        except Exception as e:
            logger.error(f"Failed to save backtest to history: {e}", exc_info=True)
            # Still mark task as completed since backtest ran successfully
            task_storage.update_status(task_id, TaskStatus.COMPLETED.value, progress=100)

        return response

    except StrategyLoadError as exc:
        task_storage.update_status(
            task_id, TaskStatus.FAILED.value,
            progress=100,
            error_message=str(exc)
        )
        raise HTTPException(status_code=400, detail=str(exc))
    except DataLoadError as exc:
        task_storage.update_status(
            task_id, TaskStatus.FAILED.value,
            progress=100,
            error_message=str(exc)
        )
        raise HTTPException(status_code=502, detail=str(exc))
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as exc:
        task_storage.update_status(
            task_id, TaskStatus.FAILED.value,
            progress=100,
            error_message=str(exc)
        )
        raise


# ========== Backtest History Endpoints ==========


@router.post("/backtest/history")
def get_backtest_history(
    query: BacktestHistoryQuery, user: dict = Depends(get_current_user)
) -> dict:
    """
    List backtest history with filtering and sorting.
    """
    storage = get_backtest_storage()
    user_id = user.get("sub") if user else None

    return storage.list_backtests(
        ticker=query.ticker,
        strategy_name=query.strategy_name,
        start_date=query.start_date,
        end_date=query.end_date,
        sort_by=query.sort_by,
        sort_order=query.sort_order,
        limit=query.limit,
        offset=query.offset,
        user_id=user_id,
    )


@router.get("/backtest/history/{backtest_id}")
def get_backtest_detail(backtest_id: str, user: dict = Depends(get_current_user)) -> dict:
    """
    Get detailed backtest result by ID.
    """
    storage = get_backtest_storage()
    user_id = user.get("sub") if user else None

    result = storage.get_backtest(backtest_id, user_id=user_id)

    if not result:
        raise HTTPException(status_code=404, detail="Backtest not found")

    return result


@router.delete("/backtest/history/{backtest_id}")
def delete_backtest_record(backtest_id: str, user: dict = Depends(get_current_user)) -> dict:
    """
    Delete backtest history record and associated plot file.
    """
    storage = get_backtest_storage()
    user_id = user.get("sub") if user else None

    deleted = storage.delete_backtest(backtest_id, user_id=user_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Backtest not found")

    return {"status": "ok", "message": "Backtest deleted"}


@router.post("/backtest/history/{backtest_id}/ai-analysis")
def update_ai_analysis(
    backtest_id: str, analysis: AIAnalysisUpdate, user: dict = Depends(get_current_user)
) -> dict:
    """
    Update AI analysis for a backtest (when user runs AI analysis).
    Stores analysis in JSON format: {model_name: analysis_content}
    """
    storage = get_backtest_storage()
    user_id = user.get("sub") if user else None

    updated = storage.update_ai_analysis(
        backtest_id=backtest_id,
        model_name=analysis.model_name,
        analysis_content=analysis.analysis,
        user_id=user_id
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Backtest not found")

    return {"status": "ok", "message": "AI analysis updated"}


# ========== Deep Analysis Endpoints ==========


@router.post("/backtest/history/{backtest_id}/deep-analysis")
def get_or_compute_deep_analysis(
    backtest_id: str,
    config: DeepAnalysisConfig | None = None,
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Get or compute deep analysis for a backtest.

    Deep analysis includes:
    - Monthly returns heatmap
    - Rolling Sharpe ratio (with benchmark comparison)
    - Returns distribution
    - Drawdown distribution
    - Consecutive losing periods
    - Benchmark comparison (alpha, beta, correlation)

    The analysis is computed on-demand and cached in the database.
    """
    storage = get_backtest_storage()
    user_id = user.get("sub") if user else None

    # Get backtest details
    backtest = storage.get_backtest(backtest_id, user_id=user_id)
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")

    # Check if analysis already cached
    cached_analysis = storage.get_deep_analysis(backtest_id, user_id=user_id)
    if cached_analysis:
        return {"status": "ok", **cached_analysis}

    # Get equity curve from metrics
    metrics = backtest.get("metrics", {})
    equity_curve = metrics.get("equity_curve")

    if not equity_curve:
        raise HTTPException(
            status_code=400,
            detail="Equity curve data not available. Please re-run the backtest to generate deep analysis data.",
        )

    # Parse config
    if config is None:
        config = DeepAnalysisConfig()

    benchmarks = config.benchmarks if config.benchmarks else DEFAULT_BENCHMARKS

    try:
        # Convert string date keys back to proper format for analysis
        from datetime import datetime

        equity_curve_parsed = {}
        for date_str, ret in equity_curve.items():
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                equity_curve_parsed[date_obj] = ret
            except ValueError:
                continue

        # Compute deep analysis
        analysis = compute_deep_analysis(
            equity_curve=equity_curve_parsed,
            start_date=backtest.get("start_date"),
            end_date=backtest.get("end_date"),
            initial_cash=backtest.get("initial_cash", 100000.0),
            benchmarks=benchmarks,
            risk_free_rate=config.risk_free_rate,
            rolling_window=config.rolling_window,
        )

        # Cache in database
        storage.update_deep_analysis(backtest_id, analysis, user_id=user_id)

        return {"status": "ok", **analysis}

    except DeepAnalysisError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to compute deep analysis for {backtest_id}")
        raise HTTPException(status_code=500, detail=f"Failed to compute analysis: {str(e)}")
