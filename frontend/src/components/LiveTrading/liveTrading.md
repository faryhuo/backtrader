# LiveTrading Directory

Frontend UI components for live and paper trading.

## Responsibilities
- `LiveConfigForm.jsx`: session launcher workspace for strategy, market (`spot` / `futures`), execution mode, position sizing, strategy parameter overrides, exchange-backed mode selection, costs, and pre-launch summary.
  - Live timeframe options are intentionally limited to `1m`, `5m`, `15m`, `1h`, `4h`, and `1d` so the launcher stays aligned with the supported trading UX.
- `LiveCredentialPanel.jsx`: launcher-adjacent access settings for Binance paper/live API keys plus the paper test URL used by the backend runtime config.
- `SessionControls.jsx`: session status bar for runtime status, feed status (`warming_up` / `live`), elapsed time, and stop / refresh actions.
- `PriceChart.jsx`: candlestick chart that prefers WebSocket OHLCV / ticker data and falls back to REST when needed.
  - Keep the chart on incremental updates: initialize series once, merge/dedupe OHLCV history by bar time, and update the active candle from ticker pushes instead of resetting the full series on every quote.
  - Avoid a fixed global candle count for the live chart; request a timeframe-aware lookback window so short and long intervals both open with enough context.
- `PnLChart.jsx`: PnL curve for the running session.
- `PositionTable.jsx`: open positions and unrealized PnL.
- `OrderBookPanel.jsx`: exchange order book depth with top 5 / top 10 view, best bid/ask, and spread.
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
- REST market fallbacks also include `orderBook` depth snapshots for the active symbol.
- Trading messages include `order`, `position`, `trade`, `pnl`, and `log`.
- Prefer stable keys such as `session_id` and `order_id` for rendered lists.

## Maintenance Rules
- Keep user-facing text in i18n files instead of hardcoding strings in components.
- Extend `useLiveTrading` before adding duplicated polling or WebSocket logic inside components.
- Keep `paper` / `live` mode differences and `spot` / `futures` market differences out of purely visual components whenever possible.
- Keep the launcher information hierarchy explicit: strategy/market first, execution mode second, strategy parameters and exchange balance source after that, launch summary last.
- Launcher-adjacent access settings may save credentials or runtime config, but session start/stop state still belongs to `useLiveTrading`.

