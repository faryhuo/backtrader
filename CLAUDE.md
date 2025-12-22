# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working Rules

- Before modifying any file, check whether the file's current folder contains a `*.md` "directory description" document. If it exists, **read it first** and follow its stated responsibilities, conventions, and non‑functional requirements when making changes.
- After updating code, update the corresponding directory description document if relevant.

Directory documentation files:
- `backend/src/src.md` - Backend source root overview
- `backend/src/routes/routes.md` - API routing conventions
- `backend/src/service/service.md` - Business logic layer
- `backend/src/db/db.md` - Database/persistence layer
- `backend/src/config/config.md` - Configuration management
- `backend/src/utils/utils.md` - Utility functions
- `backend/src/brokers/brokers.md` - Trading adapters overview
- `backend/src/brokers/ccxt_adapter/ccxt_adapter.md` - CCXT adapter
- `backend/src/brokers/ibkr_adapter/ibkr_adapter.md` - IBKR adapter
- `backend/resources/strategy/strategy.md` - Strategy file conventions

## Project Overview

This is a **Backtrader-based trading platform** with:
- **Backend**: FastAPI + Backtrader + SQLAlchemy (Python 3.11+)
- **Frontend**: React + Vite + Ant Design + i18next
- **Live Trading**: CCXT (crypto exchanges) and IBKR (Interactive Brokers) adapters
- **Features**: Strategy backtesting, live/paper trading, AI-powered analysis, multi-language support

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
# Development server (frontend only)
cd frontend
npm install
npm run dev  # Runs on http://localhost:5173 with proxy to backend

# Build for production
cd frontend
npm run build  # Outputs to frontend/dist/

# Lint
cd frontend
npm run lint
```

### Full Stack Development

```bash
# Windows: Start both backend and frontend
start_dev.bat  # Opens two terminal windows

# The frontend dev server proxies /api and /images to backend (see vite.config.js)
```

### Docker

```bash
# Build and run (uses .env.prod by default)
docker-compose up

# Build optimized image
bash docker-build-optimized.sh

# Note: Dockerfile uses multi-stage build with Python 3.12-slim-bookworm
# and Aliyun mirrors for China-based development
```

## Architecture

### Backend Structure

```
backend/
├── src/
│   ├── brokers/          # Live trading adapters
│   │   ├── ccxt_adapter/ # CCXT integration (crypto exchanges)
│   │   │   ├── ccxt_store.py   # Connection manager with async/sync bridge
│   │   │   ├── ccxt_broker.py  # Order execution
│   │   │   └── ccxt_data.py    # Live data feeds
│   │   └── ibkr_adapter/ # Interactive Brokers integration
│   │       └── ibkr_store.py
│   ├── config/           # Settings and configuration
│   ├── db/               # Database layer (SQLAlchemy)
│   │   ├── models.py           # Trading sessions, orders, positions
│   │   ├── backtest_storage.py # Backtest history persistence
│   │   └── session_storage.py  # Live trading session persistence
│   ├── routes/           # FastAPI route handlers
│   │   ├── api_routes.py       # /api/backtest, /api/strategy, /api/data
│   │   ├── ai_routes.py        # /api/ai_analyze (OpenAI integration)
│   │   ├── live_routes.py      # /api/live/* (trading session mgmt)
│   │   ├── websocket_routes.py # WebSocket for real-time updates
│   │   └── frontend_routes.py  # Static file serving
│   ├── service/          # Business logic
│   │   ├── app.py              # FastAPI app initialization
│   │   ├── backtest_engine.py  # Core backtesting logic
│   │   ├── live_engine.py      # Live trading orchestration
│   │   ├── session_manager.py  # Multi-session lifecycle mgmt
│   │   ├── strategy_sandbox.py # Safe strategy code execution
│   │   └── websocket_manager.py# WebSocket connection manager
│   └── utils/            # Utilities
│       ├── auth.py             # JWT authentication (Logto)
│       └── config_loader.py    # Broker config loader
├── resources/
│   ├── config/
│   │   └── broker_config.json  # Exchange settings, risk limits
│   ├── strategy/               # User strategy files (.py)
│   ├── frontend/               # Built frontend assets (served by backend)
│   └── images/                 # Generated backtest charts
├── main.py              # Entry point (Daphne ASGI server)
└── api.py               # Exports FastAPI app
```

### Frontend Structure

```
frontend/src/
├── components/          # React components
│   ├── Auth/           # Authentication (Logto provider)
│   ├── Layout/         # App shell with navigation
│   ├── RunStrategy/    # Backtest execution UI
│   ├── BacktestHistory/# Historical results browser
│   ├── LiveTrading/    # Live trading dashboard
│   ├── StrategyMaintain/# Strategy code editor (Monaco)
│   └── DataSource/     # Data source configuration
├── pages/              # Top-level page components
├── services/           # API client (api.js)
├── providers/          # React context providers
│   ├── LogtoProvider.jsx      # Authentication
│   └── NotificationProvider.jsx # Notification center
├── hooks/              # Custom React hooks
├── locales/            # i18n translations (en, zh)
├── config/             # Frontend configuration
└── App.jsx             # Root component with routing
```

### Key Architectural Patterns

#### 1. **Strategy Code Execution**

Strategies are written as Backtrader strategies in `backend/resources/strategy/*.py`. The same strategy class works for both backtesting and live trading:

- **Backtest**: `backtest_engine.py` loads strategy via `strategy_sandbox.py` (sandboxed execution)
- **Live**: `live_engine.py` uses same strategy loader with CCXT/IBKR data feeds
- **Storage**: Strategies are files on disk, editable via frontend Monaco editor

#### 2. **Live Trading Async/Sync Bridge**

CCXT is async-first, Backtrader is sync-first. The bridge pattern in `ccxt_store.py`:

- Background thread runs asyncio event loop
- `run_coroutine()` method executes async CCXT calls from sync Backtrader context
- Store lifecycle: `start()` → `run_coroutine()` → `stop()`

#### 3. **Session Management**

Live trading uses session-based architecture:

- `SessionManager` (`session_manager.py`) tracks multiple concurrent sessions
- Each session has: Cerebro instance, Store (CCXT/IBKR), background thread
- Sessions persist to SQLite via `session_storage.py` for recovery
- WebSocket (`websocket_manager.py`) broadcasts session updates to frontend

#### 4. **Authentication (Optional)**

- Uses Logto for JWT-based authentication
- Enabled via `ENABLE_LOGIN=true` in `.env`
- Auth middleware in `utils/auth.py` validates JWT on protected routes
- Frontend: `LogtoProvider` wraps app, `useAuth` hook provides auth state

#### 5. **Data Flow**

**Backtest Flow**:
```
Frontend (RunStrategy) → POST /api/backtest → backtest_engine.py
  → Load strategy from resources/strategy/
  → Fetch data via datasource.py (yfinance)
  → Run Backtrader Cerebro
  → Generate chart image → resources/images/
  → Store results in backtest_storage.py
  → Return metrics + image URL
```

**Live Trading Flow**:
```
Frontend (LiveTradingDashboard) → POST /api/live/start → live_routes.py
  → live_engine.run_live()
  → Create CCXTStore with exchange credentials
  → Create CCXTBroker + CCXTData
  → Load strategy (same code as backtest)
  → Start Cerebro in background thread
  → Store session in session_storage.py
  → WebSocket broadcasts updates
```

## Configuration Files

### Backend Environment Variables (`.env`)

Copy `.env.template` to `.env` and configure:

- **Authentication**: `LOGTO_ISSUER`, `LOGTO_JWKS_URI`, `ENABLE_LOGIN`
- **AI Analysis**: `OPENAI_API_KEY`, `OPENAI_BASE_URL`
- **Database**: `DATABASE_URL` (SQLite by default: `trading_sessions.db`)
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

# Run smoke tests (critical health checks, fast)
python -m pytest auto_test/smoke -q

# Run e2e tests
python -m pytest auto_test/e2e -q

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
- `auto_test/e2e/` - End-to-end workflow tests (backtest, live trading, walk-forward, settings)
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

## Security Notes

- **NEVER** enable withdrawal permissions on exchange API keys
- User strategies run in sandboxed environment (`strategy_sandbox.py`) - configure `SANDBOX_MODE` in `.env`
- `.env` is in `.gitignore` - never commit credentials

## Special Considerations

### Windows Development

- Use `start_dev.bat` to launch both servers
- Path separators handled by `pathlib.Path`

### Aliyun Mirrors (China-based Development)

- Dockerfile uses Aliyun mirrors for apt and pip (faster in China)
- To use default mirrors, edit `Dockerfile` and remove `-i https://mirrors.aliyun.com/pypi/simple/`
