# LiveTrading Directory

Frontend UI components for live and paper trading.

## Responsibilities
- `LiveConfigForm.jsx`: session launcher workspace for strategy, market, execution mode, position sizing, strategy parameter overrides, exchange-backed mode selection, costs, and pre-launch summary.
  - Live timeframe options include sub-minute intervals such as `1s` when the backend exchange config exposes them.
- `SessionControls.jsx`: session status bar for runtime status, feed status (`warming_up` / `live`), elapsed time, and stop / refresh actions.
- `PriceChart.jsx`: candlestick chart that prefers WebSocket OHLCV / ticker data and falls back to REST when needed.
- `PnLChart.jsx`: PnL curve for the running session.
- `PositionTable.jsx`: open positions and unrealized PnL.
- `OrderLog.jsx`: grouped exchange order history with three sections: open orders, recent fills, and historical closed orders; still-open orders expose cancel entry points.
- `TradeErrorPanel.jsx`: fixed panel for the most recent trading errors from broker / exchange rejections.
- `StrategyLog.jsx`: strategy log panel backed by WebSocket first and REST fallback second.
- `useLiveTrading` REST fallback must refresh exchange-backed `orders` and `positions`, not only logs/ticker/OHLCV.

## Boundaries
- State and side effects stay in hooks; components stay presentational.
- Components consume normalized `session` / `order` / `position` / `pnl` / `ticker` data and do not call APIs directly.
- The UI must work with both WebSocket updates and REST fallback polling.
- For live and paper sessions, the fallback source of truth for open positions and order history is the exchange API exposed by backend live endpoints.

## Data Contracts
- Market messages include `ticker`, `ohlcv`, and `feed_status`.
- Trading messages include `order`, `position`, `trade`, `pnl`, and `log`.
- Prefer stable keys such as `session_id` and `order_id` for rendered lists.

## Maintenance Rules
- Keep user-facing text in i18n files instead of hardcoding strings in components.
- Extend `useLiveTrading` before adding duplicated polling or WebSocket logic inside components.
- Keep `paper` and `live` mode differences out of purely visual components.
- Keep the launcher information hierarchy explicit: strategy/market first, execution mode second, strategy parameters and exchange balance source after that, launch summary last.

