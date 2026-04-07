# routes Directory

FastAPI route modules live here. Each `{feature}_routes.py` file owns request validation, dependency wiring, and HTTP response shaping for one feature area.

## Responsibilities

- Keep route handlers thin.
- Validate request payloads with Pydantic models.
- Delegate business logic to `backend/src/service/`.
- Use shared dependencies from `routes/common/`.
- Avoid direct database logic in route handlers.

## Key Modules

- `auth_routes.py`: built-in system authentication endpoints for email/password login.
- `settings_routes.py`: user settings, credentials, and frontend auth config.
- `site_config_routes.py`: public site metadata and admin site settings.
- `setup_routes.py`: first-run onboarding bootstrap endpoints.
- `strategy_routes.py`, `backtest_routes.py`, `portfolio_routes.py`, `walkforward_routes.py`, `live_routes.py`, `basis_routes.py`: trading workflows.
- `websocket_routes.py`: realtime push channels.
- `frontend_routes.py`: frontend asset mounting.

## Conventions

- Register all routers in `backend/api.py`.
- Use dependency injection instead of constructing storage/services inline when a shared provider exists.
- Return stable JSON payloads and raise `HTTPException` for client-facing failures.
- Keep auth checks at the route boundary with `Depends(...)`.

## Recent Notes

- `auth_routes.py` now provides `/api/auth/config`, `/api/auth/login`, `/api/auth/register`, and `/api/auth/me`.
- `settings_routes.py` now exposes frontend auth configuration for both `logto` and built-in `system` providers from the existing `/api/settings/logto-config` endpoint.
- `live_routes.py` now treats Binance `market` as an explicit request/query parameter so spot and futures sessions, symbol lookup, and symbol-rule lookup share one route surface.
- `live_routes.py` now also exposes `/api/live/config` so the launcher page can read and update the Binance paper test URL without going through the first-run setup wizard.
- `live_routes.py` should pass through optional OHLCV lookback parameters without reintroducing a fixed frontend-facing candle count default.
- `basis_routes.py` now exposes a standalone basis-arbitrage surface for preview, credential status, paper state, and explicit open/close actions without routing through the live session engine.
- `market_data_routes.py` now also exposes `/api/instruments/catalog` for the backtest instrument picker's platform/type/code workflow.
