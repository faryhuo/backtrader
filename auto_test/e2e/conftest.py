"""
Shared fixtures and configuration for e2e tests.
"""

import pytest
import sys
from pathlib import Path

# Add libs to path
libs_path = Path(__file__).parent.parent / "libs"
sys.path.insert(0, str(libs_path))

from api_client import APIClient, create_mock_token
from browser_helper import BrowserHelper
from data_fixtures import DataFixtures
from db_helper import DBHelper
from auth_config import should_skip_auth_test, get_auth_token


@pytest.fixture(scope="session")
def api_base_url():
    """Base URL for API tests."""
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def frontend_url():
    """Base URL for frontend tests."""
    return "http://localhost:5173"


@pytest.fixture(scope="function")
def api_client(api_base_url):
    """
    Provide API client with authentication.
    Uses real token if available, otherwise mock token.
    If backend doesn't require auth, sends no token at all.
    Function-scoped so each test gets a fresh client.
    """
    from auth_config import is_auth_required
    
    # Check if backend requires auth
    if is_auth_required():
        # Backend requires auth - use real token or mock
        token = get_auth_token() or create_mock_token(user_id="test_user", username="testuser")
    else:
        # Backend auth disabled - don't send any token!
        token = None
    
    client = APIClient(base_url=api_base_url, token=token)
    yield client
    client.close()


@pytest.fixture(scope="function", autouse=True)
def skip_if_no_auth(request):
    """Skip tests marked with 'requires_auth' if authentication is not configured."""
    if request.node.get_closest_marker('requires_auth'):
        if should_skip_auth_test():
            # Import here to avoid circular dependency
            from auth_config import is_auth_required
            if is_auth_required():
                pytest.skip("Backend requires authentication. Set TEST_AUTH_TOKEN or disable backend auth")
            # If auth is not required, test will run!


@pytest.fixture(scope="function")
def browser(frontend_url):
    """
    Provide browser helper for UI tests.
    Function-scoped so each test gets a fresh browser.
    """
    browser = BrowserHelper(
        headless=True,  # Set to False for debugging
        base_url=frontend_url,
        slow_mo=0,  # Increase for debugging (e.g., 100)
    )
    browser.start()
    yield browser
    browser.stop()


@pytest.fixture(scope="session")
def data_fixtures():
    """Provide test data fixtures."""
    return DataFixtures()


@pytest.fixture(scope="session")
def db_helper():
    """Provide database helper."""
    return DBHelper()


@pytest.fixture(scope="function", autouse=False)
def cleanup_test_data(db_helper):
    """
    Cleanup test data after each test.
    Not auto-used to give tests control over when to clean up.
    """
    yield
    # Cleanup after test
    db_helper.cleanup_test_data(user_id="test_user")


@pytest.fixture(scope="function")
def test_strategy_name():
    """Provide a unique test strategy name for each test."""
    import uuid
    return f"test_strategy_{uuid.uuid4().hex[:8]}"


# Pytest markers
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "api: mark test as API test"
    )
    config.addinivalue_line(
        "markers", "ui: mark test as UI/browser test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow-running"
    )
    config.addinivalue_line(
        "markers", "smoke: mark test as smoke test (critical)"
    )
    config.addinivalue_line(
        "markers", "requires_auth: mark test as requiring real authentication"
    )
