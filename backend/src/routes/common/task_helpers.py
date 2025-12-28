"""
Task management helper utilities.

Provides common functions for task creation, naming, and error handling
to standardize task management across all route handlers.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException
from pydantic import BaseModel

from src.contracts.exceptions import StrategyLoadError, DataLoadError


def get_user_id(user: Optional[dict]) -> Optional[str]:
    """
    Extract user ID from authentication context.

    .. deprecated::
        This function is deprecated. Use FastAPI dependency injection instead:
        - Import: `from src.routes.common.auth_dependencies import get_optional_user_id, get_user_id`
        - Usage: `user_id: str = Depends(get_optional_user_id)` in endpoint signature
        This provides better type safety and cleaner code.

    Args:
        user: User dictionary from authentication dependency

    Returns:
        User ID string or None if not authenticated
    """
    return user.get("sub") if user else None


def generate_task_name(task_type: str, config: Dict[str, Any]) -> str:
    """
    Generate standardized task names based on type and configuration.
    
    Args:
        task_type: Type of task (backtest, portfolio, walkforward, deep_analysis)
        config: Task configuration dictionary
        
    Returns:
        Human-readable task name
        
    Examples:
        >>> generate_task_name("backtest", {"ticker": "AAPL", "strategy_name": "SMA"})
        "Backtest AAPL - SMA"
        
        >>> generate_task_name("portfolio", {"tickers": ["AAPL", "MSFT", "GOOGL", "TSLA"]})
        "Portfolio Backtest: AAPL, MSFT, GOOGL +1"
    """
    if task_type == "backtest":
        ticker = config.get("ticker", "Unknown")
        strategy = config.get("strategy_name", "Default")
        return f"Backtest {ticker} - {strategy}"
    
    elif task_type == "portfolio":
        tickers = config.get("tickers", [])
        if not tickers:
            return "Portfolio Backtest"

        # Show first 3 tickers, add "+N" for remainder
        display_tickers = ", ".join(tickers[:3])
        if len(tickers) > 3:
            display_tickers += f" +{len(tickers) - 3}"
        return f"Portfolio Backtest: {display_tickers}"

    elif task_type == "multi_asset":
        tickers = config.get("tickers", [])
        opt_method = config.get("optimization_method", "equal_weight")
        if not tickers:
            return "Multi-Asset Backtest"

        # Show first 3 tickers, add "+N" for remainder
        display_tickers = ", ".join(tickers[:3])
        if len(tickers) > 3:
            display_tickers += f" +{len(tickers) - 3}"
        return f"Multi-Asset: {display_tickers} ({opt_method})"

    elif task_type == "walkforward":
        strategy = config.get("strategy_name", "Unknown")
        ticker = config.get("ticker", "Unknown")
        return f"Walk-Forward: {strategy} on {ticker}"
    
    elif task_type == "deep_analysis":
        backtest_id = config.get("backtest_id", "Unknown")
        return f"Deep Analysis: {backtest_id}"
    
    else:
        return f"Task: {task_type}"


def create_task_config(request: BaseModel, task_type: str) -> Dict[str, Any]:
    """
    Extract relevant fields from request model for task configuration.
    
    This creates a minimal config dictionary suitable for task storage
    and execution, filtering out unnecessary fields.
    
    Args:
        request: Pydantic request model
        task_type: Type of task being created
        
    Returns:
        Configuration dictionary for task
    """
    # Convert request to dict
    config = request.model_dump(exclude_unset=True)
    
    # Task-specific filtering
    if task_type == "backtest":
        return {
            "ticker": config.get("ticker"),
            "start_date": config.get("start_date"),
            "end_date": config.get("end_date"),
            "initial_cash": config.get("initial_cash"),
            "commission": config.get("commission"),
            "stake": config.get("stake"),
            "strategy_name": config.get("strategy_name"),
            "params": config.get("params"),
            "sizer_type": config.get("sizer_type", "fixed_size"),
            "sizer_config": config.get("sizer_config"),
            "timeframe": config.get("timeframe", "1d"),
        }

    
    elif task_type == "portfolio":
        return {
            "tickers": config.get("tickers"),
            "weights": config.get("weights"),
            "start_date": config.get("start_date"),
            "end_date": config.get("end_date"),
            "initial_cash": config.get("initial_cash"),
            "commission": config.get("commission"),
            "stake": config.get("stake"),
            "strategy_name": config.get("strategy_name"),
            "params": config.get("params"),
            "sizer_type": config.get("sizer_type", "fixed_size"),
            "sizer_config": config.get("sizer_config"),
            "timeframe": config.get("timeframe", "1d"),
        }
    
    elif task_type == "multi_asset":
        return {
            "tickers": config.get("tickers"),
            "weights": config.get("weights"),
            "start_date": config.get("start_date"),
            "end_date": config.get("end_date"),
            "initial_cash": config.get("initial_cash"),
            "commission": config.get("commission"),
            "strategy_name": config.get("strategy_name"),
            "per_asset_params": config.get("per_asset_params"),
            "rebalance_config": config.get("rebalance_config"),
            "optimization_method": config.get("optimization_method", "equal_weight"),
            "timeframe": config.get("timeframe", "1d"),
        }

    elif task_type == "walkforward":
        return {
            "strategy_name": config.get("strategy_name"),
            "ticker": config.get("ticker"),
            "start_date": config.get("start_date"),
            "end_date": config.get("end_date"),
            "param_grid": config.get("param_grid"),
            "train_period_days": config.get("train_period_days"),
            "test_period_days": config.get("test_period_days"),
            "anchored": config.get("anchored"),
            "optimization_metric": config.get("optimization_metric"),
            "initial_cash": config.get("initial_cash"),
            "commission": config.get("commission"),
            "stake": config.get("stake"),
            "sizer_type": config.get("sizer_type", "fixed_size"),
            "sizer_config": config.get("sizer_config"),
            "timeframe": config.get("timeframe", "1d"),
        }

    # Default: return all fields
    return config


def map_exception_to_http(exc: Exception) -> HTTPException:
    """
    Map domain exceptions to appropriate HTTP exceptions.
    
    Provides consistent error handling and status codes across routes.
    
    Args:
        exc: Exception from service layer
        
    Returns:
        HTTPException with appropriate status code and message
    """
    # Map specific exception types to HTTP status codes
    if isinstance(exc, StrategyLoadError):
        return HTTPException(status_code=400, detail=str(exc))
    
    if isinstance(exc, DataLoadError):
        return HTTPException(status_code=502, detail=str(exc))
    
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    
    if isinstance(exc, HTTPException):
        # Already an HTTP exception, return as-is
        return exc
    
    # Default: 500 Internal Server Error
    return HTTPException(status_code=500, detail=str(exc))


__all__ = [
    "get_user_id",
    "generate_task_name",
    "create_task_config",
    "map_exception_to_http",
]
