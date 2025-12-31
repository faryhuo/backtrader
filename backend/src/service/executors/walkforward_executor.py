"""
Walkforward Executor - Task executor for walk-forward optimization.

This module consolidates the walk-forward optimization execution logic that was
previously in routes/walkforward_routes.py.
"""

import logging
from typing import Any, Callable, Dict

from src.contracts.defaults import BACKTEST_DEFAULTS
from src.db import WalkForwardStorage
from src.service.walkforward_optimizer import WalkForwardOptimizer
from src.service.executors import run_blocking_in_threadpool

logger = logging.getLogger(__name__)

# Module-level storage instance
_storage = WalkForwardStorage()


async def walkforward_executor(config: Dict[str, Any], progress_callback: Callable) -> Dict[str, Any]:
    """
    Executor function for walk-forward optimization tasks.
    
    Args:
        config: Walk-forward configuration from task, including:
            - optimization_id: Unique ID for this optimization
            - strategy_name: Strategy to optimize
            - ticker: Symbol to backtest
            - start_date: Overall start date
            - end_date: Overall end date
            - param_grid: Parameter combinations to test
            - train_period_days: Training window size
            - test_period_days: Test window size
            - anchored: Use anchored vs rolling windows
            - optimization_metric: Metric to optimize
            - initial_cash: Starting capital
            - commission: Commission rate
            - stake: Position size
            - sizer_type: Position sizing type
            - sizer_config: Sizer configuration
            - timeframe: Data interval
        progress_callback: Callback for progress updates
        
    Returns:
        Dictionary with optimization_id and results
    """
    optimization_id = config["optimization_id"]
    
    await progress_callback(10, "Initializing walk-forward optimizer")
    
    # Create optimizer with all configuration
    optimizer = WalkForwardOptimizer(
        strategy_name=config["strategy_name"],
        ticker=config["ticker"],
        start_date=config["start_date"],
        end_date=config["end_date"],
        param_grid=config["param_grid"],
        initial_cash=config.get("initial_cash", BACKTEST_DEFAULTS.INITIAL_CASH),
        commission=config.get("commission", BACKTEST_DEFAULTS.COMMISSION),
        stake=config.get("stake", BACKTEST_DEFAULTS.STAKE),
        train_period_days=config.get("train_period_days", BACKTEST_DEFAULTS.TRAIN_PERIOD_DAYS),
        test_period_days=config.get("test_period_days", BACKTEST_DEFAULTS.TEST_PERIOD_DAYS),
        anchored=config.get("anchored", BACKTEST_DEFAULTS.ANCHORED),
        sizer_type=config.get("sizer_type", BACKTEST_DEFAULTS.SIZER_TYPE),
        sizer_config=config.get("sizer_config"),
        timeframe=config.get("timeframe", BACKTEST_DEFAULTS.TIMEFRAME),
    )
    
    await progress_callback(30, "Running walk-forward analysis")
    
    # Run walk-forward analysis in thread pool
    result = await run_blocking_in_threadpool(
        optimizer.run_walkforward,
        optimization_metric=config.get("optimization_metric", "sharpe_ratio"),
        optimization_id=optimization_id,
    )
    
    await progress_callback(90, "Saving optimization results")
    
    # Save results to database
    _storage.save_optimization_result(result)
    
    await progress_callback(100, "Walk-forward optimization completed")
    
    return {
        "id": optimization_id,
        "optimization_id": optimization_id,
        "result": result,
    }


__all__ = ["walkforward_executor"]
