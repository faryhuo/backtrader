"""
Worker Configuration - Settings for worker process pool.

Environment variables:
- WORKER_POOL_ENABLED: Enable/disable worker pool (default: true)
- WORKER_POOL_SIZE: Number of worker processes (default: 4)
- WORKER_TASK_TIMEOUT: Task timeout in seconds (default: 300)
- WORKER_MAX_MEMORY_MB: Max memory per worker in MB (default: 1024)
- WORKER_HEARTBEAT_INTERVAL: Heartbeat interval in seconds (default: 10)
"""

import os
from dataclasses import dataclass
from typing import Optional


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


def _parse_bool(value: str) -> bool:
    """Parse boolean from string."""
    return value.lower() in ("true", "1", "yes", "on")


def get_worker_pool_config() -> WorkerPoolConfig:
    """
    Load worker pool configuration from environment variables.
    
    Returns:
        WorkerPoolConfig with values from environment or defaults
    """
    return WorkerPoolConfig(
        enabled=_parse_bool(os.getenv("WORKER_POOL_ENABLED", "true")),
        pool_size=int(os.getenv("WORKER_POOL_SIZE", "4")),
        task_timeout_seconds=float(os.getenv("WORKER_TASK_TIMEOUT", "300")),
        max_memory_mb=int(os.getenv("WORKER_MAX_MEMORY_MB", "1024")),
        heartbeat_interval_seconds=float(os.getenv("WORKER_HEARTBEAT_INTERVAL", "10")),
        shutdown_timeout_seconds=float(os.getenv("WORKER_SHUTDOWN_TIMEOUT", "30")),
        max_queue_size=int(os.getenv("WORKER_MAX_QUEUE_SIZE", "100")),
        allow_network=_parse_bool(os.getenv("WORKER_ALLOW_NETWORK", "true")),
        allow_file_write=_parse_bool(os.getenv("WORKER_ALLOW_FILE_WRITE", "true")),
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
