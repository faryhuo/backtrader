"""
Strategy Repository.

This module encapsulates user strategy file operations:
- Strategy name sanitization (prevents path traversal)
- CRUD operations in strategy directory (configured in strategy_config.json)
- Reading strategy source with optional UTF-8 BOM stripping
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final, Tuple

from src.config.sandbox_config import get_strategy_config_singleton
from src.config.settings import ensure_resource_dirs

_STRATEGY_NAME_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9_-]+$")
_UTF8_BOM: Final[str] = "\ufeff"


def _get_strategy_dir() -> Path:
    """Get the strategy directory from config."""
    config = get_strategy_config_singleton()
    return config.get_absolute_path()


def ensure_strategy_dirs() -> None:
    """Ensure required resource directories exist (strategy/images/etc)."""
    ensure_resource_dirs()
    # Also ensure strategy dir from config exists
    strategy_dir = _get_strategy_dir()
    strategy_dir.mkdir(parents=True, exist_ok=True)


def sanitize_strategy_filename(name: str) -> str:
    """
    Sanitize a user-provided strategy name and return a filename.

    Only allow simple names to avoid path traversal. Accepts an optional ".py"
    suffix and always returns "<name>.py".

    Args:
        name: Strategy name, with or without ".py".

    Returns:
        Sanitized filename with ".py" suffix.

    Raises:
        ValueError: If the name is missing or contains invalid characters.
    """
    if not name:
        raise ValueError("Strategy name is required")
    clean = name.strip()
    if clean.lower().endswith(".py"):
        clean = clean[:-3]
    if not _STRATEGY_NAME_RE.match(clean):
        raise ValueError("Strategy name must use letters, numbers, '-' or '_'")
    return f"{clean}.py"


def get_strategy_path(name: str) -> Path:
    """
    Get the full path for a strategy file by name.

    Args:
        name: Strategy name, with or without ".py".

    Returns:
        Path under strategy directory (configured in strategy_config.json).
    """
    return _get_strategy_dir() / sanitize_strategy_filename(name)


def list_strategies() -> list[str]:
    """
    List available user strategy names (without ".py").

    Returns:
        Sorted list of strategy stems.
    """
    ensure_strategy_dirs()
    strategy_dir = _get_strategy_dir()
    return sorted({path.stem for path in strategy_dir.glob("*.py")})


def get_user_strategy_code(name: str) -> str:
    """
    Read raw user strategy code from disk.

    Args:
        name: Strategy name.

    Returns:
        Raw strategy text (no BOM stripping for UI fidelity).

    Raises:
        FileNotFoundError: If the strategy file does not exist.
        OSError: If the file cannot be read.
        ValueError: If the name is invalid.
    """
    ensure_strategy_dirs()
    path = get_strategy_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Strategy '{name}' not found")
    return path.read_text(encoding="utf-8")


def save_user_strategy_code(name: str, code: str) -> None:
    """
    Save user strategy code to disk.

    Args:
        name: Strategy name.
        code: Strategy source code.

    Raises:
        OSError: If the file cannot be written.
        ValueError: If the name is invalid.
    """
    ensure_strategy_dirs()
    path = get_strategy_path(name)
    path.write_text(code, encoding="utf-8")


def read_user_strategy_source(name: str) -> Tuple[Path, str]:
    """
    Read user strategy source for execution/analysis.

    This helper normalizes UTF-8 BOM so that code compilation and AST parsing
    behave consistently.

    Args:
        name: Strategy name.

    Returns:
        Tuple of (path, source) where source has BOM stripped if present.

    Raises:
        FileNotFoundError: If the strategy file does not exist.
        OSError: If the file cannot be read.
        ValueError: If the name is invalid.
    """
    ensure_strategy_dirs()
    path = get_strategy_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Strategy '{name}' not found")
    source = path.read_text(encoding="utf-8")
    return path, _strip_utf8_bom(source)


def _strip_utf8_bom(text: str) -> str:
    if text.startswith(_UTF8_BOM):
        return text.lstrip(_UTF8_BOM)
    return text


