import os
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backtest_engine import (
    run_backtest,
    get_user_strategy_code,
    save_user_strategy_code,
    list_strategies,
    StrategyLoadError,
    DataLoadError,
    IMAGE_DIR,
)


router = APIRouter()


class BacktestRequest(BaseModel):
    ticker: str
    start_date: str
    end_date: str
    initial_cash: float
    commission: float | None = 0.0005
    stake: int | None = 100
    strategy_name: str | None = None


class StrategyCode(BaseModel):
    name: str
    code: str


class AnalysisRequest(BaseModel):
    metrics: dict


@router.get("/strategies")
def get_strategy_list():
    try:
        names = list_strategies()
        return {"strategies": names}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/backtest")
async def backtest(request: BacktestRequest):
    try:
        filename = f"{uuid.uuid4()}.png"
        save_path = os.path.join(IMAGE_DIR, filename)

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

        return {
            "metrics": metrics,
            "plot_url": f"/images/{filename}",
        }
    except StrategyLoadError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except DataLoadError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/strategy")
def get_strategy(name: str | None = None):
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
def save_strategy(request: StrategyCode):
    try:
        save_user_strategy_code(request.name, request.code)
        return {"status": "ok", "message": "Strategy saved", "name": request.name}
    except StrategyLoadError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/analyze")
def analyze_results(request: AnalysisRequest):
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
