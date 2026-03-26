"""
Backtest Executor - Task executor for single-asset backtests.

This module consolidates the backtest execution logic that was previously
scattered in routes/backtest_routes.py. Provides a clean executor interface
for TaskManager.
"""

import logging
import uuid
from typing import Any, Callable, Dict

from src.config.settings import IMAGES_DIR
from src.contracts.defaults import BACKTEST_DEFAULTS
from src.db.storage.backtest import BacktestStorage
from src.routes.common.dependencies import get_backtest_storage
from src.service.backtest_engine import run_backtest, get_user_strategy_code
from src.service.executors import run_blocking_in_threadpool

logger = logging.getLogger(__name__)


async def backtest_executor(config: Dict[str, Any], progress_callback: Callable) -> Dict[str, Any]:
    """
    Executor function for backtest tasks.
    
    This function is called by TaskManager with automatic status tracking.
    
    Args:
        config: Backtest configuration from task, including:
            - ticker: Stock symbol
            - start_date: Backtest start date
            - end_date: Backtest end date
            - initial_cash: Starting capital
            - commission: Commission rate
            - stake: Position size
            - strategy_name: Strategy file name
            - params: Strategy parameters
            - sizer_type: Position sizing type
            - sizer_config: Sizer configuration
            - timeframe: Data interval
            - user_id: User identifier for storage
        progress_callback: Callback for progress updates (progress, message)
        
    Returns:
        Dictionary with backtest_id and result data:
            - id: Backtest ID
            - backtest_id: Backtest ID (alias)
            - metrics: Performance metrics
            - chart_data: Structured chart payload
            - plot_url: URL to plot image when image generation is enabled
    """
    backtest_id = str(uuid.uuid4())
    generate_chart_image = bool(config.get("generate_chart_image", False))
    filename = f"{backtest_id}.png" if generate_chart_image else None
    save_path = IMAGES_DIR / filename if filename else None
    
    await progress_callback(10, "Loading strategy")
    
    # Get strategy code for storage
    strategy_code = None
    strategy_name = config.get("strategy_name")
    if strategy_name:
        try:
            strategy_code = get_user_strategy_code(strategy_name)
        except Exception as e:
            logger.warning(f"Failed to get strategy code: {e}")
    
    await progress_callback(20, "Running backtest")
    
    # Run backtest in thread pool to avoid blocking event loop
    metrics = await run_blocking_in_threadpool(
        run_backtest,
        ticker=config["ticker"],
        start_date=config["start_date"],
        end_date=config["end_date"],
        initial_cash=config.get("initial_cash", BACKTEST_DEFAULTS.INITIAL_CASH),
        commission=config.get("commission", BACKTEST_DEFAULTS.COMMISSION),
        stake=config.get("stake", BACKTEST_DEFAULTS.STAKE),
        strategy_name=strategy_name,
        save_path=save_path,
        params=config.get("params"),
        sizer_type=config.get("sizer_type", BACKTEST_DEFAULTS.SIZER_TYPE),
        sizer_config=config.get("sizer_config"),
        timeframe=config.get("timeframe", BACKTEST_DEFAULTS.TIMEFRAME),
    )
    
    if metrics is None:
        raise ValueError("Backtest failed - no metrics returned")
    
    await progress_callback(80, "Saving results")
    
    # Save to database
    storage = get_backtest_storage()
    storage_config = {
        "ticker": config["ticker"],
        "start_date": config["start_date"],
        "end_date": config["end_date"],
        "initial_cash": config.get("initial_cash", BACKTEST_DEFAULTS.INITIAL_CASH),
        "commission": config.get("commission", BACKTEST_DEFAULTS.COMMISSION),
        "stake": config.get("stake", BACKTEST_DEFAULTS.STAKE),
        "strategy_name": strategy_name,
        "params": config.get("params"),
        "strategy_code": strategy_code,
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
        "chart_data": metrics.get("chart_data"),
        "plot_url": f"/images/{filename}" if filename else None,
    }


__all__ = ["backtest_executor"]
