"""
Worker Configuration - Settings for worker process pool.

Configuration is loaded from strategy_config.json.
"""

import json
import logging
from dataclasses import dataclass
from typing import Optional

from src.config.settings import CONFIG_DIR

logger = logging.getLogger(__name__)


@dataclass
class WorkerPoolConfig:
    """Configuration for the worker process pool."""
    
    # Whether worker pool is enabled
    enabled: bool = True
    
    # Number of worker processes in the pool
    pool_size: int = 4
    
    # Maximum time for a single task (seconds)
    task_timeout_seconds: float = 300.0
    
    # Maximum memory per worker (MB)
    max_memory_mb: int = 1024
    
    # Heartbeat interval for live trading workers (seconds)
    heartbeat_interval_seconds: float = 10.0
    
    # Graceful shutdown timeout (seconds)
    shutdown_timeout_seconds: float = 30.0
    
    # Maximum queue size (0 = unlimited)
    max_queue_size: int = 100
    
    # Whether to allow network access in workers
    allow_network: bool = True  # Required for live trading
    
    # Whether to allow file writes in workers
    allow_file_write: bool = True  # Required for chart generation


def _parse_bool(value) -> bool:
    """Parse boolean from JSON boolean or string."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


def _load_strategy_config_json() -> dict:
    """
    Load strategy configuration from strategy_config.json.
    
    Returns:
        dict: Parsed JSON configuration or empty dict if file not found
    """
    config_file = CONFIG_DIR / "strategy_config.json"
    
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                logger.debug(f"Loaded worker config from {config_file}")
                return config
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load strategy_config.json: {e}")
    
    return {}


def get_worker_pool_config() -> WorkerPoolConfig:
    """
    Load worker pool configuration from strategy_config.json.
    
    Returns:
        WorkerPoolConfig with values from config file or defaults
    """
    config_data = _load_strategy_config_json()
    worker_data = config_data.get("workerPool", {})
    
    return WorkerPoolConfig(
        enabled=_parse_bool(worker_data.get("enabled", True)),
        pool_size=int(worker_data.get("poolSize", 4)),
        task_timeout_seconds=float(worker_data.get("taskTimeoutSeconds", 300)),
        max_memory_mb=int(worker_data.get("maxMemoryMB", 1024)),
        heartbeat_interval_seconds=float(worker_data.get("heartbeatIntervalSeconds", 10)),
        shutdown_timeout_seconds=float(worker_data.get("shutdownTimeoutSeconds", 30)),
        max_queue_size=int(worker_data.get("maxQueueSize", 100)),
        allow_network=_parse_bool(worker_data.get("allowNetwork", True)),
        allow_file_write=_parse_bool(worker_data.get("allowFileWrite", True)),
    )


# Singleton config instance
_config: Optional[WorkerPoolConfig] = None


def get_config() -> WorkerPoolConfig:
    """Get the singleton worker pool configuration."""
    global _config
    if _config is None:
        _config = get_worker_pool_config()
    return _config


def reset_config() -> None:
    """Reset config (for testing)."""
    global _config
    _config = None


__all__ = [
    "WorkerPoolConfig",
    "get_worker_pool_config",
    "get_config",
    "reset_config",
]


