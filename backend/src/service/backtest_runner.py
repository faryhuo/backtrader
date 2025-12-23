"""
Backtest Runner.

Executes backtests via:
- Worker pool (default, isolated execution)
- Legacy in-process execution (when worker pool disabled)

This module does not manage strategy files or sandbox validation; it focuses on
execution and metric normalization.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Optional, Type

import backtrader as bt
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.db.storage.market_data import get_bt_feed as get_data

logger = logging.getLogger(__name__)


class BacktestRunnerError(Exception):
    """Raised when the backtest runner cannot execute a task."""


def run_backtest_worker(
    *,
    ticker: str,
    start_date: str,
    end_date: str,
    initial_cash: float,
    commission: float,
    stake: int,
    strategy_name: str,
    save_path: Optional[Path],
    params: Optional[dict],
) -> dict:
    """
    Run backtest in isolated worker process (secure).

    The API process NEVER executes user strategy code - all execution
    happens in the worker process.
    """
    from src.service.worker.task_models import BacktestTask, TaskStatus
    from src.service.worker.worker_pool import (
        WorkerPoolError,
        WorkerTimeoutError,
        get_worker_pool,
    )

    task = BacktestTask(
        task_id=str(uuid.uuid4()),
        strategy_name=strategy_name,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        initial_cash=initial_cash,
        commission=commission,
        stake=stake,
        params=params,
        generate_chart=save_path is not None,
        chart_save_path=str(save_path) if save_path else None,
    )

    pool = get_worker_pool()

    try:
        result = pool.submit_backtest_sync(task)
    except WorkerTimeoutError as exc:
        raise BacktestRunnerError(f"Backtest timed out: {exc}") from exc
    except WorkerPoolError as exc:
        raise BacktestRunnerError(f"Worker pool error: {exc}") from exc

    if result.status != TaskStatus.COMPLETED:
        error_msg = result.error or "Unknown error"
        raise BacktestRunnerError(f"Backtest failed: {error_msg}")

    metrics = result.metrics or {
        "final_value": result.final_value,
        "sharpe": result.sharpe_ratio,
        "drawdown": result.max_drawdown,
        "returns": result.total_return,
        "trade_details": result.trade_details,
        "equity_curve": result.equity_curve,
        "annual_returns": result.annual_returns,
    }

    return _normalize_metrics(metrics)


def run_backtest_legacy(
    *,
    ticker: str,
    start_date: str,
    end_date: str,
    initial_cash: float,
    commission: float,
    stake: int,
    strategy_cls: Type[bt.Strategy],
    trade_recorder_cls: Type[bt.Analyzer],
    save_path: Optional[Path],
    params: Optional[dict],
) -> dict:
    """
    Legacy in-process backtest execution.

    WARNING: This executes user strategy code in the API process!
    Only use when worker pool is explicitly disabled.
    """
    plt.ioff()
    plt.show = lambda *args, **kwargs: None  # Prevent local popups in API runs

    cerebro = bt.Cerebro()
    if params:
        cerebro.addstrategy(strategy_cls, **params)
    else:
        cerebro.addstrategy(strategy_cls)

    data = get_data(ticker, start_date, end_date)
    cerebro.adddata(data)

    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)
    cerebro.addsizer(bt.sizers.FixedSize, stake=stake)

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name="annual")
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
    cerebro.addanalyzer(bt.analyzers.TimeDrawDown, _name="timedraw")
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="timereturns")
    cerebro.addanalyzer(trade_recorder_cls, _name="trade_recorder")

    try:
        results = cerebro.run()
    except Exception as exc:
        logger.exception("Backtest run failed: %s", exc)
        raise
    strat = results[0]

    trade_details = strat.analyzers.trade_recorder.get_analysis()
    time_returns_raw = strat.analyzers.timereturns.get_analysis()
    equity_curve = {
        dt.strftime("%Y-%m-%d") if hasattr(dt, "strftime") else str(dt): float(ret)
        for dt, ret in time_returns_raw.items()
    }

    metrics = {
        "final_value": cerebro.broker.getvalue(),
        "sharpe": strat.analyzers.sharpe.get_analysis().get("sharperatio", None),
        "drawdown": strat.analyzers.drawdown.get_analysis().get("max", {}).get("drawdown", 0.0),
        "returns": strat.analyzers.returns.get_analysis().get("rnorm100", 0.0),
        "annual_returns": strat.analyzers.annual.get_analysis(),
        "sqn": strat.analyzers.sqn.get_analysis().get("sqn", None),
        "trades": strat.analyzers.trades.get_analysis(),
        "time_drawdown": strat.analyzers.timedraw.get_analysis(),
        "trade_details": trade_details,
        "equity_curve": equity_curve,
    }

    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            plt.ioff()
            figures = cerebro.plot(style="candlestick", iplot=False)
            first_fig = figures[0][0] if figures and figures[0] else None
            if first_fig:
                first_fig.set_size_inches(18, 10)
                first_fig.savefig(save_path, bbox_inches="tight", dpi=150)
                plt.close(first_fig)
            plt.close("all")
        except Exception as exc:
            logger.exception("Plot rendering failed: %s", exc)
            plt.close("all")
            raise RuntimeError(f"Failed to render plot: {exc}") from exc

    return _normalize_metrics(metrics)


def _normalize_metrics(metrics: dict) -> dict:
    """
    Normalize metrics keys between execution paths.

    This only adds missing keys with safe defaults and does not rename keys.
    """
    defaults = {
        "final_value": None,
        "sharpe": None,
        "drawdown": 0.0,
        "returns": 0.0,
        "annual_returns": {},
        "sqn": None,
        "trades": {},
        "time_drawdown": {},
        "trade_details": {},
        "equity_curve": {},
    }
    normalized = dict(defaults)
    normalized.update(metrics or {})
    return normalized
