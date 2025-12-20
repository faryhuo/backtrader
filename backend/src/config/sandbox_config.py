"""
Sandbox Configuration Module

Provides configuration for strategy execution sandbox with support for
multiple isolation modes: soft, subprocess, and docker.
"""

import os
from dataclasses import dataclass, field
from typing import Literal, Optional

# Type alias for sandbox modes
SandboxMode = Literal["soft", "subprocess", "docker"]


@dataclass
class SandboxConfig:
    """
    Configuration for strategy execution sandbox.
    
    Attributes:
        mode: Isolation mode - 'soft' (in-process), 'subprocess' (isolated process), 
              or 'docker' (containerized)
        timeout_seconds: Maximum execution time before termination
        max_memory_mb: Maximum memory usage in megabytes
        max_cpu_percent: Maximum CPU usage percentage (0-100)
        allow_network: Whether to allow network access in sandbox
        allow_file_write: Whether to allow file write operations
        docker_image: Docker image to use for container mode
        docker_network: Docker network mode ('none', 'bridge', 'host')
    """
    mode: SandboxMode = "subprocess"
    timeout_seconds: float = 30.0
    max_memory_mb: int = 512
    max_cpu_percent: int = 100
    allow_network: bool = False
    allow_file_write: bool = False
    
    # Docker-specific configuration
    docker_image: str = "python:3.11-slim"
    docker_network: str = "none"
    
    # Advanced options
    process_pool_size: int = 2  # Number of worker processes to keep warm
    enable_caching: bool = True  # Cache compiled strategy bytecode


def _parse_bool(value: str) -> bool:
    """Parse boolean from environment variable string."""
    return value.lower() in ("true", "1", "yes", "on")


def get_sandbox_config() -> SandboxConfig:
    """
    Load sandbox configuration from environment variables.
    
    Environment Variables:
        SANDBOX_MODE: soft | subprocess | docker (default: subprocess)
        SANDBOX_TIMEOUT_SECONDS: float (default: 30.0)
        SANDBOX_MAX_MEMORY_MB: int (default: 512)
        SANDBOX_MAX_CPU_PERCENT: int (default: 100)
        SANDBOX_ALLOW_NETWORK: bool (default: false)
        SANDBOX_ALLOW_FILE_WRITE: bool (default: false)
        SANDBOX_DOCKER_IMAGE: str (default: python:3.11-slim)
        SANDBOX_DOCKER_NETWORK: str (default: none)
        SANDBOX_PROCESS_POOL_SIZE: int (default: 2)
        SANDBOX_ENABLE_CACHING: bool (default: true)
    
    Returns:
        SandboxConfig: Loaded configuration
    """
    mode_str = os.getenv("SANDBOX_MODE", "subprocess").lower()
    if mode_str not in ("soft", "subprocess", "docker"):
        mode_str = "subprocess"
    
    return SandboxConfig(
        mode=mode_str,  # type: ignore
        timeout_seconds=float(os.getenv("SANDBOX_TIMEOUT_SECONDS", "30.0")),
        max_memory_mb=int(os.getenv("SANDBOX_MAX_MEMORY_MB", "512")),
        max_cpu_percent=int(os.getenv("SANDBOX_MAX_CPU_PERCENT", "100")),
        allow_network=_parse_bool(os.getenv("SANDBOX_ALLOW_NETWORK", "false")),
        allow_file_write=_parse_bool(os.getenv("SANDBOX_ALLOW_FILE_WRITE", "false")),
        docker_image=os.getenv("SANDBOX_DOCKER_IMAGE", "python:3.11-slim"),
        docker_network=os.getenv("SANDBOX_DOCKER_NETWORK", "none"),
        process_pool_size=int(os.getenv("SANDBOX_PROCESS_POOL_SIZE", "2")),
        enable_caching=_parse_bool(os.getenv("SANDBOX_ENABLE_CACHING", "true")),
    )


# Global singleton instance (lazy loaded)
_config: Optional[SandboxConfig] = None


def get_config() -> SandboxConfig:
    """Get the global sandbox configuration (singleton)."""
    global _config
    if _config is None:
        _config = get_sandbox_config()
    return _config


def reset_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global _config
    _config = None


__all__ = [
    "SandboxConfig",
    "SandboxMode",
    "get_sandbox_config",
    "get_config",
    "reset_config",
]
