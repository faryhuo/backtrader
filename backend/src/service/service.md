# service Directory

This directory contains application services and orchestration logic. Services sit between route handlers and storage/adapters.

## Responsibilities

- Implement business workflows.
- Coordinate storage classes, brokers, AI providers, and worker execution.
- Normalize domain errors before they reach the route layer.
- Keep reusable runtime logic out of routes.

## Conventions

- Route handlers call services; services should not depend on FastAPI request objects.
- Prefer explicit method inputs/outputs over hidden global state.
- Keep security-sensitive logic centralized.
- Long-running or isolated workloads belong in worker/sandbox components.

## Relevant Modules

- `auth_service.py`: built-in email/password authentication, password hashing, JWT issuing, and system-user lookup.
- `setup_wizard_service.py`: first-run bootstrap persistence and validation.
- `backtest_engine.py`, `live_engine.py`, `walkforward_optimizer.py`: core trading execution flows.
- `websocket_manager.py`: realtime push coordination.

## Recent Notes

- `auth_service.py` now powers the built-in `system` auth provider, including first-user bootstrap registration.
- `setup_wizard_service.py` now exposes system-user bootstrap state to onboarding and can create the first system administrator during initial setup when needed.
- `setup_wizard_service.py` must treat masked onboarding secrets as placeholders: saving should preserve the real server-side value, and connection tests should resolve masked inputs back to the stored secret before validation.
- Runtime user management after bootstrap still belongs to `auth_service.py` and auth routes, not the setup wizard.
- `auth_service.py` also owns startup-time bootstrap for the first built-in admin: when `AUTH_PROVIDER=system`, no users exist, and `SYSTEM_ADMIN_EMAIL` plus `SYSTEM_ADMIN_PASSWORD` are present in the environment, startup should create that admin in the database exactly once.
- `live_engine.py` now needs to normalize account snapshots separately for Binance `spot` and `futures`, because order history, balances, positions, and portfolio value are sourced from different exchange payloads.
- `live_engine.py` now also owns the small runtime config surface used by the live launcher for the Binance paper test URL, and paper-session startup passes that URL into the Binance store.
- `live_engine.py` should provide live-chart OHLCV backfill with a timeframe-aware lookback window instead of a single fixed candle count, so the frontend can keep more natural chart context across `1s` / `1m` / `1h` sessions.
