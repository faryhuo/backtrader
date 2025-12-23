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
from src.service.task_manager import get_task_manager
from src.routes.common.task_helpers import get_user_id, generate_task_name, create_task_config, map_exception_to_http
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
from src.utils.request_context import get_request_id, set_trace_id

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


async def _backtest_executor(config: dict, progress_callback) -> dict:
    """
    Executor function for backtest tasks.
    
    This function is called by TaskManager with automatic status tracking.
    
    Args:
        config: Backtest configuration from task
        progress_callback: Callback for progress updates (progress, message)
        
    Returns:
        Dictionary with backtest_id and result data
    """
    backtest_id = str(uuid.uuid4())
    filename = f"{backtest_id}.png"
    save_path = IMAGES_DIR / filename
    
    await progress_callback(10, "Loading strategy")
    
    # Get strategy code
    strategy_code = None
    if config.get("strategy_name"):
        try:
            strategy_code = get_user_strategy_code(config["strategy_name"])
        except Exception as e:
            logger.warning(f"Failed to get strategy code: {e}")
    
    await progress_callback(20, "Running backtest")
    
    # Run backtest
    metrics = run_backtest(
        ticker=config["ticker"],
        start_date=config["start_date"],
        end_date=config["end_date"],
        initial_cash=config.get("initial_cash", 100000.0),
        commission=config.get("commission", 0.0005),
        stake=config.get("stake", 100),
        strategy_name=config.get("strategy_name"),
        save_path=save_path,
        params=config.get("params"),
    )
    
    if metrics is None:
        raise ValueError("Backtest failed - no metrics returned")
    
    await progress_callback(80, "Saving results")
    
    # Save to database
    storage = get_backtest_storage()
    storage_config = {
        "ticker": config["ticker"],
        "start_date": config["start_date"],
        "strategy_code": strategy_code,
        "end_date": config["end_date"],
        "initial_cash": config.get("initial_cash", 100000.0),
        "commission": config.get("commission", 0.0005),
        "stake": config.get("stake", 100),
        "strategy_name": config.get("strategy_name"),
        "params": config.get("params"),
    }
    
    storage.save_backtest(
        backtest_id=backtest_id,
        config=storage_config,
        metrics=metrics,
        plot_filename=filename,
        ai_analysis=None,
        strategy_code=strategy_code,
        user_id=config.get("user_id"),
    )
    
    await progress_callback(100, "Backtest completed")
    
    return {
        "id": backtest_id,
        "backtest_id": backtest_id,
        "metrics": metrics,
        "plot_url": f"/images/{filename}",
    }


@router.post("/backtest")
async def backtest(request: BacktestRequest, user: dict = Depends(get_current_user)) -> dict:
    """
    Run a backtest and return results.
    
    This endpoint submits a backtest task to TaskManager for execution.
    The task runs asynchronously with automatic status tracking and WebSocket updates.
    """
    user_id = get_user_id(user)
    
    # Generate trace ID for logging
    trace_id = str(uuid.uuid4())
    set_trace_id(trace_id)
    
    request_id = get_request_id()
    logger.info(
        f"[{request_id}] Submitting backtest: ticker={request.ticker} strategy={request.strategy_name}"
    )
    
    try:
        # Create task configuration
        task_config = create_task_config(request, "backtest")
        task_config["user_id"] = user_id  # Add user_id for storage
        
        # Generate task name
        task_name = generate_task_name("backtest", task_config)
        
        # Submit to TaskManager
        task_manager = get_task_manager()
        task = await task_manager.submit(
            task_type="backtest",
            executor=_backtest_executor,
            config=task_config,
            user_id=user_id,
            name=task_name,
        )
        
        logger.info(f"[{request_id}] Backtest task submitted: {task['task_id']}")
        
        return {
            "task_id": task["task_id"],
            "status": task["status"],
            "message": "Backtest task submitted successfully",
        }
    
    except Exception as exc:
        logger.exception(f"Failed to submit backtest: {exc}")
        http_exc = map_exception_to_http(exc)
        raise http_exc


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
