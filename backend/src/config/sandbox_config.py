"""
Sandbox Configuration Module

Provides configuration for strategy execution sandbox with support for
multiple isolation modes: soft, subprocess, and docker.

Configuration is loaded from strategy_config.json.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

from src.config.settings import CONFIG_DIR, PROJECT_ROOT, STRATEGY_DIR

logger = logging.getLogger(__name__)

# Type alias for sandbox modes
SandboxMode = Literal["soft", "subprocess", "docker"]


@dataclass
class StrategyConfig:
    """
    Configuration for strategy file paths.
    
    Attributes:
        file_path: Directory path for user strategy files (relative to PROJECT_ROOT)
    """
    file_path: str = STRATEGY_DIR.relative_to(PROJECT_ROOT).as_posix()
    
    def get_absolute_path(self) -> Path:
        """Get the absolute path for strategy files."""
        path = Path(self.file_path)
        if path.is_absolute():
            return path
        return PROJECT_ROOT / path


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
                logger.debug(f"Loaded strategy config from {config_file}")
                return config
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load strategy_config.json: {e}")
    
    return {}


def get_strategy_config() -> StrategyConfig:
    """
    Load strategy configuration from strategy_config.json.
    
    Returns:
        StrategyConfig: Strategy file path configuration
    """
    config_data = _load_strategy_config_json()
    strategy_data = config_data.get("strategy", {})
    
    return StrategyConfig(
        file_path=strategy_data.get("filePath", STRATEGY_DIR.relative_to(PROJECT_ROOT).as_posix()),
    )


def get_sandbox_config() -> SandboxConfig:
    """
    Load sandbox configuration from strategy_config.json.
    
    Returns:
        SandboxConfig: Loaded configuration
    """
    config_data = _load_strategy_config_json()
    sandbox_data = config_data.get("sandbox", {})
    
    # Get mode with validation
    mode_str = str(sandbox_data.get("mode", "subprocess")).lower()
    if mode_str not in ("soft", "subprocess", "docker"):
        mode_str = "subprocess"
    
    return SandboxConfig(
        mode=mode_str,  # type: ignore
        timeout_seconds=float(sandbox_data.get("timeoutSeconds", 30.0)),
        max_memory_mb=int(sandbox_data.get("maxMemoryMB", 512)),
        max_cpu_percent=int(sandbox_data.get("maxCpuPercent", 100)),
        allow_network=_parse_bool(sandbox_data.get("allowNetwork", False)),
        allow_file_write=_parse_bool(sandbox_data.get("allowFileWrite", False)),
        docker_image=str(sandbox_data.get("dockerImage", "python:3.11-slim")),
        docker_network=str(sandbox_data.get("dockerNetwork", "none")),
        process_pool_size=int(sandbox_data.get("processPoolSize", 2)),
        enable_caching=_parse_bool(sandbox_data.get("enableCaching", True)),
    )


# Global singleton instances (lazy loaded)
_sandbox_config: Optional[SandboxConfig] = None
_strategy_config: Optional[StrategyConfig] = None


def get_config() -> SandboxConfig:
    """Get the global sandbox configuration (singleton)."""
    global _sandbox_config
    if _sandbox_config is None:
        _sandbox_config = get_sandbox_config()
    return _sandbox_config


def get_strategy_config_singleton() -> StrategyConfig:
    """Get the global strategy configuration (singleton)."""
    global _strategy_config
    if _strategy_config is None:
        _strategy_config = get_strategy_config()
    return _strategy_config


def reset_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global _sandbox_config, _strategy_config
    _sandbox_config = None
    _strategy_config = None


__all__ = [
    "SandboxConfig",
    "SandboxMode",
    "StrategyConfig",
    "get_sandbox_config",
    "get_strategy_config",
    "get_strategy_config_singleton",
    "get_config",
    "reset_config",
]

