"""
Portfolio Executor - Task executor for multi-asset portfolio backtests.

This module consolidates the multi-asset backtest execution logic that was
previously in routes/portfolio_routes.py.
"""

import logging
import uuid
from typing import Any, Callable, Dict

from src.config.settings import IMAGES_DIR
from src.contracts.defaults import BACKTEST_DEFAULTS
from src.db import get_portfolio_storage
from src.service.multi_asset_backtest import run_multi_asset_backtest
from src.service.executors import run_blocking_in_threadpool

logger = logging.getLogger(__name__)


async def portfolio_executor(config: Dict[str, Any], progress_callback: Callable) -> Dict[str, Any]:
    """
    Executor function for multi-asset portfolio backtest tasks.
    
    Args:
        config: Multi-asset configuration from task, including:
            - tickers: List of ticker symbols
            - weights: Allocation weights
            - start_date: Backtest start date
            - end_date: Backtest end date
            - initial_cash: Starting capital
            - commission: Commission rate
            - strategy_name: Strategy file name
            - params: Strategy parameters
            - timeframe: Data interval
            - user_id: User identifier for storage
        progress_callback: Callback for progress updates
        
    Returns:
        Dictionary with portfolio_id and results
    """
    plot_filename = f"multi_asset_{uuid.uuid4()}.png"
    save_path = IMAGES_DIR / plot_filename
    
    await progress_callback(10, "Starting multi-asset backtest")
    
    # Run multi-asset backtest in thread pool
    result = await run_blocking_in_threadpool(
        run_multi_asset_backtest,
        tickers=config["tickers"],
        weights=config["weights"],
        start_date=config["start_date"],
        end_date=config["end_date"],
        initial_cash=config.get("initial_cash", BACKTEST_DEFAULTS.INITIAL_CASH),
        commission=config.get("commission", BACKTEST_DEFAULTS.COMMISSION),
        strategy_name=config["strategy_name"],
        params=config.get("params"),
        timeframe=config.get("timeframe", BACKTEST_DEFAULTS.TIMEFRAME),
        save_path=save_path,
    )
    
    await progress_callback(80, "Saving multi-asset results")
    
    # Prepare result for database storage
    result["plot_filename"] = plot_filename
    result["strategy_name"] = config.get("strategy_name")
    
    # Build extended metrics including all frontend-needed fields
    extended_metrics = result.get("metrics", {})
    extended_metrics.update({
        # Risk-adjusted metrics
        "sharpe_ratio": result.get("sharpe_ratio"),
        "calmar_ratio": result.get("calmar_ratio"),
        "recovery_factor": result.get("recovery_factor"),
        # Trading activity
        "total_commission": result.get("total_commission", 0.0),
        "total_volume": result.get("total_volume", 0.0),
        "total_trades": result.get("total_trades", 0),
    })
    
    # Build storage-compatible format
    storage_result = {
        "id": str(uuid.uuid4()),
        "tickers": result["tickers"],
        "weights": result["weights"],
        "start_date": config["start_date"],
        "end_date": config["end_date"],
        "initial_cash": result["initial_cash"],
        "commission": config.get("commission", BACKTEST_DEFAULTS.COMMISSION),
        "strategy_name": result.get("strategy_name"),
        "params": None,
        "plot_filename": plot_filename,
        # Portfolio-level metrics
        "final_value": result["final_value"],
        "total_return": result["total_return"],
        "weighted_sharpe": result["sharpe_ratio"],
        "max_drawdown": result["max_drawdown"],
        "num_assets": result["num_assets"],
        # Multi-asset specific fields
        "equity_curve": result.get("equity_curve", {}),
        "asset_contributions": result.get("asset_contributions", {}),
        "all_trades": result.get("all_trades", []),
        "per_asset_params": None,
        # Individual results for UI compatibility
        "individual_results": result.get("individual_results", []),
        # Extended metrics including optimization suggestions
        "portfolio_metrics": extended_metrics,
        # Optimization suggestions (optional)
        "optimization": result.get("optimization"),
        # Correlation matrix (optional)
        "correlation": result.get("correlation"),
    }
    
    # Save to database
    storage = get_portfolio_storage()
    portfolio_id = storage.save_result(storage_result, user_id=config.get("user_id"))
    
    await progress_callback(100, "Multi-asset backtest completed")
    
    # Add metadata to result
    result["id"] = portfolio_id
    result["portfolio_id"] = portfolio_id
    result["plot_url"] = f"/images/{plot_filename}"
    
    return result


__all__ = ["portfolio_executor"]
