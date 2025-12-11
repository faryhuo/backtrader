# Live/Paper Trading with CCXT

This guide explains how to use the live/paper trading functionality with cryptocurrency exchanges.

## Phase 1 Status: CCXT Foundation ✅

**Implemented:**
- ✅ CCXT Store (connection manager)
- ✅ CCXT Broker (order execution)
- ✅ CCXT Data (live data feeds)
- ✅ Live Engine (trading orchestration)
- ✅ Broker configuration system
- ✅ Environment variable management

**Coming in Phase 2:**
- Session management (start/stop/status)
- REST API endpoints
- Database persistence

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- `ccxt>=4.2.0` - Exchange connectivity
- `websockets>=12.0` - Real-time updates (Phase 3)
- `aiohttp>=3.9.0` - Async HTTP support
- `aiodns>=3.0,<4.0` - Async DNS resolver (pinned for pycares compatibility)
- `pycares>=4.3,<5.0` - Required by aiodns; pycares 5.x removes ares_query_a_result
- `pydantic>=2.5.0` - Configuration validation

> If you hit `AttributeError: module 'pycares' has no attribute 'ares_query_a_result'` during ccxt import, reinstall the resolver stack to pull the pinned versions:
> ```bash
> pip install "aiodns>=3.0,<4.0" "pycares>=4.3,<5.0" --force-reinstall
> ```

### 2. Get Exchange API Keys

**For Binance Testnet (Recommended for testing):**
1. Visit: https://testnet.binance.vision/
2. Create account and generate API key
3. Save API Key and Secret

**For Live Trading (After thorough testing only!):**
1. Create API key on your exchange
2. **IMPORTANT:** Enable trading permissions ONLY (no withdrawal)
3. Enable IP whitelist if possible
4. Enable 2FA on your account

### 3. Configure Environment Variables

```bash
# Copy template
cp .env.template .env

# Edit .env and add your API keys
CCXT_BINANCE_PAPER_API_KEY=your_testnet_api_key
CCXT_BINANCE_PAPER_SECRET=your_testnet_secret
```

### 4. Configure Broker Settings

The broker configuration is in `backend/resources/config/broker_config.json`:

```json
{
  "exchanges": {
    "binance": {
      "enabled": true,
      "paper_mode": {
        "enabled": true,
        "initial_balance_usdt": 10000
      }
    }
  },
  "risk_management": {
    "position_limits": {
      "max_position_size_usd": 5000,
      "max_positions_count": 5
    },
    "loss_limits": {
      "max_daily_loss_usd": 500
    }
  }
}
```

**Adjust risk limits based on your tolerance!**

## Usage (Phase 1)

### Python API

```python
from src.service.live_engine import run_live

# Start paper trading session
session = run_live(
    strategy_name='sma_cross',  # Your strategy name
    symbol='BTC/USDT',           # Trading pair
    exchange='binance',          # Exchange ID
    mode='paper',                # 'paper' or 'live'
    timeframe='1m',              # Bar timeframe
    initial_cash=10000.0,        # Starting balance (paper mode)
    commission=0.001             # 0.1% commission
)

print(f"Session ID: {session['session_id']}")
print(f"Status: {session['status']}")
```

### Test Script

Create `test_live_trading.py`:

```python
import time
import logging
from src.service.live_engine import run_live

logging.basicConfig(level=logging.INFO)

# Start paper trading
session = run_live(
    strategy_name='sma_cross',
    symbol='BTC/USDT',
    exchange='binance',
    mode='paper',
    timeframe='1m',
    initial_cash=10000.0
)

print(f"Started session: {session['session_id']}")
print("Trading live... Press Ctrl+C to stop")

try:
    while True:
        time.sleep(10)
except KeyboardInterrupt:
    print("\nStopping...")
    # TODO: Implement stop_live() in Phase 2
```

Run:
```bash
cd backend
python test_live_trading.py
```

## Architecture

### Component Overview

```
run_live()
    ↓
CCXTStore (connection manager)
    → Creates CCXT exchange instance
    → Manages async event loop in background thread
    → Handles reconnection on failures
    ↓
CCXTBroker (order execution)
    → Submits orders to exchange
    → Tracks positions and cash
    → Processes order fills
    ↓
CCXTData (data feed)
    → Fetches real-time OHLCV bars
    → Polls exchange for latest data
    → Provides bars to strategy
    ↓
Backtrader Cerebro
    → Runs strategy.next() on each bar
    → Generates buy/sell signals
    → Routes orders to CCXTBroker
```

### Async/Sync Bridge

CCXT is async, Backtrader is sync. The bridge works like this:

1. **CCXTStore** runs asyncio event loop in background thread
2. **run_coroutine()** method executes async operations from sync context
3. **Background thread** keeps event loop alive for concurrent operations

Example:
```python
# Sync context (Backtrader)
store = CCXTStore('binance', 'paper')
store.start()

# Execute async CCXT operation from sync code
balance = store.run_coroutine(
    store.get_exchange().fetch_balance()
)
```

## Supported Exchanges

| Exchange | Status | Paper Mode | Notes |
|----------|--------|------------|-------|
| Binance | ✅ Ready | ✅ Yes | testnet.binance.vision |
| OKX | 🚧 Phase 5 | ✅ Yes | Requires passphrase |
| Bybit | 🚧 Phase 5 | ✅ Yes | api-testnet.bybit.com |

## Supported Timeframes

- `1m` - 1 minute
- `5m` - 5 minutes
- `15m` - 15 minutes
- `30m` - 30 minutes
- `1h` - 1 hour
- `4h` - 4 hours
- `1d` - 1 day

## Strategy Compatibility

**Same strategy code works for both backtest and live trading!**

Example strategy (`backend/resources/strategy/sma_cross.py`):

```python
import backtrader as bt

class UserStrategy(bt.Strategy):
    params = (
        ('fast_period', 10),
        ('slow_period', 30),
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(self.data.close, period=self.params.fast_period)
        self.slow_ma = bt.indicators.SMA(self.data.close, period=self.params.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        else:
            if self.crossover < 0:
                self.close()
```

This strategy runs identically in:
- **Backtest mode:** `run_backtest(strategy_name='sma_cross', ...)`
- **Live mode:** `run_live(strategy_name='sma_cross', ...)`

## Troubleshooting

### "Missing API credentials" error

**Solution:** Check your `.env` file has the correct format:
```bash
CCXT_BINANCE_PAPER_API_KEY=your_key
CCXT_BINANCE_PAPER_SECRET=your_secret
```

Variable name must match: `CCXT_{EXCHANGE}_{MODE}_{KEY_TYPE}`

### "Unsupported exchange" error

**Solution:**
1. Check exchange ID is correct (use `binance`, not `Binance`)
2. Ensure exchange is enabled in `broker_config.json`

### "Failed to start event loop" error

**Solution:** This indicates asyncio thread startup issue. Check:
1. No other event loops running
2. Python version >= 3.8

### Orders not executing

**Checklist:**
1. ✅ API keys are correct and active
2. ✅ Paper mode URL is correct (testnet for Binance)
3. ✅ Symbol is valid (e.g., 'BTC/USDT' not 'BTCUSDT')
4. ✅ Sufficient balance in paper trading account
5. ✅ Check logs for CCXT errors

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Best Practices

### For Paper Trading (Testnet)
- ✅ Use testnet API keys (separate from live account)
- ✅ Never share testnet keys publicly
- ✅ Rotate keys periodically

### For Live Trading (Production)
- ⚠️ **START WITH SMALL POSITION SIZES**
- ⚠️ Test extensively with paper trading first (minimum 1 week)
- ✅ Create API keys with trading-only permissions (NO WITHDRAWAL)
- ✅ Enable IP whitelist on exchange
- ✅ Enable 2FA on exchange account
- ✅ Monitor first trades closely
- ✅ Set conservative risk limits in `broker_config.json`
- ✅ Never commit `.env` to version control

### API Key Permissions

When creating API keys on exchange:
```
✅ Spot Trading     - ENABLE
✅ Futures Trading  - ENABLE (if needed)
❌ Withdrawal       - DISABLE
❌ Account Transfer - DISABLE
```

## Logs and Monitoring

### Log Levels

```python
import logging

# Info level (recommended)
logging.basicConfig(level=logging.INFO)

# Debug level (for troubleshooting)
logging.basicConfig(level=logging.DEBUG)
```

### What to Monitor

**During paper trading:**
- Order submission confirmations
- Order fill prices (check for slippage)
- Position updates
- Cash balance changes
- Any errors or warnings

**During live trading (additionally):**
- Compare strategy signals with actual fills
- Monitor exchange balance vs. broker balance
- Check for network disconnections
- Verify risk limits are enforced

## Next Steps

### Phase 2: Session Management (Week 3)
- Implement SessionManager for multi-session support
- Add REST API endpoints:
  - `POST /api/live/start` - Start session
  - `POST /api/live/stop` - Stop session
  - `GET /api/live/status/{id}` - Get status
- Database persistence for sessions

### Phase 3: WebSocket Monitoring (Week 4)
- Real-time dashboard
- WebSocket updates for positions, orders, P&L
- Frontend React components

### Phase 4: Risk Management (Week 5)
- Pre-trade validation
- Emergency stops
- Position limits enforcement

### Phase 5: Multi-Exchange (Week 6)
- Enable OKX and Bybit
- Exchange-specific configurations

### Phase 6: Live Trading (Week 7-8)
- Enable live mode
- Advanced order types
- Security audit

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review logs for error messages
3. Verify configuration files
4. Create issue on GitHub

## License

Same as main project.
