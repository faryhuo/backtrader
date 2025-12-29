# Portfolio Strategy Guide

This guide explains how to write trading strategies for multi-asset portfolio backtesting in the Backtrader platform.

## Table of Contents

1. [Overview](#overview)
2. [Multi-Data Strategy Pattern](#multi-data-strategy-pattern)
3. [Accessing Multiple Assets](#accessing-multiple-assets)
4. [Position Sizing](#position-sizing)
5. [Rebalancing](#rebalancing)
6. [Examples](#examples)
7. [Common Pitfalls](#common-pitfalls)

---

## Overview

Portfolio backtesting differs from single-asset backtesting in several key ways:

- **Multiple data feeds**: Your strategy accesses multiple assets via `self.datas[0]`, `self.datas[1]`, etc.
- **Strategy-controlled sizing**: You specify exact position sizes (number of shares)
- **Ticker mapping**: Asset order matches your API call's `tickers` array
- **Rebalancing coexistence**: Auto-rebalancing (if configured) runs alongside your strategy signals

**Key Difference from Single-Asset Strategies:**

| Single-Asset Strategy | Portfolio Strategy |
|-----------------------|-------------------|
| `self.data.close[0]` | `self.datas[0].close[0]` for first asset |
| One data feed | Multiple data feeds (`self.datas`) |
| Position sizing via sizer | Direct position sizing via `size` parameter |
| Trade one asset | Trade multiple assets independently or cross-asset logic |

---

## Multi-Data Strategy Pattern

### How It Works

When you run a portfolio backtest with `tickers=['AAPL', 'GOOGL', 'MSFT']`:

1. Backtrader creates **one Cerebro instance** with **three data feeds**
2. Your strategy receives all three feeds via `self.datas`
3. Ticker-to-data mapping:
   - `self.datas[0]` → AAPL
   - `self.datas[1]` → GOOGL
   - `self.datas[2]` → MSFT

### Basic Template Structure

```python
import backtrader as bt

class UserStrategy(bt.Strategy):
    params = (
        ('period', 20),
        ('position_size', 100),
    )

    def __init__(self):
        # Create indicators for each asset
        self.smas = []
        for data in self.datas:
            sma = bt.indicators.SMA(data.close, period=self.p.period)
            self.smas.append(sma)

    def next(self):
        # Trading logic called every bar
        for i, data in enumerate(self.datas):
            # Your trading logic here
            pass
```

---

## Accessing Multiple Assets

### Iterating Over Assets

**Pattern 1: Index-based access**

```python
def next(self):
    for i in range(len(self.datas)):
        data = self.datas[i]
        price = data.close[0]
        sma = self.smas[i]
        # Trade logic
```

**Pattern 2: Enumerate (recommended)**

```python
def next(self):
    for i, data in enumerate(self.datas):
        ticker = data._name  # Access ticker name
        price = data.close[0]
        # Trade logic
```

### Getting Ticker Names

Each data feed has a `_name` attribute set by Cerebro:

```python
def __init__(self):
    for i, data in enumerate(self.datas):
        ticker = data._name if hasattr(data, '_name') else f"Asset_{i}"
        print(f"Initialized {ticker}")
```

### Accessing Historical Data

Use negative indexing to access historical bars:

```python
current_close = data.close[0]       # Current close
previous_close = data.close[-1]     # Previous bar's close
close_10_bars_ago = data.close[-10] # 10 bars ago

# Check if enough data available
if len(data) >= 20:
    # Safe to access data.close[-19]
```

### Checking Positions

Get current position for specific asset:

```python
position = self.getposition(data)
shares = position.size
entry_price = position.price

if position:  # True if position exists
    print(f"Holding {shares} shares at avg price {entry_price}")
```

---

## Position Sizing

### Strategy-Controlled Sizing

You have **full control** over position sizes. The system does **not** automatically enforce portfolio weights.

**Basic Examples:**

```python
# Fixed size
self.buy(data=data, size=100)  # Buy 100 shares

# Percentage of portfolio
portfolio_value = self.broker.getvalue()
target_value = portfolio_value * 0.3  # 30% allocation
price = data.close[0]
size = int(target_value / price)
self.buy(data=data, size=size)

# Dollar amount
dollars_to_invest = 10000
size = int(dollars_to_invest / price)
self.buy(data=data, size=size)
```

### Order Types

**Buy/Sell specific size:**

```python
self.buy(data=data, size=100)   # Buy 100 shares
self.sell(data=data, size=50)   # Sell 50 shares
```

**Close entire position:**

```python
self.close(data=data)  # Close all shares of this asset
```

**Target specific position size:**

```python
# Set position to exactly 200 shares (buys or sells as needed)
self.order_target_size(data=data, target=200)

# Set position to 0 (close position)
self.order_target_size(data=data, target=0)
```

### Cash Management

**Check available cash:**

```python
cash = self.broker.getcash()
portfolio_value = self.broker.getvalue()  # Cash + positions

if cash >= 10000:
    # Enough cash to buy
    self.buy(data=data, size=size)
```

**Prevent overdraft:**

Backtrader's broker enforces cash limits automatically. If you try to buy more than you can afford, the order will be rejected.

---

## Rebalancing

### How Rebalancing Works

When you enable rebalancing via API configuration:

1. **Your strategy signals** execute normally (buys/sells based on your logic)
2. **Rebalancing** runs on schedule (monthly, quarterly, etc.)
3. **Potential conflicts**: Rebalancing may adjust positions your strategy created

### Rebalancing Configuration (API)

```json
{
  "rebalance_config": {
    "frequency": "monthly",
    "min_trade_threshold": 0.01,
    "transaction_cost_pct": 0.001
  },
  "optimization_method": "equal_weight"
}
```

**Optimization methods:**

- `equal_weight`: 1/N allocation (simple)
- `risk_parity`: Equal risk contribution
- `min_variance`: Minimize portfolio volatility
- `markowitz`: Maximize Sharpe ratio

### Strategy + Rebalancing Coexistence

**Scenario 1: Strategy controls all trading (recommended)**

- Disable rebalancing (`rebalance_config: null`)
- Your strategy has full control
- No conflicts

**Scenario 2: Strategy + Rebalancing both active**

- Your strategy generates entry/exit signals
- Rebalancing adjusts allocation periodically
- Example: Strategy trades based on momentum, rebalancing maintains target weights

**Scenario 3: Manual rebalancing in strategy**

- Implement your own rebalancing logic in `next()`
- Disable API rebalancing
- Full control over when and how to rebalance

**Manual Rebalancing Example:**

```python
class EqualWeightRebalancing(bt.Strategy):
    params = (('rebalance_days', 30),)

    def __init__(self):
        self.days_since_rebalance = 0

    def next(self):
        self.days_since_rebalance += 1

        if self.days_since_rebalance >= self.p.rebalance_days:
            self.rebalance_to_equal_weights()
            self.days_since_rebalance = 0

    def rebalance_to_equal_weights(self):
        num_assets = len(self.datas)
        portfolio_value = self.broker.getvalue()
        target_value_per_asset = portfolio_value / num_assets

        for data in self.datas:
            current_value = self.getposition(data).size * data.close[0]
            value_diff = target_value_per_asset - current_value
            shares_diff = int(value_diff / data.close[0])

            if shares_diff > 0:
                self.buy(data=data, size=shares_diff)
            elif shares_diff < 0:
                self.sell(data=data, size=abs(shares_diff))
```

---

## Examples

### Example 1: Independent Per-Asset Trading

Trade each asset independently based on SMA crossover:

```python
class IndependentSMAStrategy(bt.Strategy):
    params = (
        ('period', 20),
        ('position_size', 100),
    )

    def __init__(self):
        self.smas = []
        self.signals = []

        for data in self.datas:
            sma = bt.indicators.SMA(data.close, period=self.p.period)
            self.smas.append(sma)

            cross = bt.indicators.CrossOver(data.close, sma)
            self.signals.append(cross)

    def next(self):
        for i, data in enumerate(self.datas):
            position = self.getposition(data)
            signal = self.signals[i]

            # Buy signal: price crosses above SMA
            if signal > 0 and not position:
                self.buy(data=data, size=self.p.position_size)

            # Sell signal: price crosses below SMA
            elif signal < 0 and position:
                self.close(data=data)
```

### Example 2: Pairs Trading

Trade based on relative strength between two assets:

```python
class PairsTradingStrategy(bt.Strategy):
    params = (
        ('ratio_threshold', 1.1),
        ('position_size', 100),
    )

    def next(self):
        if len(self.datas) < 2:
            return

        data0 = self.datas[0]  # First asset
        data1 = self.datas[1]  # Second asset

        pos0 = self.getposition(data0)
        pos1 = self.getposition(data1)

        # Calculate price ratio
        ratio = data0.close[0] / data1.close[0]

        # Asset 0 is relatively expensive → sell 0, buy 1
        if ratio > self.p.ratio_threshold:
            if pos0:
                self.close(data=data0)
            if not pos1:
                self.buy(data=data1, size=self.p.position_size)

        # Asset 1 is relatively expensive → sell 1, buy 0
        elif ratio < (1 / self.p.ratio_threshold):
            if pos1:
                self.close(data=data1)
            if not pos0:
                self.buy(data=data0, size=self.p.position_size)
```

### Example 3: Sector Rotation (Momentum)

Buy top performers, sell laggards:

```python
class SectorRotationStrategy(bt.Strategy):
    params = (
        ('lookback', 30),
        ('top_n', 2),
        ('position_size', 100),
    )

    def next(self):
        if len(self.datas[0]) < self.p.lookback:
            return  # Not enough data yet

        # Calculate momentum for each asset
        momentums = []
        for i, data in enumerate(self.datas):
            momentum = (data.close[0] - data.close[-self.p.lookback]) / data.close[-self.p.lookback]
            momentums.append((i, momentum))

        # Sort by momentum (descending)
        momentums.sort(key=lambda x: x[1], reverse=True)

        # Buy top N, close others
        for rank, (i, momentum) in enumerate(momentums):
            data = self.datas[i]
            pos = self.getposition(data)

            if rank < self.p.top_n:  # Top performers
                if not pos:
                    self.buy(data=data, size=self.p.position_size)
            else:  # Laggards
                if pos:
                    self.close(data=data)
```

### Example 4: Buy and Hold Portfolio

Simple buy-and-hold with equal allocation:

```python
class BuyAndHoldPortfolio(bt.Strategy):
    params = (('allocation_pct', 0.95),)

    def __init__(self):
        self.ordered = False

    def next(self):
        if not self.ordered:
            num_assets = len(self.datas)
            portfolio_value = self.broker.getvalue()
            per_asset_value = (portfolio_value * self.p.allocation_pct) / num_assets

            for data in self.datas:
                price = data.close[0]
                size = int(per_asset_value / price)
                if size > 0:
                    self.buy(data=data, size=size)

            self.ordered = True
```

---

## Common Pitfalls

### 1. ❌ Using `self.data` instead of `self.datas[i]`

**Wrong:**

```python
# This only accesses the FIRST asset
price = self.data.close[0]
self.buy()  # Only buys first asset
```

**Right:**

```python
# Access specific asset
for data in self.datas:
    price = data.close[0]
    self.buy(data=data)  # Specify which asset
```

### 2. ❌ Not specifying `data=` parameter in orders

**Wrong:**

```python
# Ambiguous - which asset?
self.buy(size=100)
```

**Right:**

```python
# Explicit asset reference
self.buy(data=self.datas[0], size=100)
```

### 3. ❌ Assuming automatic weight enforcement

Portfolio strategies do **NOT** automatically maintain target weights. You must implement this yourself.

**If you want weight-based sizing:**

```python
def calculate_target_size(self, data, target_weight):
    portfolio_value = self.broker.getvalue()
    target_value = portfolio_value * target_weight
    price = data.close[0]
    return int(target_value / price)

def next(self):
    target_weight = 0.33  # 33% allocation
    target_size = self.calculate_target_size(self.datas[0], target_weight)
    self.order_target_size(data=self.datas[0], target=target_size)
```

### 4. ❌ Not handling insufficient data

Indicators need warmup time. Check data length before accessing historical bars:

**Wrong:**

```python
def next(self):
    # Crashes if < 50 bars available
    old_price = self.datas[0].close[-50]
```

**Right:**

```python
def next(self):
    if len(self.datas[0]) < 51:
        return  # Wait for enough data

    old_price = self.datas[0].close[-50]
```

### 5. ❌ Forgetting order rejection handling

Orders can be rejected (insufficient cash, market closed, etc.):

```python
def notify_order(self, order):
    if order.status in [order.Completed]:
        # Order executed
        pass
    elif order.status in [order.Canceled, order.Margin, order.Rejected]:
        # Order failed
        ticker = order.data._name
        print(f"Order {order.Status[order.status]} for {ticker}")
```

### 6. ❌ Ignoring rebalancing conflicts

If both your strategy and auto-rebalancing are active:

- Your strategy's positions may be adjusted by rebalancing
- Consider: disable rebalancing if strategy fully controls portfolio
- Or: design strategy to work with periodic rebalancing

**Recommendation:**

```python
# Either:
# 1. Strategy controls all → disable rebalancing
# 2. Rebalancing only → use simple buy-and-hold strategy
# 3. Hybrid → strategy for entries/exits, rebalancing for weights
```

---

## Testing Your Strategy

### 1. Start with Template

Copy [multi_asset_template.py](../backend/resources/strategy/multi_asset_template.py) as your starting point.

### 2. Test with 2-3 Assets First

```json
{
  "tickers": ["AAPL", "GOOGL"],
  "weights": [0.5, 0.5],
  "strategy_name": "my_portfolio_strategy"
}
```

### 3. Check Logs

Enable logging in your strategy:

```python
def log(self, txt, dt=None):
    dt = dt or self.datas[0].datetime.date(0)
    print(f'{dt.isoformat()} {txt}')

def next(self):
    self.log(f'Portfolio value: ${self.broker.getvalue():.2f}')
```

### 4. Verify Trades

Use `notify_order()` and `notify_trade()` to track execution:

```python
def notify_trade(self, trade):
    if trade.isclosed:
        ticker = trade.data._name
        self.log(f'TRADE CLOSED: {ticker} | PnL: ${trade.pnlcomm:.2f}')
```

---

## Best Practices

1. **Start simple**: Test with buy-and-hold before adding complex logic
2. **Use ticker names**: Access `data._name` for readable logs
3. **Check data length**: Always verify enough bars available before accessing historical data
4. **Log everything**: Use `notify_order()`, `notify_trade()`, and custom `log()` method
5. **Test incrementally**: Add one feature at a time (indicators → signals → sizing → rebalancing)
6. **Handle edge cases**: Insufficient cash, insufficient data, market gaps
7. **Document parameters**: Use descriptive param names and docstrings

---

## Getting Help

- **Template**: See [multi_asset_template.py](../backend/resources/strategy/multi_asset_template.py)
- **Examples**: Check `backend/resources/strategy/` for more examples
- **Backtrader Docs**: https://www.backtrader.com/docu/
- **API Reference**: See `CLAUDE.md` for API endpoint documentation

---

## Summary

| Concept | Key Points |
|---------|-----------|
| **Multi-data access** | Use `self.datas[i]` to access each asset |
| **Ticker mapping** | Asset order matches API `tickers` array |
| **Position sizing** | Strategy-controlled via `size` parameter |
| **Rebalancing** | Optional - runs alongside strategy if enabled |
| **Order syntax** | Always specify `data=data` parameter |
| **Common pattern** | `for i, data in enumerate(self.datas):` |

Happy trading! 🚀
