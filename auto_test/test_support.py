"""
Shared helpers for automated tests.

Ensures backend modules are importable from the repo root and disables
authentication for local test runs.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"


def ensure_backend_on_path() -> None:
    """Make backend/ importable when tests run from repo root."""
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))


def disable_auth_for_tests() -> None:
    """Disable login enforcement during automated tests."""
    os.environ.setdefault("ENABLE_LOGIN", "false")
    os.environ.setdefault("LIVE_TRADING_ENABLED", "false")


def reset_session_manager() -> Any:
    """
    Clear SessionManager state and return the singleton instance.

    This keeps tests isolated because SessionManager caches sessions globally.
    """
    from src.service.session_manager import get_session_manager

    manager = get_session_manager()
    manager._sessions.clear()
    return manager


# Apply defaults on import so tests can rely on them.
ensure_backend_on_path()
disable_auth_for_tests()
