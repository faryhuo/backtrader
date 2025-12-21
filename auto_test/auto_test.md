# Auto Test Suite

| 目录 | 说明 | 典型内容 / 特点 |
| :--- | :--- | :--- |
| **e2e/** | 存放端到端用例：从浏览器或 API 入口，穿过前端、网关、后端、数据库等完整链路。 |
| **smoke/** | 从 e2e 用例中挑出最关键、数量最少的一小撮，用作每次构建/部署后的快速健康检查。 |
| **libs/** | 放各种可复用的封装，避免 e2e/smoke 里的脚本变成「复制粘贴地狱」。 |

## Test Coverage

### E2E Tests

| File | Coverage Area | Test Count |
| :--- | :--- | :--- |
| `test_strategy_management.py` | Strategy CRUD, versioning, templates | 15 tests |
| `test_backtest_workflow.py` | Backtest execution, history, AI analysis | 15 tests |
| `test_live_trading.py` | Live/paper trading sessions, exchanges | 10 tests |
| `test_portfolio_workflow.py` | Portfolio backtesting, multi-asset | 10 tests |
| `test_walkforward_workflow.py` | Walk-forward optimization | 11 tests |
| `test_market_data.py` | Ticker data, cache, resampling, analysis | 17 tests |
| `test_settings.py` | User settings, credentials, data source config | 15 tests |
| `test_tasks.py` | Task management, lifecycle, stats | 15 tests |

### Smoke Tests

| File | Coverage Area | Test Count |
| :--- | :--- | :--- |
| `test_critical_api.py` | Essential API endpoint health checks | 12 tests |
| `test_critical_ui.py` | Frontend page load verification | 4 tests |

## Libs Modules

| Module | Purpose |
| :--- | :--- |
| `api_client.py` | HTTP client with authentication support |
| `browser_helper.py` | Playwright browser automation wrapper |
| `assertions.py` | Custom assertion helpers for API responses |
| `data_fixtures.py` | Test data generators and configurations |
| `db_helper.py` | SQLite database utilities for cleanup |
| `auth_config.py` | Smart authentication detection |
| `response_normalizer.py` | Response format normalization |

## Running Tests

```bash
# Run all tests
python -m pytest auto_test -q

# Run smoke tests only (fastest)
python -m pytest auto_test/smoke -q

# Run e2e tests only
python -m pytest auto_test/e2e -q

# Run tests by marker
python -m pytest auto_test -m api -q      # API tests only
python -m pytest auto_test -m ui -q       # UI tests only
python -m pytest auto_test -m slow -q     # Slow tests only

# Run specific test file
python -m pytest auto_test/e2e/test_strategy_management.py -v
```

## Test Markers

- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.ui` - UI/browser tests
- `@pytest.mark.slow` - Tests that take >10 seconds
- `@pytest.mark.smoke` - Critical fast tests for health checks
- `@pytest.mark.requires_auth` - Tests requiring authentication

## Authentication

Tests automatically detect if the backend requires authentication:

1. **Auth Disabled**: Tests run without tokens
2. **Auth Enabled + Token Available**: Tests use the provided token
3. **Auth Enabled + No Token**: Tests are skipped gracefully

Set `TEST_AUTH_TOKEN` environment variable for authenticated testing:
```bash
set TEST_AUTH_TOKEN=your_jwt_token_here
python -m pytest auto_test -q
```
