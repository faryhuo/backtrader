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
- Runtime user management after bootstrap still belongs to `auth_service.py` and auth routes, not the setup wizard.
