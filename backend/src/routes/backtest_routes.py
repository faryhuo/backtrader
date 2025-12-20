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


# ========== Backtest Execution Endpoints ==========


@router.post("/backtest")
async def backtest(request: BacktestRequest, user: dict = Depends(get_current_user)) -> dict:
    try:
        # Generate unique ID for this backtest
        backtest_id = str(uuid.uuid4())
        filename = f"{backtest_id}.png"
        save_path = IMAGES_DIR / filename

        # Get strategy code before running backtest
        strategy_code = None
        if request.strategy_name:
            try:
                strategy_code = get_user_strategy_code(request.strategy_name)
            except Exception as e:
                logger.warning(f"Failed to get strategy code for {request.strategy_name}: {e}")

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
            raise HTTPException(status_code=500, detail="Backtest failed")

        response = {
            "backtest_id": backtest_id,  # Add backtest_id to response
            "metrics": metrics,
            "plot_url": f"/images/{filename}",
        }

        # Save to database (non-blocking, errors logged but don't fail request)
        try:
            storage = get_backtest_storage()
            user_id = user.get("sub") if user else None

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
                ai_analysis=None,  # Will be updated separately if AI analysis is run
                strategy_code=strategy_code,  # Save strategy code snapshot
                user_id=user_id,
            )
        except Exception as e:
            # Log error but don't fail the backtest response
            logger.error(f"Failed to save backtest to history: {e}", exc_info=True)

        return response

    except StrategyLoadError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except DataLoadError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


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
