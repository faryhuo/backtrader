import uuid
import logging

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.config.settings import IMAGES_DIR
from src.service.backtest_engine import (
    run_backtest,
    get_user_strategy_code,
    save_user_strategy_code,
    list_strategies,
    StrategyLoadError,
)
from src.db.datasource import get_raw_data_json, DataLoadError
from src.db.backtest_storage import BacktestStorage
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


class BacktestRequest(BaseModel):
    ticker: str
    start_date: str
    end_date: str
    initial_cash: float
    commission: float | None = 0.0005
    stake: int | None = 100
    strategy_name: str | None = None


class DataRequest(BaseModel):
    ticker: str
    start_date: str
    end_date: str


class StrategyCode(BaseModel):
    name: str
    code: str


class AnalysisRequest(BaseModel):
    metrics: dict


@router.get("/strategies")
def get_strategy_list(user: dict = Depends(get_current_user)) -> dict:
    try:
        names = list_strategies()
        return {"strategies": names}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ========== Ticker Data Endpoints (Split API) ==========

@router.get("/ticker/{ticker}/info")
def get_ticker_info(ticker: str, user: dict = Depends(get_current_user)) -> dict:
    """Get ticker metadata and validation info."""
    try:
        from src.db.datasource import get_ticker_metadata
        ticker_info = get_ticker_metadata(ticker)

        if not ticker_info.get('is_valid'):
            raise HTTPException(
                status_code=400,
                detail=ticker_info.get('validation_error', 'Invalid ticker symbol')
            )

        return ticker_info
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ticker/{ticker}/prices")
def get_ticker_prices(
    ticker: str,
    start_date: str,
    end_date: str,
    user: dict = Depends(get_current_user)
) -> dict:
    """Get OHLCV price data for a ticker within date range."""
    try:
        data = get_raw_data_json(ticker, start_date, end_date)
        return {"data": data}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# Legacy endpoint for backward compatibility
@router.post("/data")
def fetch_market_data(request: DataRequest, user: dict = Depends(get_current_user)) -> dict:
    try:
        # Step 1: Get ticker metadata (validates ticker)
        from src.db.datasource import get_ticker_metadata
        ticker_info = get_ticker_metadata(request.ticker)

        # Step 2: Validate ticker
        if not ticker_info.get('is_valid'):
            raise HTTPException(
                status_code=400,
                detail=ticker_info.get('validation_error', 'Invalid ticker symbol')
            )

        # Step 3: Fetch OHLCV data (existing logic)
        data = get_raw_data_json(request.ticker, request.start_date, request.end_date)

        # Step 4: Return enhanced response
        return {
            "ticker_info": ticker_info,
            "data": data
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


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
            import traceback

            traceback.print_exc()
            logger.error(f"Failed to save backtest to history: {e}")

        return response

    except StrategyLoadError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except DataLoadError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/strategy")
def get_strategy(name: str | None = None, user: dict = Depends(get_current_user)) -> dict:
    try:
        if not name:
            names = list_strategies()
            if not names:
                raise HTTPException(status_code=404, detail="No strategies available")
            name = names[0]
        code = get_user_strategy_code(name)
        return {"code": code, "name": name}
    except StrategyLoadError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/strategy")
def save_strategy(request: StrategyCode, user: dict = Depends(get_current_user)) -> dict:
    try:
        save_user_strategy_code(request.name, request.code)
        return {"status": "ok", "message": "Strategy saved", "name": request.name}
    except StrategyLoadError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/analyze")
def analyze_results(request: AnalysisRequest, user: dict = Depends(get_current_user)) -> dict:
    sharpe = request.metrics.get("sharpe")
    returns = request.metrics.get("returns")
    drawdown = request.metrics.get("drawdown")

    analysis = "Based on the backtest results:\n\n"

    if returns > 0:
        analysis += f"The strategy is profitable with a return of {returns:.2f}%. "
    else:
        analysis += f"The strategy resulted in a loss of {returns:.2f}%. "

    if sharpe and sharpe > 1:
        analysis += "The Sharpe Ratio indicates good risk-adjusted returns. "
    elif sharpe:
        analysis += "The Sharpe Ratio suggests potential risk volatility. "

    analysis += f"Max drawdown was {drawdown:.2f}%. "
    analysis += "Consider optimizing the moving average periods for better performance in volatile markets."

    return {"analysis": analysis}


# ========== Backtest History Endpoints ==========


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


@router.post("/backtest/history")
def get_backtest_history(
    query: BacktestHistoryQuery, user: dict = Depends(get_current_user)
) -> dict:
    """
    List backtest history with filtering and sorting.
    """
    try:
        storage = get_backtest_storage()
        user_id = user.get("sub") if user else None

        result = storage.list_backtests(
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

        return result

    except Exception as exc:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/backtest/history/{backtest_id}")
def get_backtest_detail(backtest_id: str, user: dict = Depends(get_current_user)) -> dict:
    """
    Get detailed backtest result by ID.
    """
    try:
        storage = get_backtest_storage()
        user_id = user.get("sub") if user else None

        result = storage.get_backtest(backtest_id, user_id=user_id)

        if not result:
            raise HTTPException(status_code=404, detail="Backtest not found")

        return result

    except HTTPException:
        raise
    except Exception as exc:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/backtest/history/{backtest_id}")
def delete_backtest_record(backtest_id: str, user: dict = Depends(get_current_user)) -> dict:
    """
    Delete backtest history record and associated plot file.
    """
    try:
        storage = get_backtest_storage()
        user_id = user.get("sub") if user else None

        deleted = storage.delete_backtest(backtest_id, user_id=user_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Backtest not found")

        return {"status": "ok", "message": "Backtest deleted"}

    except HTTPException:
        raise
    except Exception as exc:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/backtest/history/{backtest_id}/ai-analysis")
def update_ai_analysis(
    backtest_id: str, analysis: AIAnalysisUpdate, user: dict = Depends(get_current_user)
) -> dict:
    """
    Update AI analysis for a backtest (when user runs AI analysis).
    Stores analysis in JSON format: {model_name: analysis_content}
    """
    try:
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

    except HTTPException:
        raise
    except Exception as exc:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))
