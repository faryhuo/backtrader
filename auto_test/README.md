# Auto Test Suite

Comprehensive automated test suite for the backtrader application, covering end-to-end workflows, reusable test libraries, and smoke tests for quick health checks.

## Directory Structure

```
auto_test/
├── libs/               # Reusable test utilities
│   ├── api_client.py   # HTTP client wrapper with authentication
│   ├── browser_helper.py  # Playwright browser automation utilities
│   ├── data_fixtures.py   # Test data generators and factories
│   ├── db_helper.py    # Database utilities for test setup/teardown
│   └── assertions.py   # Custom assertion helpers
├── e2e/                # End-to-end tests
│   ├── test_strategy_management.py
│   ├── test_backtest_workflow.py
│   ├── test_live_trading.py
│   └── ...
├── smoke/              # Smoke tests (critical, fast)
│   ├── test_critical_api.py
│   └── test_critical_ui.py
├── conftest.py         # Root pytest configuration
├── pytest.ini          # Pytest settings
├── requirements.txt    # Test dependencies
└── .env.test.template  # Environment configuration template
```

## Setup

### 1. Install Dependencies

```bash
cd d:\Project\backtrader\auto_test
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Environment

Copy the environment template and configure:

```bash
copy .env.test.template .env.test
```

Edit `.env.test` with your settings (API URL, database path, etc.).

### 3. Ensure Backend and Frontend are Running

> [!IMPORTANT]
> **The servers MUST be running before executing tests!**

The tests expect the backend and frontend servers to be running:

- **Backend**: `http://localhost:8000` (required for all tests)
  ```bash
  # Start from project root
  .\start_server.bat
  ```

- **Frontend**: `http://localhost:5173` (required for UI tests only)
  ```bash
  # Start from project root  
  cd frontend
  npm run dev
  ```

If servers are not running:
- **API tests** will fail or be skipped
- **UI tests** will be skipped with a warning

### 4. Configure Authentication (Optional)

> [!NOTE]
> By default, tests that require authentication will be SKIPPED. To run them, you need valid authentication.

**To run auth-required tests:**

```bash
# Option 1: Set environment variable with real JWT token
set TEST_AUTH_TOKEN=your_valid_jwt_token_here
pytest e2e/

# Option 2: Disable auth skip (will fail if no token)
set SKIP_AUTH_TESTS=false
pytest e2e/
```

**Without authentication:**
- ✅ Smoke tests will PASS (check server health)
- ⏭️ E2E API tests will SKIP (require auth)
- ⏭️ E2E UI tests will SKIP if frontend not running

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Smoke Tests (Fast Health Check)

```bash
pytest -m smoke
```

Smoke tests should complete in <30 seconds and verify critical functionality.

### Run E2E Tests

```bash
pytest e2e/
```

### Run Specific Test Categories

```bash
# API tests only
pytest -m api

# UI tests only
pytest -m ui

# Fast tests (exclude slow)
pytest -m "not slow"

# Specific test file
pytest e2e/test_strategy_management.py

# Specific test function
pytest e2e/test_strategy_management.py::TestStrategyAPI::test_create_and_get_strategy
```

### Run with Browser Visible (for debugging UI tests)

Modify the `headless` parameter in fixtures or set environment variable:

```bash
# In .env.test
HEADLESS_BROWSER=false
```

Then run UI tests:

```bash
pytest -m ui
```

## Test Categories

### Libs (Reusable Utilities)

- **api_client.py**: HTTP client with authentication, retry logic, and common request methods
- **browser_helper.py**: Playwright wrapper with navigation, interaction, and assertion helpers
- **data_fixtures.py**: Test data generators for strategies, configs, and sample data
- **db_helper.py**: Database connection and data cleanup utilities
- **assertions.py**: Custom assertions for API responses, metrics, and data validation

### E2E Tests (Comprehensive Workflows)

- **test_strategy_management.py**: Strategy CRUD, version control, template import
- **test_backtest_workflow.py**: Backtest execution, history, AI analysis
- **test_live_trading.py**: Live/paper trading sessions, monitoring
- Additional tests can be added for portfolio, walk-forward, etc.

### Smoke Tests (Critical Health Checks)

- **test_critical_api.py**: Essential API endpoint checks (<10s total)
- **test_critical_ui.py**: Essential UI page load checks (<20s total)

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Auto Tests

on: [push, pull_request]

jobs:
  smoke-tests:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          cd auto_test
          pip install -r requirements.txt
          playwright install chromium
      - name: Run smoke tests
        run: |
          cd auto_test
          pytest -m smoke
```

## Notes

### Authentication

Currently using mock authentication tokens. For production testing with real Logto:

1. Update `api_client.py` to obtain real JWT tokens
2. Configure test user credentials in `.env.test`
3. Update fixtures in `conftest.py` to use real authentication

### Live Trading Tests

Live trading tests use paper mode by default. To test with real exchange APIs:

1. Configure exchange API credentials in `.env.test`
2. Ensure exchange is properly configured in backend
3. Tests will automatically use configured exchanges

### Database Cleanup

Tests include cleanup fixtures to remove test data. Use `cleanup_test_data` fixture:

```python
def test_example(api_client, cleanup_test_data):
    # Test code...
    pass
    # cleanup_test_data will run after test
```

## Troubleshooting

### Browser Tests Fail

- Ensure frontend is running on `http://localhost:5173`
- Check if Playwright browsers are installed: `playwright install`
- Run with `headless=False` to see browser actions
- Check browser console for JavaScript errors

### API Tests Fail

- Ensure backend is running on `http://localhost:8000`
- Check if authentication is properly configured
- Verify database connection settings
- Check backend logs for errors

### Tests Are Slow

- Run only smoke tests for quick checks: `pytest -m smoke`
- Use parallel execution: `pytest -n auto` (requires pytest-xdist)
- Skip slow tests: `pytest -m "not slow"`

## Contributing

When adding new tests:

1. Place in appropriate directory (`e2e/` or `smoke/`)
2. Use existing fixtures from `conftest.py`
3. Add proper markers (`@pytest.mark.api`, `@pytest.mark.ui`, etc.)
4. Follow naming convention: `test_*.py` for files, `test_*` for functions
5. Add smoke test if it's a critical feature
6. Update this README if adding new test categories
