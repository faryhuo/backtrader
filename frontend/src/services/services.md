# services Directory

Frontend service modules live here. They wrap backend APIs, websocket access, and selected external data sources behind reusable interfaces.

## Responsibilities

- Keep request construction, response parsing, and transport details out of pages and feature components.
- Group service methods by business domain instead of accumulating everything in one large file.
- Normalize failures so callers can handle domain-level errors consistently.

## Conventions

- Add new domain files when a feature owns a clear API surface.
- Keep `api.js` as a compatibility aggregator, but prefer direct imports from domain modules in new code.
- Avoid UI coupling in service modules; return plain data objects that pages and hooks can shape further.

## Current Modules

- `apiCore.js`: shared request helpers and auth token wiring.
- `basisApi.js`: OKX public funding-rate and ticker snapshots for the basis arbitrage page.
- `strategyApi.js`, `backtestApi.js`, `marketDataApi.js`, `liveApi.js`, `walkforwardApi.js`, `settingsApi.js`, `portfolioApi.js`, `reportApi.js`, `authApi.js`, `setupApi.js`: domain services for app features.
- `websocket.js`: realtime websocket management.

## Recent Notes

- `basisApi.js` now fetches synchronized spot, perpetual, and funding-rate data from OKX public endpoints for the basis arbitrage monitor.
