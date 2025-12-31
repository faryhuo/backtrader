"""
Executor Registry - Centralized task executor management.

This module provides:
- ExecutorRegistry: Central registry mapping task_type to executor functions
- run_blocking_in_threadpool: Utility for running sync functions without blocking event loop
- Common executor interfaces and utilities

Usage:
    from src.service.executors import get_executor, run_blocking_in_threadpool
    
    # Get executor by type
    executor = get_executor("backtest")
    
    # Run blocking function in threadpool
    result = await run_blocking_in_threadpool(my_sync_function, arg1, arg2, kwarg=value)
"""

import asyncio
import logging
from functools import partial
from typing import Any, Callable, Dict, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def run_blocking_in_threadpool(
    func: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    """
    Run a blocking/sync function in the default thread pool executor.
    
    This utility replaces the scattered pattern:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, partial(func, *args, **kwargs))
    
    Args:
        func: Synchronous callable to execute
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func
        
    Returns:
        Result from func execution
        
    Example:
        result = await run_blocking_in_threadpool(
            run_backtest,
            ticker="AAPL",
            start_date="2020-01-01",
            end_date="2023-12-31",
        )
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,  # Use default ThreadPoolExecutor
        partial(func, *args, **kwargs),
    )


# Registry of task_type -> executor function
_EXECUTOR_REGISTRY: Dict[str, Callable] = {}


def register_executor(task_type: str, executor: Callable) -> None:
    """
    Register an executor function for a task type.
    
    Args:
        task_type: Type identifier (e.g., "backtest", "portfolio", "walkforward")
        executor: Async callable with signature (config: dict, progress_callback) -> dict
    """
    _EXECUTOR_REGISTRY[task_type] = executor
    logger.debug(f"Registered executor for task_type={task_type}")


def get_executor(task_type: str) -> Optional[Callable]:
    """
    Get the executor function for a task type.
    
    Args:
        task_type: Type identifier
        
    Returns:
        Executor function or None if not registered
        
    Raises:
        KeyError: If task_type is not registered
    """
    if task_type not in _EXECUTOR_REGISTRY:
        raise KeyError(f"No executor registered for task_type={task_type}")
    return _EXECUTOR_REGISTRY[task_type]


def list_registered_executors() -> list[str]:
    """List all registered task types."""
    return list(_EXECUTOR_REGISTRY.keys())


# Import and register executors when module loads
def _register_all_executors():
    """Import and register all built-in executors."""
    try:
        from src.service.executors.backtest_executor import backtest_executor
        register_executor("backtest", backtest_executor)
    except ImportError as e:
        logger.warning(f"Could not register backtest executor: {e}")
    
    try:
        from src.service.executors.portfolio_executor import portfolio_executor
        register_executor("multi_asset", portfolio_executor)
        register_executor("portfolio", portfolio_executor)  # Alias
    except ImportError as e:
        logger.warning(f"Could not register portfolio executor: {e}")
    
    try:
        from src.service.executors.walkforward_executor import walkforward_executor
        register_executor("walkforward", walkforward_executor)
    except ImportError as e:
        logger.warning(f"Could not register walkforward executor: {e}")


# Auto-register on import
_register_all_executors()


__all__ = [
    "run_blocking_in_threadpool",
    "register_executor",
    "get_executor",
    "list_registered_executors",
]
