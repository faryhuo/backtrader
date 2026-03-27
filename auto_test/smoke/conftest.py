"""
Shared fixtures for smoke tests.

Smoke tests use minimal setup for fast execution.
"""

import pytest
import sys
from pathlib import Path

# Add libs to path
libs_path = Path(__file__).parent.parent / "libs"
sys.path.insert(0, str(libs_path))

from api_client import APIClient, create_mock_token


@pytest.fixture(scope="session")
def api_client():
    """Provide API client for smoke tests (session-scoped for speed)."""
    token = create_mock_token()
    client = APIClient(token=token)
    yield client
    client.close()


@pytest.fixture(scope="session")
def browser():
    """Provide browser for smoke tests (session-scoped for speed)."""
    try:
        from browser_helper import BrowserHelper
    except ModuleNotFoundError as exc:
        if exc.name == "playwright":
            pytest.skip("Playwright is not installed; skipping browser smoke tests.")
        raise

    browser = BrowserHelper(headless=True)
    browser.start()
    yield browser
    browser.stop()
