"""
Root conftest for auto_test package.

Provides global pytest configuration and fixtures.
"""

import pytest


def pytest_configure(config):
    """Configure custom markers at root level."""
    config.addinivalue_line(
        "markers", "smoke: mark test as smoke test (critical, fast)"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API test"
    )
    config.addinivalue_line(
        "markers", "ui: mark test as UI/browser test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow-running (>10s)"
    )


# pytest --collect-only to see all collected tests
# pytest -m smoke to run only smoke tests
# pytest -m "api and not slow" to run fast API tests
# pytest e2e/ to run only e2e tests
# pytest smoke/ to run only smoke tests
