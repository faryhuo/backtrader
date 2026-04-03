"""
Backtest execution and history routes.

Handles:
- Running backtests
- Backtest history CRUD
- AI analysis updates
"""
import uuid
import logging

from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel

from src.config.settings import IMAGES_DIR
from src.contracts.task import TaskStatus
from src.contracts.defaults import BACKTEST_DEFAULTS
from src.service.task_manager import get_task_manager
from src.service.executors import get_executor
from src.routes.common.task_helpers import generate_task_name, create_task_config, map_exception_to_http
from src.routes.common.auth_dependencies import get_optional_user_id
from src.service.backtest_engine import (
    get_user_strategy_code,
    StrategyLoadError,
)
from src.service.deep_analysis import (
    compute_deep_analysis,
    DeepAnalysisError,
    DEFAULT_BENCHMARKS,
)
from src.service.pyfolio_exporter import (
    export_to_csv_zip,
    generate_tear_sheet_html,
    get_pyfolio_metrics,
    PyFolioExportError,
)
from src.db.storage.market_data import DataLoadError
from src.db.storage.backtest import BacktestStorage
from src.routes.common.dependencies import get_backtest_storage
from src.utils.request_context import get_request_id, set_trace_id

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== Pydantic Models ==========


class BacktestRequest(BaseModel):
    ticker: str
    data_source: str | None = None
    instrument_type: str | None = None
    start_date: str
    end_date: str
    initial_cash: float
    commission: float | None = BACKTEST_DEFAULTS.COMMISSION
    stake: int | None = BACKTEST_DEFAULTS.STAKE
    # Sizer configuration
    sizer_type: str | None = BACKTEST_DEFAULTS.SIZER_TYPE
    sizer_config: dict | None = None  # Type-specific config (percents, risk_percent, etc.)
    # Data configuration
    timeframe: str | None = BACKTEST_DEFAULTS.TIMEFRAME
    strategy_name: str | None = None
    params: dict | None = None  # Strategy parameter overrides
    generate_chart_image: bool = False


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


class PyFolioExportConfig(BaseModel):
    include_tear_sheet: bool = False  # Generate QuantStats tear sheet HTML
    benchmark_ticker: str | None = None  # Optional benchmark for comparison


# ========== Backtest Execution Endpoints ==========


@router.post("/backtest")
async def backtest(
    request: BacktestRequest,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """
    Run a backtest and return results.

    This endpoint submits a backtest task to TaskManager for execution.
    The task runs asynchronously with automatic status tracking and WebSocket updates.
    """
    
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
        
        # Submit to TaskManager using executor from registry
        task_manager = get_task_manager()
        task = await task_manager.submit(
            task_type="backtest",
            executor=get_executor("backtest"),
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
    query: BacktestHistoryQuery,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """
    List backtest history with filtering and sorting.
    """
    storage = get_backtest_storage()

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
def get_backtest_detail(
    backtest_id: str,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """
    Get detailed backtest result by ID.
    """
    storage = get_backtest_storage()

    result = storage.get_backtest(backtest_id, user_id=user_id)

    if not result:
        raise HTTPException(status_code=404, detail="Backtest not found")

    return result


@router.delete("/backtest/history/{backtest_id}")
def delete_backtest_record(
    backtest_id: str,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """
    Delete backtest history record and associated plot file.
    """
    storage = get_backtest_storage()

    deleted = storage.delete_backtest(backtest_id, user_id=user_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Backtest not found")

    return {"status": "ok", "message": "Backtest deleted"}


@router.post("/backtest/history/{backtest_id}/ai-analysis")
def update_ai_analysis(
    backtest_id: str,
    analysis: AIAnalysisUpdate,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """
    Update AI analysis for a backtest (when user runs AI analysis).
    Stores analysis in JSON format: {model_name: analysis_content}
    """
    storage = get_backtest_storage()

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
    user_id: str = Depends(get_optional_user_id),
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


# ========== PyFolio Export Endpoints ==========


@router.get("/backtest/history/{backtest_id}/pyfolio-export")
def export_pyfolio_data(
    backtest_id: str,
    user_id: str = Depends(get_optional_user_id),
) -> Response:
    """
    Export backtest data in PyFolio-compatible format as a ZIP file.

    The ZIP file contains:
    - returns.csv: Daily returns series (required for PyFolio)
    - transactions.csv: Trade transactions
    - positions.csv: Position values over time
    - metadata.json: Export metadata and usage instructions
    - README.md: Usage documentation

    Returns:
        ZIP file as attachment download
    """
    storage = get_backtest_storage()

    # Get backtest details
    backtest = storage.get_backtest(backtest_id, user_id=user_id)
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")

    # Get required data
    metrics = backtest.get("metrics", {})
    equity_curve = metrics.get("equity_curve")
    trade_details = metrics.get("trade_details", {})
    ticker = backtest.get("ticker", "UNKNOWN")
    initial_cash = backtest.get("initial_cash", 100000.0)

    if not equity_curve:
        raise HTTPException(
            status_code=400,
            detail="Equity curve data not available. Please re-run the backtest.",
        )

    try:
        # Generate ZIP file
        zip_data = export_to_csv_zip(
            equity_curve=equity_curve,
            trade_details=trade_details,
            ticker=ticker,
            backtest_id=backtest_id,
            initial_cash=initial_cash,
        )

        # Return as downloadable attachment
        filename = f"pyfolio_export_{ticker}_{backtest_id[:8]}.zip"

        return Response(
            content=zip_data,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
            },
        )

    except PyFolioExportError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to export PyFolio data for {backtest_id}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/backtest/history/{backtest_id}/pyfolio-metrics")
def get_pyfolio_style_metrics(
    backtest_id: str,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """
    Get PyFolio-style performance metrics for a backtest.

    Returns comprehensive metrics including:
    - Annual return and volatility
    - Sharpe and Sortino ratios
    - Max drawdown and Calmar ratio
    - VaR and CVaR (95%)
    - Skewness and Kurtosis
    - Win rate and total return
    """
    storage = get_backtest_storage()

    # Get backtest details
    backtest = storage.get_backtest(backtest_id, user_id=user_id)
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")

    # Get equity curve
    metrics = backtest.get("metrics", {})
    equity_curve = metrics.get("equity_curve")

    if not equity_curve:
        raise HTTPException(
            status_code=400,
            detail="Equity curve data not available.",
        )

    try:
        pyfolio_metrics = get_pyfolio_metrics(equity_curve)
        return {"status": "ok", "metrics": pyfolio_metrics}
    except Exception as e:
        logger.exception(f"Failed to compute PyFolio metrics for {backtest_id}")
        raise HTTPException(status_code=500, detail=f"Failed to compute metrics: {str(e)}")


@router.post("/backtest/history/{backtest_id}/pyfolio-tearsheet")
def generate_pyfolio_tearsheet(
    backtest_id: str,
    config: PyFolioExportConfig | None = None,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """
    Generate a PyFolio-style tear sheet report using QuantStats.

    This endpoint generates an HTML tear sheet that can be displayed
    in the frontend or downloaded.

    Args:
        backtest_id: Backtest identifier
        config: Optional configuration for the tear sheet

    Returns:
        Dict with HTML content of the tear sheet
    """
    storage = get_backtest_storage()

    # Get backtest details
    backtest = storage.get_backtest(backtest_id, user_id=user_id)
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")

    # Get required data
    metrics = backtest.get("metrics", {})
    equity_curve = metrics.get("equity_curve")
    trade_details = metrics.get("trade_details", {})
    ticker = backtest.get("ticker", "UNKNOWN")
    strategy_name = backtest.get("strategy_name", "Strategy")
    initial_cash = backtest.get("initial_cash", 100000.0)

    if not equity_curve:
        raise HTTPException(
            status_code=400,
            detail="Equity curve data not available.",
        )

    if config is None:
        config = PyFolioExportConfig()

    try:
        html_content = generate_tear_sheet_html(
            equity_curve=equity_curve,
            trade_details=trade_details,
            ticker=ticker,
            strategy_name=strategy_name,
            initial_cash=initial_cash,
            benchmark_ticker=config.benchmark_ticker,
        )

        if html_content is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate tear sheet. QuantStats may not be installed.",
            )

        return {
            "status": "ok",
            "html": html_content,
            "backtest_id": backtest_id,
            "ticker": ticker,
            "strategy_name": strategy_name,
        }

    except PyFolioExportError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to generate tear sheet for {backtest_id}")
        raise HTTPException(status_code=500, detail=f"Failed to generate tear sheet: {str(e)}")
