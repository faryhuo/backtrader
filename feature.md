# Feature Plan

## Context
- Stack: FastAPI + Backtrader backend; React (Ant Design) frontend with i18n; auth via Logto (optional) and JWT guard; assets served from `backend/resources/frontend`.
- Current APIs: `/api/data`, `/api/backtest`, `/api/strategy` (CRUD), `/api/ai_analyze` (OpenAI image/text), static frontend + images.

## Ready-to-Ship (1-3 days)
- Data layer: add db caching toggle in `datasource.get_data`; add resample/replay options in backtest payload; surface synthetic-data warning to UI.
- Strategy UX: seed example strategies in `resources/strategy`; add duplicate/rename endpoints; 1-click reset-to-sample.
- Results clarity: expose trade log table (from `trade_recorder`) in UI; CSV export; consistent timezone display.
- Auth polish: optional `ENABLE_LOGIN=false` already; add 401 toast + re-login button on token expiry.

## Next (1-2 weeks)
- Parameter optimization: new `/api/optimize` to wrap `cerebro.optstrategy`; parallel pool; return top-N configs + metrics heatmap ready data.
- Multi-ticker/portfolio: allow multiple tickers + weights; aggregate NAV & drawdown; correlation matrix + contribution chart.
- Walk-forward / validation split: train window + test window runs; overfit warnings (sharpe drop, drawdown spike).
- AI assist v2: send strategy code + trade log to `/api/ai_analyze`; model suggests risk notes and parameter tweaks.
- Notifications & scheduling: APScheduler/Celery to run daily backtest; deliver PDF/PNG to email/Slack/WeCom.

## Later (2-4 weeks)
- Live/纸面交易桥接: Backtrader Store/Broker for CCXT (spot/futures) or IBKR; account state displayed alongside backtests.
- Risk engine: per-strategy risk budget, volatility targeting, trading window filters, slippage models (fixed/percentage/volume-based).
- Metrics warehouse: persist analyzers/trade logs to DB; dashboards via Metabase/Grafana; API for historical runs.
- Collaboration: role-based strategy sharing, version history, comment threads on strategies.

## Suggested API Sketches
- `POST /api/optimize`: {ticker(s), date range, param grid, cash, commission, stake} → {top_configs, leaderboard, heatmap_data, log_id}.
- `POST /api/portfolio/backtest`: {tickers:[{symbol,weight}], rebalance, cost_model} → portfolio metrics + per-leg results.
- `POST /api/schedule`: create/update scheduled jobs; `POST /api/notify/test` for webhook/email test.

## Frontend Hooks
- Run Strategy page: add resample selector, synthetic-data warning, trade-log export; charts for annual returns and drawdown duration already present.
- Maintain page: strategy templates gallery, rename/duplicate actions, AI critique button (code + recent trades).
- DataSource page: source indicator (DB/YF/synthetic), latency badge, cache refresh control.

## Dependencies / Config
- Add optional `REDIS_URL` or DB table for cache; `OPTIMIZE_MAX_PROCS` for pools; `OPENAI_*` already present; broker creds for CCXT/IBKR gated by env.
