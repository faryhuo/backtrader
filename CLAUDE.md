# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working Rules

- Before modifying any file, check whether the file's current folder contains a `*.md` "directory description" document. If it exists, **read it first** and follow its stated responsibilities, conventions, and non‑functional requirements when making changes.
- After updating code, update the corresponding directory description document if relevant.

Directory documentation files:
- `backend/src/src.md` - Backend source root overview
- `backend/src/routes/routes.md` - API routing conventions
- `backend/src/service/service.md` - Business logic layer
- `backend/src/service/worker/worker.md` - Worker pool isolation system
- `backend/src/db/db.md` - Database/persistence layer
- `backend/src/config/config.md` - Configuration management
- `backend/src/utils/utils.md` - Utility functions
- `backend/src/brokers/brokers.md` - Trading adapters overview
- `backend/src/brokers/ccxt_adapter/ccxt_adapter.md` - CCXT adapter
- `backend/src/brokers/ibkr_adapter/ibkr_adapter.md` - IBKR adapter
- `backend/resources/strategy/strategy.md` - Strategy file conventions

Feature documentation (in `docs/`):
- `docs/DEEP_ANALYSIS_FEATURE.md` - Deep analysis feature details
- `docs/MULTI_ASSET_IMPLEMENTATION_ROADMAP.md` - Portfolio backtest roadmap
- `docs/SECURITY.md` - Security guidelines
- `docs/TIME_FRAME.md` - Timeframe documentation
- `docs/FEATURE-PLAN.md` - Feature planning

## Project Overview

This is a **Backtrader-based trading platform** with:
- **Backend**: FastAPI + Backtrader + SQLAlchemy (Python 3.11+)
- **Frontend**: React + Vite + Ant Design + i18next
- **Live Trading**: CCXT (crypto exchanges) and IBKR (Interactive Brokers) adapters
- **Features**:
  - Strategy backtesting (single-asset and multi-asset portfolio)
  - Walk-forward optimization with out-of-sample validation
  - Live/paper trading with real-time monitoring
  - AI-powered analysis (OpenAI integration)
  - Deep analysis (returns heatmaps, rolling metrics, drawdown analysis)
  - Report generation and sharing
  - Task queue for async operations
  - Multi-language support (en, zh)
  - PyFolio integration for advanced metrics

The platform allows users to develop, backtest, and deploy trading strategies with the same code running in both backtest and live modes.

## Development Commands

### Backend (Python)

```bash
# Development server (backend only)
cd backend
python main.py  # Runs on http://0.0.0.0:8000

# Install dependencies
cd backend
pip install -r requirements.txt

# Run tests (pytest configured but no tests currently)
cd backend
python -m pytest

# Environment setup
cd backend
cp .env.template .env  # Then edit .env with your credentials
```

### Frontend (React + Vite)

```bash
# Build for production
cd frontend
npm run build  # Outputs to frontend/dist/

# Note: if you want to run the frontend. pls run the Full Stack Development

# Lint
cd frontend
npm run lint
```


### Full Stack Development

```bash
# Windows: 1. build 2. start server
build.bat

start_server.bat
```

### Docker

```bash
# Build and run (uses .env.prod by default)
docker-compose up

# Build optimized image
bash docker-build-optimized.sh

# Note: Dockerfile uses multi-stage build with Python 3.12-slim-bookworm
```

## Architecture

### Backend Structure

```
backend/
├── src/
│   ├── brokers/              # Live trading adapters
│   │   ├── ccxt_adapter/     # CCXT integration (crypto exchanges)
│   │   │   ├── ccxt_store.py       # Connection manager with async/sync bridge
│   │   │   ├── ccxt_broker.py      # Order execution
│   │   │   └── ccxt_data.py        # Live data feeds
│   │   └── ibkr_adapter/     # Interactive Brokers integration
│   │       └── ibkr_store.py
│   ├── config/               # Settings and configuration
│   │   ├── config_manager.py       # Configuration management
│   │   ├── settings.py             # Settings definitions
│   │   ├── sandbox_config.py       # Sandbox environment config
│   │   └── worker_config.py        # Worker pool configuration
│   ├── contracts/            # Configuration contracts and exceptions
│   │   ├── exceptions.py           # Custom exception classes
│   │   ├── sizer_config.py         # Position sizing configuration
│   │   └── task.py                 # Task-related contracts
│   ├── db/                   # Database layer (SQLAlchemy)
│   │   ├── models/                 # Database models (reorganized)
│   │   │   ├── base.py             # Base model class
│   │   │   ├── trading.py          # Session, order, position models
│   │   │   ├── backtest.py         # Backtest history, portfolio results
│   │   │   ├── market.py           # Market data, ticker metadata
│   │   │   ├── user.py             # User settings, strategy versions
│   │   │   ├── report.py           # Report models
│   │   │   └── task.py             # Task models
│   │   ├── storage/                # Data access layer
│   │   │   ├── base.py             # Base storage class
│   │   │   ├── backtest.py         # Backtest history persistence
│   │   │   ├── portfolio.py        # Portfolio backtest results
│   │   │   ├── walkforward.py      # Walk-forward results
│   │   │   ├── report.py           # Report storage
│   │   │   ├── task.py             # Task storage
│   │   │   ├── session.py          # Live trading session persistence
│   │   │   ├── market_data.py      # Market data caching
│   │   │   ├── eodhd_data.py       # EODHD data integration
│   │   │   ├── ticker_metadata.py  # Ticker information
│   │   │   ├── strategy_version.py # Version control
│   │   │   ├── resampler.py        # Data resampling
│   │   │   ├── data_cache.py       # Cache management
│   │   │   └── settings/           # Settings storage submodule
│   │   │       ├── base.py         # Base settings storage
│   │   │       ├── credentials.py  # API credentials storage
│   │   │       ├── data_source.py  # Data source settings
│   │   │       ├── logto_config.py # Auth configuration
│   │   │       └── site_config.py  # Site configuration
│   │   └── database.py             # Database connection
│   ├── routes/               # FastAPI route handlers
│   │   ├── common/                 # Route utilities
│   │   │   ├── auth_dependencies.py# Auth dependency injection
│   │   │   ├── dependencies.py     # Common dependencies
│   │   │   ├── error_utils.py      # Error handling utilities
│   │   │   └── task_helpers.py     # Task route helpers
│   │   ├── backtest_routes.py      # /api/backtest (core backtesting)
│   │   ├── portfolio_routes.py     # /api/portfolio (multi-asset backtest)
│   │   ├── walkforward_routes.py   # /api/walkforward (optimization)
│   │   ├── report_routes.py        # /api/reports (generation/sharing)
│   │   ├── task_routes.py          # /api/tasks (async task management)
│   │   ├── market_data_routes.py   # /api/market-data
│   │   ├── settings_routes.py      # /api/settings
│   │   ├── site_config_routes.py   # /api/site-config
│   │   ├── strategy_routes.py      # /api/strategy
│   │   ├── ai_routes.py            # /api/ai_analyze (OpenAI integration)
│   │   ├── live_routes.py          # /api/live/* (trading session mgmt)
│   │   ├── websocket_routes.py     # WebSocket for real-time updates
│   │   └── frontend_routes.py      # Static file serving
│   ├── service/              # Business logic
│   │   ├── worker/                 # Worker pool isolation
│   │   │   ├── worker_pool.py      # Process pool manager
│   │   │   ├── backtest_worker.py  # Backtest execution worker
│   │   │   ├── live_worker.py      # Live trading worker
│   │   │   ├── task_models.py      # IPC task models
│   │   │   └── worker.md           # Worker documentation
│   │   ├── app.py                  # FastAPI app initialization
│   │   ├── backtest_engine.py      # Core backtesting logic
│   │   ├── backtest_runner.py      # Backtest execution wrapper
│   │   ├── multi_asset_backtest.py # Multi-asset portfolio backtesting
│   │   ├── multi_asset_strategy_wrapper.py # Strategy adapter
│   │   ├── portfolio_analyzers.py  # Portfolio analysis tools
│   │   ├── portfolio_rebalancer.py # Portfolio rebalancing logic
│   │   ├── walkforward_optimizer.py# Walk-forward optimization
│   │   ├── pyfolio_exporter.py     # PyFolio integration
│   │   ├── report_generator.py     # Report generation
│   │   ├── live_engine.py          # Live trading orchestration
│   │   ├── session_manager.py      # Multi-session lifecycle mgmt
│   │   ├── strategy_sandbox.py     # Safe strategy code execution
│   │   ├── strategy_loader.py      # Strategy loading utility
│   │   ├── strategy_param_extractor.py # Parameter extraction
│   │   ├── strategy_repo.py        # Strategy repository management
│   │   ├── task_manager.py         # Task queue management
│   │   ├── websocket_manager.py    # WebSocket connection manager
│   │   ├── echarts_theme.py        # Chart theming support
│   │   ├── deep_analysis.py        # Deep analysis calculations
│   │   ├── parameter_analysis.py   # Parameter sensitivity analysis
│   │   ├── strategy_executor.py    # Strategy execution wrapper
│   │   ├── strategy_templates.py   # Strategy template management
│   │   ├── version_service.py      # Version tracking service
│   │   └── isolated_sandbox.py     # Isolated sandbox execution
│   └── utils/                # Utilities
│       ├── auth.py                 # JWT authentication (Logto)
│       ├── config_loader.py        # Broker config loader
│       ├── logger.py               # Logging configuration
│       ├── encryption.py           # Credential encryption
│       ├── credential_validator.py # Credential validation
│       ├── exception_handlers.py   # Global exception handlers
│       ├── request_context.py      # Request context management
│       ├── share_token.py          # Share token generation
│       └── report_i18n.py          # Report internationalization
├── resources/
│   ├── config/
│   │   └── broker_config.json      # Exchange settings, risk limits
│   ├── strategy/                   # User strategy files (.py)
│   ├── frontend/                   # Built frontend assets (served by backend)
│   ├── images/                     # Generated backtest charts
│   ├── reports/                    # Generated reports storage
│   └── templates/                  # Report/email templates
├── main.py                   # Entry point (Daphne ASGI server)
└── api.py                    # Exports FastAPI app
```

### Frontend Structure

```
frontend/src/
├── assets/                  # Static assets (images, fonts)
├── components/              # React components
│   ├── Auth/               # Authentication (Logto provider)
│   ├── Layout/             # App shell with navigation
│   ├── Landing/            # Landing page
│   │   ├── Hero.jsx        # Hero section
│   │   ├── Features.jsx    # Features showcase
│   │   ├── Roadmap.jsx     # Development roadmap
│   │   ├── Workflow.jsx    # User workflow demo
│   │   ├── CTA.jsx         # Call-to-action section
│   │   ├── Navbar.jsx      # Landing page navigation
│   │   └── Footer.jsx      # Footer component
│   ├── RunStrategy/        # Backtest execution UI
│   ├── BacktestHistory/    # Historical results browser
│   ├── PortfolioBacktest/  # Portfolio backtesting UI│   ├── WalkForward/        # Walk-forward optimization UI│   ├── DeepAnalysis/       # Advanced analysis visualizations│   │   ├── MonthlyReturnsHeatmap.jsx
│   │   ├── RollingMetricsChart.jsx
│   │   ├── ReturnsDistribution.jsx
│   │   ├── DrawdownAnalysis.jsx
│   │   └── ConsecutiveLossStats.jsx
│   ├── ReportCenter/       # Report generation and sharing│   ├── DataManagement/     # Data cache management UI│   ├── LiveTrading/        # Live trading dashboard
│   ├── StrategyMaintain/   # Strategy code editor (Monaco)
│   ├── DataSource/         # Data source configuration
│   └── Settings/           # User settings UI
├── pages/                  # Top-level page components
│   ├── Home.jsx
│   ├── Backtest.jsx
│   ├── PortfolioBacktest.jsx    # Portfolio backtesting page│   ├── WalkForward.jsx          # Walk-forward optimization page│   ├── ReportCenter.jsx         # Report management page│   ├── TaskCenter.jsx           # Async task monitoring│   ├── DataManagement.jsx       # Data management page│   ├── SharedReport.jsx         # Report sharing page│   ├── LiveTrading.jsx
│   └── Settings.jsx
├── services/               # API client (api.js)
├── providers/              # React context providers
│   ├── LogtoProvider.jsx         # Authentication
│   └── NotificationProvider.jsx  # Notification center
├── contexts/               # React contexts├── constants/              # Constants and configuration├── hooks/                  # Custom React hooks
├── locales/                # i18n translations (en, zh)
├── config/                 # Frontend configuration
├── i18n.js                 # Internationalization setup
└── App.jsx                 # Root component with routing
```

### Key Architectural Patterns

#### 1. **Worker Pool Isolation (NEW)**

Strategy execution is isolated in separate processes for stability and resource control:

- **Process Pool**: `worker_pool.py` manages a pool of worker processes
- **Task Models**: `task_models.py` defines IPC communication contracts
- **Workers**: Separate workers for backtest (`backtest_worker.py`) and live trading (`live_worker.py`)
- **Configuration**: Enable via `WORKER_POOL_ENABLED=true`, configure pool size with `WORKER_POOL_SIZE`
- **Benefits**: Prevents strategy crashes from affecting main server, enables resource limits per execution

#### 2. **Strategy Code Execution**

Strategies are written as Backtrader strategies in `backend/resources/strategy/*.py`. The same strategy class works for both backtesting and live trading:

- **Backtest**: `backtest_engine.py` loads strategy via `strategy_sandbox.py` (sandboxed execution)
- **Live**: `live_engine.py` uses same strategy loader with CCXT/IBKR data feeds
- **Storage**: Strategies are files on disk, editable via frontend Monaco editor

#### 3. **Portfolio Backtesting (NEW)**

Multi-asset portfolio backtesting with rebalancing support:

- **Multi-Asset Engine**: `multi_asset_backtest.py` handles multiple data feeds
- **Strategy Wrapper**: `multi_asset_strategy_wrapper.py` adapts strategies for portfolio use
- **Rebalancing**: `portfolio_rebalancer.py` implements various rebalancing strategies
- **Analyzers**: `portfolio_analyzers.py` provides portfolio-specific metrics
- **Storage**: Results stored via `portfolio.py` storage module

#### 4. **Walk-Forward Optimization (NEW)**

Out-of-sample validation to detect overfitting:

- **Optimizer**: `walkforward_optimizer.py` splits data into in-sample/out-of-sample windows
- **Validation**: Compares in-sample vs out-of-sample performance
- **Metrics**: Tracks parameter stability across windows
- **Storage**: Results stored via `walkforward.py` storage module

#### 5. **Task Queue System (NEW)**

Async task management for long-running operations:

- **Task Manager**: `task_manager.py` queues and tracks tasks
- **Task Routes**: `task_routes.py` exposes task status/results via API
- **Task Storage**: `task.py` persists task state to database
- **Frontend**: `TaskCenter.jsx` provides task monitoring UI

#### 6. **Report Generation (NEW)**

Generate and share backtest/analysis reports:

- **Generator**: `report_generator.py` creates comprehensive reports
- **Storage**: `report.py` stores reports with sharing tokens
- **Sharing**: Public report links via `SharedReport.jsx`

#### 7. **Live Trading Async/Sync Bridge**

CCXT is async-first, Backtrader is sync-first. The bridge pattern in `ccxt_store.py`:

- Background thread runs asyncio event loop
- `run_coroutine()` method executes async CCXT calls from sync Backtrader context
- Store lifecycle: `start()` → `run_coroutine()` → `stop()`

#### 8. **Session Management**

Live trading uses session-based architecture:

- `SessionManager` (`session_manager.py`) tracks multiple concurrent sessions
- Each session has: Cerebro instance, Store (CCXT/IBKR), background thread
- Sessions persist to SQLite via `session.py` for recovery
- WebSocket (`websocket_manager.py`) broadcasts session updates to frontend

#### 9. **Authentication (Optional)**

- Uses Logto for JWT-based authentication
- Enabled via `ENABLE_LOGIN=true` in `.env`
- Auth middleware in `utils/auth.py` validates JWT on protected routes
- Frontend: `LogtoProvider` wraps app, `useAuth` hook provides auth state

#### 10. **Data Flow**

**Backtest Flow**:
```
Frontend (RunStrategy) → POST /api/backtest → backtest_engine.py
  → Load strategy from resources/strategy/
  → Fetch data via datasource.py (yfinance/EODHD)
  → Run Backtrader Cerebro (optionally via worker pool)
  → Generate chart image → resources/images/
  → Store results in backtest storage
  → Return metrics + image URL
```

**Portfolio Backtest Flow**:
```
Frontend (PortfolioBacktest) → POST /api/portfolio/backtest → multi_asset_backtest.py
  → Load strategy and multiple assets
  → Apply portfolio rebalancing strategy
  → Run multi-asset Cerebro
  → Calculate portfolio-level metrics
  → Store results and return analysis
```

**Walk-Forward Flow**:
```
Frontend (WalkForward) → POST /api/walkforward → walkforward_optimizer.py
  → Split data into training/validation windows
  → Optimize parameters on in-sample data
  → Validate on out-of-sample data
  → Compare performance across windows
  → Return optimization results with stability metrics
```

**Live Trading Flow**:
```
Frontend (LiveTradingDashboard) → POST /api/live/start → live_routes.py
  → live_engine.run_live()
  → Create CCXTStore with exchange credentials
  → Create CCXTBroker + CCXTData
  → Load strategy (same code as backtest)
  → Start Cerebro in background thread
  → Store session in session storage
  → WebSocket broadcasts updates
```

## Configuration Files

### Backend Environment Variables (`.env`)

Copy `.env.template` to `.env` and configure:

- **Authentication**: `LOGTO_ISSUER`, `LOGTO_JWKS_URI`, `ENABLE_LOGIN`
- **AI Analysis**: `OPENAI_API_KEY`, `OPENAI_BASE_URL`
- **Database**: `DATABASE_URL` (SQLite by default: `trading_sessions.db`)
- **Worker Pool**: `WORKER_POOL_ENABLED`, `WORKER_POOL_SIZE`, `WORKER_TIMEOUT`
- **Exchange Credentials**: `CCXT_{EXCHANGE}_{MODE}_API_KEY/SECRET`
  - Format: `CCXT_BINANCE_PAPER_API_KEY` (testnet), `CCXT_BINANCE_LIVE_API_KEY` (production)
  - Supports: Binance, OKX, Bybit (CCXT), IBKR (via IB Gateway)
- **Proxies**: `HTTP_PROXY`, `HTTPS_PROXY` (optional)

### Broker Configuration (`backend/resources/config/broker_config.json`)

Controls exchange settings and risk management:

- **Exchange config**: Enable/disable exchanges, sandbox URLs, rate limits
- **Risk limits**: Max position size, max daily loss, max positions count
- **Trading settings**: Supported timeframes, reconnect behavior
- **Notifications**: WebSocket event configuration

**IMPORTANT**: Adjust risk limits before live trading!

### Frontend Vite Config (`frontend/vite.config.js`)

- Proxy `/api` → `http://127.0.0.1:8000` (backend)
- Proxy `/images` → `http://127.0.0.1:8000` (charts)
- Build output: `frontend/dist/` (copied to `backend/resources/frontend/` for production)

## Testing

### Commands

```bash
# Run all backend unit tests with coverage
cd backend
pytest --cov=src --cov-report=term-missing

# Or use the batch script (Windows)
cd backend
run_tests_coverage.bat

# Run smoke tests (critical health checks, fast)
python -m pytest auto_test/smoke -q

# Run e2e tests
python -m pytest auto_test/e2e -q

# Run all auto tests with batch script (Windows)
cd auto_test
run_tests.bat

# Run tests by marker
python -m pytest auto_test -m api -q      # API tests only
python -m pytest auto_test -m ui -q       # UI tests only
python -m pytest auto_test -m slow -q     # Slow tests only

# Run specific test file
python -m pytest auto_test/e2e/test_strategy_management.py -v

# Frontend lint
cd frontend && npm run lint
```

### Test Structure

- `backend/tests/` - Unit tests organized by module (db, service, routes, brokers, utils, config)
- `auto_test/smoke/` - Critical API and UI health checks (fastest, run first)
- `auto_test/e2e/` - End-to-end workflow tests:
  - `test_backtest_workflow.py` - Core backtest testing
  - `test_portfolio_workflow.py` - Portfolio backtesting  - `test_walkforward_workflow.py` - Walk-forward optimization  - `test_live_trading.py` - Live trading flows
  - `test_strategy_management.py` - Strategy CRUD
  - `test_market_data.py` - Market data endpoints
  - `test_ai_analysis.py` - AI analysis integration
  - `test_reports.py` - Report generation  - `test_tasks.py` - Task queue  - `test_settings.py` - Settings management
  - `test_websocket.py` - WebSocket connections
  - `test_site_config.py` - Site configuration
  - `test_frontend_routes.py` - Frontend serving
- `auto_test/libs/` - Reusable test utilities (api_client, assertions, data_fixtures)

### Test Markers

- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.ui` - Browser/UI tests (requires Playwright)
- `@pytest.mark.slow` - Tests taking >10 seconds
- `@pytest.mark.smoke` - Critical fast tests for health checks
- `@pytest.mark.requires_auth` - Tests requiring authentication

### Authenticated Testing

Tests auto-detect if backend requires auth. For authenticated testing:
```bash
set TEST_AUTH_TOKEN=your_jwt_token_here  # Windows
export TEST_AUTH_TOKEN=your_jwt_token_here  # Linux/Mac
python -m pytest auto_test -q
```

### CI Pipeline

GitHub Actions runs on push to main/master and all PRs:
- `backend-tests`: pytest + coverage + smoke tests (Python 3.11)
- `frontend-lint`: ESLint (Node.js 20)

### Live Trading Testing

**ALWAYS test with paper trading first!**

1. Get testnet credentials (e.g., Binance testnet: https://testnet.binance.vision/)
2. Configure `CCXT_BINANCE_PAPER_API_KEY/SECRET` in `.env`
3. Enable paper mode in `broker_config.json`
4. Start small position sizes
5. Monitor first trades closely via WebSocket dashboard

See `backend/README_LIVE_TRADING.md` for detailed live trading guide.

## Common Patterns

### Adding a New API Endpoint

1. **Define route in `backend/src/routes/`**:
   ```python
   from src.routes.common.dependencies import get_db
   from src.routes.common.auth_dependencies import get_current_user

   @router.post("/api/my_endpoint")
   def my_endpoint(request: MyRequest, user: dict = Depends(get_current_user)):
       # Logic here
       return {"result": "data"}
   ```

2. **Register router in `backend/src/service/app.py`**:
   ```python
   from src.routes.my_routes import router as my_router
   app.include_router(my_router, prefix="/api")
   ```

3. **Call from frontend in `frontend/src/services/api.js`**:
   ```javascript
   export const callMyEndpoint = async (data) => {
       return apiRequest('/api/my_endpoint', { method: 'POST', body: JSON.stringify(data) })
   }
   ```

### Adding a New Strategy

1. **Create strategy file**: `backend/resources/strategy/my_strategy.py`
   ```python
   import backtrader as bt

   class UserStrategy(bt.Strategy):
       params = (('period', 20),)

       def __init__(self):
           self.sma = bt.indicators.SMA(self.data.close, period=self.params.period)

       def next(self):
           if not self.position and self.data.close > self.sma:
               self.buy()
           elif self.position and self.data.close < self.sma:
               self.close()
   ```

2. **Strategy is automatically discovered** by `list_strategies()` in `backtest_engine.py`

3. **Use in backtest or live trading** with `strategy_name='my_strategy'`

### Adding a New Exchange

1. **Update `broker_config.json`**:
   ```json
   "my_exchange": {
       "enabled": true,
       "adapter": "ccxt",
       "ccxt_id": "kraken",
       "paper_mode": { "enabled": true, "sandbox_url": "..." }
   }
   ```

2. **Add credentials to `.env`**:
   ```
   CCXT_KRAKEN_PAPER_API_KEY=...
   CCXT_KRAKEN_PAPER_SECRET=...
   ```

3. **No code changes needed** - CCXT adapter auto-detects via `config_loader.py`

### Adding a New Async Task Type

1. **Define task in `backend/src/contracts/task.py`**
2. **Add handler in `backend/src/service/task_manager.py`**
3. **Create route in `backend/src/routes/task_routes.py`**
4. **Add frontend task status polling in `TaskCenter.jsx`**

## Troubleshooting

### "Missing API credentials" (Live Trading)

- Check `.env` has correct format: `CCXT_{EXCHANGE}_{MODE}_API_KEY`
- Verify exchange is enabled in `broker_config.json`
- Ensure credentials are for correct mode (PAPER vs LIVE)

### "Failed to start event loop" (CCXT)

- Check no other asyncio event loops running
- Restart backend to clear thread state
- See `backend/README_LIVE_TRADING.md` for CCXT troubleshooting

### Frontend shows "Network Error"

- Backend must be running on port 8000
- Check CORS is enabled in `backend/src/service/app.py`
- Verify Vite proxy config in `frontend/vite.config.js`

### Strategy not found

- Strategies must be in `backend/resources/strategy/`
- Filename must match strategy name (e.g., `sma_cross.py` → `strategy_name='sma_cross'`)
- Check file contains `class UserStrategy(bt.Strategy)`

### Database errors (SQLAlchemy)

- Default DB is SQLite: `backend/trading_sessions.db`
- For production, set `DATABASE_URL` to PostgreSQL/MySQL
- Run migrations: `python -m src.db.migrate_cleanup_json` (if needed)

### Worker pool issues

- Check `WORKER_POOL_ENABLED` is set correctly
- Verify `WORKER_POOL_SIZE` doesn't exceed system resources
- Check worker logs for process-level errors
- Disable worker pool temporarily with `WORKER_POOL_ENABLED=false` for debugging

## Security Notes

- **NEVER** enable withdrawal permissions on exchange API keys
- User strategies run in sandboxed environment (`strategy_sandbox.py`) - configure `SANDBOX_MODE` in `.env`
- `.env` is in `.gitignore` - never commit credentials
- Report sharing uses secure tokens - tokens can be revoked

## Special Considerations

### Windows Development

- Use `start_dev.bat` to launch both servers
- Path separators handled by `pathlib.Path`

### Aliyun Mirrors (China-based Development)

- Dockerfile uses Aliyun mirrors for apt and pip (faster in China)
- To use default mirrors, edit `Dockerfile` and remove `-i https://mirrors.aliyun.com/pypi/simple/`

## Related Files

- `README.md` - User-facing project documentation
- `backend/README_LIVE_TRADING.md` - Detailed live trading guide
- `auto_test/README.md` - Test suite documentation
