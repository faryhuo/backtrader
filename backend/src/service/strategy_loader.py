"""
Strategy Loader.

Loads and compiles user strategy code with optional subprocess-based validation.
"""

from __future__ import annotations

import logging

import backtrader as bt

from src.config.sandbox_config import get_config as get_sandbox_config
from src.service.isolated_sandbox import (
    IsolatedSandbox,
    SandboxError,
    SandboxExecutionError,
    SandboxTimeoutError,
)
from src.service.strategy_repo import read_user_strategy_source
from src.service.strategy_sandbox import StrategySandboxError, execute_strategy_code

logger = logging.getLogger(__name__)


class StrategyLoaderError(Exception):
    """Raised when a user strategy cannot be loaded by the loader."""


def load_user_strategy(name: str) -> type[bt.Strategy]:
    """
    Load and compile a user strategy from file.

    Security Model:
        - Subprocess mode (default): Code is first validated in an isolated subprocess
          with resource limits and blocked dangerous patterns. After validation,
          the code is RE-EXECUTED in the main process to obtain the class object.
        - Soft mode: Code executes directly in main process with minimal restrictions.

    IMPORTANT: Both modes ultimately execute user code in the main process.
    This is suitable ONLY for trusted strategy code. For untrusted code in
    multi-tenant deployments, use container-level isolation.
    See docs/SECURITY.md for threat model and known bypass techniques.

    Args:
        name: Strategy name (without .py extension)

    Returns:
        type[bt.Strategy]: The UserStrategy class from the strategy file

    Raises:
        StrategyLoaderError: If strategy cannot be loaded.
    """
    try:
        path, source = read_user_strategy_source(name)
    except FileNotFoundError as exc:
        raise StrategyLoaderError(f"Strategy '{name}' not found") from exc

    try:
        sandbox_config = get_sandbox_config()

        if sandbox_config.mode == "soft":
            logger.warning(
                "Using soft sandbox mode - not secure against malicious code. "
                "Set SANDBOX_MODE=subprocess for better isolation."
            )
            module_globals = execute_strategy_code(
                source,
                module_name=f"user_strategy_{name}",
                filename=str(path),
            )
            strategy_cls = module_globals.get("UserStrategy")
        else:
            sandbox = IsolatedSandbox(
                timeout=sandbox_config.timeout_seconds,
                max_memory_mb=sandbox_config.max_memory_mb,
                allow_network=sandbox_config.allow_network,
                allow_file_write=sandbox_config.allow_file_write,
            )
            result = sandbox.execute_strategy(
                source=source,
                module_name=f"user_strategy_{name}",
                filename=str(path),
            )

            strategy_class_name = result.get("strategy_class")
            if not strategy_class_name:
                raise StrategyLoaderError("UserStrategy class not found in strategy file")

            module_globals = execute_strategy_code(
                source,
                module_name=f"user_strategy_{name}",
                filename=str(path),
            )
            strategy_cls = module_globals.get("UserStrategy")

    except SandboxTimeoutError as exc:
        raise StrategyLoaderError(
            f"Strategy '{name}' timed out during validation"
        ) from exc
    except (SandboxError, SandboxExecutionError) as exc:
        raise StrategyLoaderError(f"Failed to load strategy '{name}': {exc}") from exc
    except (OSError, StrategySandboxError) as exc:
        raise StrategyLoaderError(f"Failed to load strategy '{name}': {exc}") from exc

    if strategy_cls is None:
        raise StrategyLoaderError("UserStrategy class not found in strategy file")
    if not issubclass(strategy_cls, bt.Strategy):
        raise StrategyLoaderError("UserStrategy must inherit from backtrader.Strategy")
    return strategy_cls

