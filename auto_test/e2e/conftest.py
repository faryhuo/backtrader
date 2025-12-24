"""
Shared fixtures and configuration for e2e tests.
"""

import os
import pytest
import socket
import subprocess
import sys
import time
from pathlib import Path

# Add libs to path
libs_path = Path(__file__).parent.parent / "libs"
sys.path.insert(0, str(libs_path))

from api_client import APIClient, create_mock_token
from browser_helper import BrowserHelper
from data_fixtures import DataFixtures
from db_helper import DBHelper
from auth_config import should_skip_auth_test, get_auth_token


def is_port_in_use(port: int, host: str = "localhost") -> bool:
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        try:
            s.connect((host, port))
            return True
        except (socket.error, socket.timeout):
            return False


def wait_for_server(port: int, host: str = "localhost", timeout: int = 30) -> bool:
    """Wait for server to become available."""
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        if is_port_in_use(port, host):
            # Double-check with HTTP request
            try:
                import httpx
                response = httpx.get(f"http://{host}:{port}/api/site/config", timeout=5, proxy=None)
                if response.status_code == 200:
                    return True
            except Exception:
                pass
        time.sleep(1)
    return False


# Global to track if we started the server
_server_process = None
_server_started_by_tests = False


@pytest.fixture(scope="session", autouse=True)
def server_manager():
    """
    Manage backend server lifecycle.
    
    - Checks if server is running on port 8000
    - If not, starts it automatically
    - Stops the server after all tests complete (only if we started it)
    """
    global _server_process, _server_started_by_tests
    
    port = 8000
    backend_dir = Path(__file__).parent.parent.parent / "backend"
    
    # Check if server is already running
    if is_port_in_use(port):
        print(f"\n[Test Setup] Backend server already running on port {port}")
        _server_started_by_tests = False
        yield
        return
    
    # Server not running - start it
    print(f"\n[Test Setup] Starting backend server on port {port}...")
    
    try:
        # Start uvicorn in subprocess
        _server_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", str(port)],
            cwd=str(backend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            # Don't capture output to see startup errors
            # stdout=None,
            # stderr=None,
        )
        _server_started_by_tests = True
        
        # Wait for server to be ready
        if wait_for_server(port, timeout=30):
            print(f"[Test Setup] Backend server started successfully (PID: {_server_process.pid})")
        else:
            print(f"[Test Setup] WARNING: Server may not be ready yet")
        
        yield
        
    finally:
        # Only stop server if we started it
        if _server_started_by_tests and _server_process:
            print(f"\n[Test Teardown] Stopping backend server (PID: {_server_process.pid})...")
            _server_process.terminate()
            try:
                _server_process.wait(timeout=5)
                print("[Test Teardown] Backend server stopped")
            except subprocess.TimeoutExpired:
                _server_process.kill()
                print("[Test Teardown] Backend server force killed")
            _server_process = None


@pytest.fixture(scope="session")
def api_base_url(server_manager):
    """Base URL for API tests. Depends on server_manager to ensure server is running."""
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


@pytest.fixture(scope="function", autouse=True)
def skip_ui_tests(request):
    """
    Auto-skip UI tests due to asyncio/Playwright conflicts.
    UI tests should be run separately with proper async handling.
    """
    if request.node.get_closest_marker('ui'):
        pytest.skip("UI tests skipped (asyncio/Playwright conflict). Run separately with: pytest -m ui --no-header")


@pytest.fixture(scope="function")
def browser(frontend_url):
    """
    Provide browser helper for UI tests.
    Function-scoped so each test gets a fresh browser.
    
    Environment variables:
        HEADLESS: Set to '0' or 'false' to show browser window (default: headless)
        SLOW_MO: Milliseconds to slow down operations (default: 0)
    """
    import os
    
    # Check HEADLESS env var - default to True (headless mode)
    headless_env = os.getenv("HEADLESS", "1").lower()
    headless = headless_env not in ("0", "false", "no")
    
    # Check SLOW_MO env var - useful for debugging
    slow_mo = int(os.getenv("SLOW_MO", "0"))
    
    browser = BrowserHelper(
        headless=headless,
        base_url=frontend_url,
        slow_mo=slow_mo,
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
