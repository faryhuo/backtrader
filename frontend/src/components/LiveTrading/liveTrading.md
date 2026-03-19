# LiveTrading Directory

Frontend UI components for live and paper trading.

## Responsibilities
- `LiveConfigForm.jsx`: session launcher workspace for strategy, market, execution mode, strategy parameter overrides, exchange-backed mode selection, costs, and pre-launch summary.
- `SessionControls.jsx`: session status bar for runtime status, feed status (`warming_up` / `live`), elapsed time, and stop / refresh actions.
- `PriceChart.jsx`: candlestick chart that prefers WebSocket OHLCV / ticker data and falls back to REST when needed.
- `PnLChart.jsx`: PnL curve for the running session.
- `PositionTable.jsx`: open positions and unrealized PnL.
- `OrderLog.jsx`: order stream with cancel entry points.
- `StrategyLog.jsx`: strategy log panel backed by WebSocket first and REST fallback second.

## Boundaries
- State and side effects stay in hooks; components stay presentational.
- Components consume normalized `session` / `order` / `position` / `pnl` / `ticker` data and do not call APIs directly.
- The UI must work with both WebSocket updates and REST fallback polling.

## Data Contracts
- Market messages include `ticker`, `ohlcv`, and `feed_status`.
- Trading messages include `order`, `position`, `trade`, `pnl`, and `log`.
- Prefer stable keys such as `session_id` and `order_id` for rendered lists.

## Maintenance Rules
- Keep user-facing text in i18n files instead of hardcoding strings in components.
- Extend `useLiveTrading` before adding duplicated polling or WebSocket logic inside components.
- Keep `paper` and `live` mode differences out of purely visual components.
- Keep the launcher information hierarchy explicit: strategy/market first, execution mode second, strategy parameters and exchange balance source after that, launch summary last.

