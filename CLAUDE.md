# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **web-based algorithmic trading backtesting platform** that allows users to design and test trading strategies using the Backtrader library. The platform features:
- Strategy editor with Monaco code editor
- Historical backtesting on financial market data
- AI-powered strategy analysis using GPT-4
- Interactive candlestick charts and trade execution logs
- Multiple pre-built strategy templates

## Architecture

The project uses a **full-stack architecture** with clear separation:

```
Frontend (React/Vite SPA) ←→ Backend (FastAPI/Python)
                              ↓
                          Backtrader Engine
```

**Communication:**
- Frontend communicates via REST API at `/api/*` endpoints
- In development: Vite dev server proxies API calls to `http://127.0.0.1:8000`
- In production: Backend serves frontend as static files from `/backend/resources/frontend/`

## Technology Stack

**Frontend:**
- React 18.3.1 with Vite 6.0.5 bundler
- Ant Design (antd) for UI components
- Monaco Editor for code editing
- Lightweight Charts for financial charts
- React Router DOM for client-side routing
- i18next for internationalization

**Backend:**
- Python 3.12
- FastAPI for REST API
- Daphne ASGI server
- Backtrader 1.9.78.123 for backtesting
- yfinance for market data
- Matplotlib for plot generation (Agg backend for headless rendering)
- OpenAI API for AI analysis

## Development Commands

### Setup
```bash
# Full build (installs dependencies and builds frontend)
build.bat

# Frontend only
cd frontend
npm install
npm run build  # Output goes to frontend/dist/
```

### Development Mode
```bash
# Start both frontend and backend in dev mode (recommended)
start_dev.bat

# Or manually:
# Terminal 1 - Backend (port 8000)
cd backend
python main.py

# Terminal 2 - Frontend (port 5173)
cd frontend
npm run dev
```

### Frontend Commands
```bash
cd frontend
npm run dev      # Start Vite dev server with hot reload (port 5173)
npm run build    # Build for production → dist/
npm run lint     # Run ESLint
npm run preview  # Preview production build
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build

# Access at http://localhost:8020
```

## Code Architecture Details

### Backend Structure (`/backend/`)

**Core Files:**
- [`main.py`](backend/main.py) - Entry point, starts Daphne ASGI server
- [`api.py`](backend/api.py) - FastAPI app initialization, CORS middleware, router registration
- [`backtest_engine.py`](backend/backtest_engine.py) - Core backtesting logic (262 lines)
  - Strategy loading from files
  - Backtrader Cerebro orchestration
  - Custom `TradeRecorder` analyzer for detailed trade logs
  - Metrics calculation (Sharpe ratio, drawdown, returns, etc.)
  - Matplotlib plot generation
- [`datasource.py`](backend/datasource.py) - Market data fetching with fallback priority:
  1. Database (if `DATABASE_URL` set)
  2. yfinance (Yahoo Finance API)
  3. Synthetic data (monotonic series as last resort)

**Routes (`/backend/routes/`):**
- [`api_routes.py`](backend/routes/api_routes.py) - Main API endpoints (151 lines)
  - `GET /api/strategies` - List available strategies
  - `POST /api/data` - Fetch market data (OHLCV)
  - `POST /api/backtest` - Run backtest with parameters
  - `GET /api/strategy?name=X` - Get strategy code
  - `POST /api/strategy` - Save/update strategy code
  - `POST /api/analyze` - Basic text analysis
- [`ai_routes.py`](backend/routes/ai_routes.py) - AI analysis endpoints (68 lines)
  - `POST /api/ai_analyze` - GPT-4 analysis of charts/code
- [`frontend_routes.py`](backend/routes/frontend_routes.py) - SPA serving (41 lines)
  - Serves built frontend from `/backend/resources/frontend/`
  - Mounts `/images/*` for generated plot images
  - Catch-all routing for SPA

**Strategy Templates (`/backend/strategy/`):**
All strategies inherit from `bt.Strategy` with required methods:
- `__init__()` - Initialize indicators
- `next()` - Execute on each bar

Available templates:
- [`sma_cross.py`](backend/strategy/sma_cross.py) - Fast/slow SMA crossover (trend-following)
- [`breakout.py`](backend/strategy/breakout.py) - Highest/lowest breakout with stop-loss/take-profit
- [`rsi_reversion.py`](backend/strategy/rsi_reversion.py) - RSI mean reversion
- [`buy_and_hold.py`](backend/strategy/buy_and_hold.py) - Buy-and-hold baseline

### Frontend Structure (`/frontend/`)

**Entry Point:**
- [`main.jsx`](frontend/src/main.jsx) - React entry point
- [`App.jsx`](frontend/src/App.jsx) - Root component with React Router routing

**Pages (`/src/pages/`):**
- [`RunStrategy.jsx`](frontend/src/pages/RunStrategy.jsx) - Main backtesting interface
- [`StrategyMaintain.jsx`](frontend/src/pages/StrategyMaintain.jsx) - Strategy code editor
- [`DataSource.jsx`](frontend/src/pages/DataSource.jsx) - Market data viewer

**Components (`/src/components/`):**
- `Layout/Layout.jsx` - App shell with navigation
- `RunStrategy/` - Backtest configuration, metrics display, trade log, charts, AI insights
- `StrategyMaintain/` - Strategy selector, Monaco editor, save/analyze actions
- `DataSource/` - Candlestick chart viewer

**Services (`/src/services/`):**
- [`api.js`](frontend/src/services/api.js) - API client with all backend endpoints
- [`aiAnalysis.js`](frontend/src/services/aiAnalysis.js) - AI analysis service wrapper

### Backtest Execution Flow

```
1. User fills form in RunStrategy page (ticker, dates, cash, strategy)
   ↓
2. Frontend calls POST /api/backtest
   ↓
3. Backend (api_routes.py) → run_backtest() in backtest_engine.py
   ↓
4. Load strategy class from /backend/strategy/{name}.py
   ↓
5. Fetch market data via datasource.py (DB → yfinance → synthetic)
   ↓
6. Initialize Backtrader Cerebro engine:
   - Add strategy + data feed
   - Set broker params (cash, commission, stake)
   - Add analyzers: SharpeRatio, DrawDown, Returns, AnnualReturn,
     SQN, TradeAnalyzer, TimeDrawDown, TradeRecorder (custom)
   ↓
7. Run backtest → collect metrics → generate PNG plot
   ↓
8. Return JSON with metrics, trades, plot URL
   ↓
9. Frontend displays: performance metrics, trade log, candlestick chart
```

## Important Implementation Details

### Custom TradeRecorder Analyzer
Located in [`backtest_engine.py`](backend/backtest_engine.py), this custom Backtrader analyzer captures:
- Open/close prices, dates, commissions
- P&L and return percentages
- Holding periods
- Aggregated trade statistics

### Path Sanitization
Strategy file paths are sanitized in [`api_routes.py`](backend/routes/api_routes.py) to prevent directory traversal attacks. Only alphanumeric, underscore, and hyphen characters are allowed in strategy names.

### Matplotlib Configuration
Backend uses Agg backend (`matplotlib.use('Agg')`) for headless rendering. This is required for server environments without display capabilities.

### Frontend Build Process
1. `npm run build` in `/frontend/` creates production bundle in `dist/`
2. `build.bat` copies `dist/` to `/backend/resources/frontend/`
3. Backend serves frontend via [`frontend_routes.py`](backend/routes/frontend_routes.py)
4. SPA routing handled by catch-all route that serves `index.html`

### Environment Variables
Backend reads from `.env` file (use python-dotenv):
- `OPENAI_API_KEY` - Required for AI analysis features
- `DATABASE_URL` - Optional, for database-backed data source
- `PORT` - Server port (default: 8000)
- `HOST` - Server host (default: 0.0.0.0)

### Vite Proxy Configuration
In development, Vite proxies requests in [`vite.config.js`](frontend/vite.config.js):
- `/api/*` → `http://127.0.0.1:8000/api/*` (rewrite removes `/api` prefix at backend)
- `/images/*` → `http://127.0.0.1:8000/images/*`

**IMPORTANT:** The Vite proxy rewrites `/api` to `/` at the backend. Backend routes are defined without `/api` prefix in route files, but the FastAPI router mounts them with `prefix="/api"` in [`api.py`](backend/api.py).

## Writing New Strategies

To create a new strategy:

1. Create a new file in [`/backend/strategy/`](backend/strategy/)
2. Inherit from `bt.Strategy`
3. Implement required methods:
   ```python
   import backtrader as bt

   class MyStrategy(bt.Strategy):
       params = (
           ('param1', default_value),
       )

       def __init__(self):
           # Initialize indicators
           self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=20)

       def next(self):
           # Execute on each bar
           if not self.position:
               if self.data.close[0] > self.sma[0]:
                   self.buy()
           else:
               if self.data.close[0] < self.sma[0]:
                   self.close()
   ```

4. Strategy file must contain exactly one class inheriting from `bt.Strategy`
5. File naming: use lowercase with underscores (e.g., `my_strategy.py`)

## Docker Multi-Stage Build

The [`Dockerfile`](Dockerfile) uses a two-stage build:

**Stage 1 (builder):**
- Installs build dependencies (gcc, build-essential, etc.)
- Builds Python wheels from `requirements.txt`
- Stores wheels in `/wheels`

**Stage 2 (runtime):**
- Uses Python 3.12-slim base (smaller)
- Installs only runtime libraries (no build tools)
- Installs from pre-built wheels (faster, offline)
- Copies application code
- Exposes port 8000

Benefits: Smaller final image size (~200MB vs ~800MB), faster builds with layer caching

## Testing Strategy Code

There's currently no automated test suite. To test strategies:

1. Use the web interface at `RunStrategy` page
2. Select strategy, configure parameters (ticker, dates, cash)
3. Click "Run Backtest"
4. Review metrics (Sharpe ratio, max drawdown, total return)
5. Check trade log for execution details
6. Use AI analysis for insights

For debugging:
- Add `print()` statements in strategy code (visible in backend console)
- Check backend logs for errors during strategy loading/execution
- Verify strategy class name matches file name convention
