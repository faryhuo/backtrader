# Database Layer (`db`)

This directory contains all database-related code including SQLAlchemy models, storage classes, and data fetching modules.

## Directory Structure

```
db/
|-- __init__.py              # Package exports - re-exports all models and storage classes
|-- db.md                    # This documentation file
|-- models/                  # SQLAlchemy model definitions
|   |-- __init__.py          # Exports all models for backward compatibility
|   |-- base.py              # Base class, SafeJSON, Enums, init_database
|   |-- trading.py           # TradingSessionModel, OrderModel, PositionModel
|   |-- backtest.py          # BacktestHistoryModel, PortfolioResultModel, WalkForwardOptimizationModel
|   |-- market.py            # MarketDataModel, TickerMetadataModel
|   `-- user.py              # UserSettingsModel, StrategyVersionModel
`-- storage/                 # Storage classes and data modules
    |-- __init__.py          # Exports all storage classes and data functions
    |-- base.py              # BaseStorage class with common database session management
    |-- backtest.py          # BacktestStorage - CRUD for backtest history
    |-- session.py           # SessionStorage - trading session persistence
    |-- settings.py          # SettingsStorage - user settings and credentials
    |-- walkforward.py       # WalkForwardStorage - walk-forward optimization results
    |-- portfolio.py         # PortfolioStorage - portfolio backtest results
    |-- strategy_version.py  # StrategyVersionStorage - strategy version control
    |-- market_data.py       # Market data fetching (yfinance) with DB caching
    `-- ticker_metadata.py   # Ticker info fetching and validation
```

## Key Components

### Models (`models/`)
- **base.py**: Contains `Base`, `SafeJSON` type decorator, `SessionStatusEnum`, `OrderStatusEnum`, and `init_database` function
- **trading.py**: Models for live trading sessions, orders, and positions
- **backtest.py**: Models for backtest history, portfolio results, and walk-forward optimizations
- **market.py**: Models for market data (OHLCV) and ticker metadata caching
- **user.py**: Models for user settings and strategy version tracking

### Storage (`storage/`)
- **BaseStorage**: Common base class with database initialization and session management
- **BacktestStorage**: Manages backtest history with auto-cleanup and AI analysis storage
- **SessionStorage**: Handles trading session persistence and order tracking
- **SettingsStorage**: Encrypted credential storage with environment variable fallback
- **WalkForwardStorage**: Stores walk-forward optimization results
- **PortfolioStorage**: Persists portfolio backtest results
- **StrategyVersionStorage**: Version control for strategy code
- **market_data.py**: Fetches OHLCV data from yfinance with database caching
- **ticker_metadata.py**: Fetches and validates ticker information with caching

## Usage

Import from the package directly:

```python
# Import storage classes
from src.db import BacktestStorage, SessionStorage, SettingsStorage

# Import models
from src.db import TradingSessionModel, BacktestHistoryModel

# Import data functions
from src.db import get_data, get_bt_feed, get_ticker_metadata

# Or import from subpackages
from src.db.models import Base, init_database
from src.db.storage import BacktestStorage, get_raw_data_json
```

## Conventions

1. **Database URL Configuration**: Always import `DATABASE_URL` and `DEFAULT_DB_URL` from `src.config.settings`
2. **Session Management**: Use `BaseStorage.session_scope()` context manager for automatic commit/rollback
3. **Model Naming**: Models end with `Model` suffix (e.g., `TradingSessionModel`)
4. **Storage Naming**: Storage classes end with `Storage` suffix (e.g., `BacktestStorage`)

## Recent Notes

- `user_settings` now supports unified AI provider settings via `ai_provider_priority` and `ai_provider_configs`.
- Legacy `openai_api_key` and `openai_base_url` are retained for backward compatibility and migration fallback.
- `system_users` now stores built-in email/password accounts for the new system authentication flow.
- `user_settings` now also persists auth configuration such as `auth_provider` and `system_auth_allow_registration`.
- `user_settings.setup_completed` now tracks whether first-run onboarding has finished, and setup readiness should read that database flag instead of inferring readiness only from `.env`.
