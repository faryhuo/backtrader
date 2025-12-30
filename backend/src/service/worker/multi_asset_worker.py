"""
Multi-Asset Backtest Worker - Isolated multi-asset portfolio backtest execution.

This module runs inside the worker process and executes multi-asset portfolio
backtests in complete isolation from the API process.

IMPORTANT: User strategy code is only loaded and executed here,
NEVER in the main API process.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Configure logging for worker process
from src.utils.logger import setup_worker_logging
setup_worker_logging()
logger = logging.getLogger(__name__)


def get_memory_usage_mb() -> float:
    """Get current process memory usage in MB."""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        # psutil not available, return 0
        return 0.0
    except Exception:
        return 0.0


def execute_multi_asset_task(task: "MultiAssetBacktestTask") -> "MultiAssetBacktestResult":
    """
    Execute a multi-asset portfolio backtest task in the worker process.

    This function loads the user strategy, runs the multi-asset backtest,
    and returns serialized results with memory tracking.

    Args:
        task: MultiAssetBacktestTask with all parameters

    Returns:
        MultiAssetBacktestResult with metrics and data
    """
    from src.service.worker.task_models import MultiAssetBacktestResult, MultiAssetBacktestTask, TaskStatus

    task_id = task.task_id
    start_memory = get_memory_usage_mb()
    peak_memory = start_memory

    logger.info(
        f"Starting multi-asset backtest task {task_id}: "
        f"{len(task.tickers)} tickers, strategy={task.strategy_name}"
    )

    try:
        # Import backtrader and related modules HERE (in worker, not API process)
        import backtrader as bt
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from src.service.multi_asset_backtest import run_multi_asset_backtest

        # Disable matplotlib popups
        plt.ioff()
        plt.show = lambda *args, **kwargs: None

        # Run the multi-asset backtest
        logger.info(
            f"Running multi-asset backtest for {task.tickers} "
            f"from {task.start_date} to {task.end_date}"
        )

        result = run_multi_asset_backtest(
            tickers=task.tickers,
            weights=task.weights,
            start_date=task.start_date,
            end_date=task.end_date,
            initial_cash=task.initial_cash,
            commission=task.commission,
            strategy_name=task.strategy_name,
            timeframe=task.timeframe,
            save_path=Path(task.chart_save_path) if task.chart_save_path else None,
        )

        # Track peak memory
        current_memory = get_memory_usage_mb()
        peak_memory = max(peak_memory, current_memory)

        # Extract metrics from result
        final_value = result.get("final_value", 0.0)
        total_return = result.get("total_return", 0.0)
        sharpe_ratio = result.get("sharpe_ratio")
        max_drawdown = result.get("max_drawdown", 0.0)
        volatility = result.get("volatility")

        # Extract portfolio data
        equity_curve = result.get("equity_curve", {})
        asset_contributions = result.get("asset_contributions", {})
        optimization_history = result.get("optimization_history", [])
        per_asset_results = result.get("per_asset_results", {})

        # Chart path
        chart_path = result.get("plot_url")
        if chart_path and not chart_path.startswith("/"):
            chart_path = f"/images/{chart_path}" if chart_path else None

        logger.info(
            f"Multi-asset backtest {task_id} completed: "
            f"final_value={final_value:.2f}, return={total_return:.2f}%, "
            f"memory={peak_memory:.1f}MB"
        )

        return MultiAssetBacktestResult(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            final_value=final_value,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            volatility=volatility,
            equity_curve=equity_curve,
            asset_contributions=asset_contributions,
            optimization_history=optimization_history,
            per_asset_results=per_asset_results,
            chart_path=chart_path,
            peak_memory_mb=peak_memory,
        )

    except Exception as e:
        logger.exception(f"Multi-asset backtest {task_id} failed: {e}")
        return MultiAssetBacktestResult.error_result(task_id, str(e), type(e).__name__)


__all__ = ["execute_multi_asset_task", "get_memory_usage_mb"]
