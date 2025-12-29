"""
Turtle Trading Strategy - Trend Following (Multi-Data Support)

The famous Turtle Trading system created by Richard Dennis and William Eckhardt.
Uses Donchian Channel breakouts for entry, with ATR-based position sizing and
stop-loss management. This is a complete trading system with entry, exit, and
risk management rules.

Suitable for: Futures, forex, commodities, trending markets
Difficulty: Intermediate
"""
import backtrader as bt


class UserStrategy(bt.Strategy):
    """
    Turtle Trading Strategy
    
    Parameters:
        entry_period: Entry breakout period - buy on N-day high (default: 20)
        exit_period: Exit breakout period - sell on N-day low (default: 10)
        atr_period: ATR period for volatility and position sizing (default: 20)
        risk_factor: Risk per trade as fraction of portfolio (default: 0.02)
    """
    params = (
        ("entry_period", 20),
        ("exit_period", 10),
        ("atr_period", 20),
        ("risk_factor", 0.02),
    )

    def __init__(self):
        self.indicators = {}
        self.entry_prices = {}
        self.stop_prices = {}
        
        # Create indicators for EACH data feed
        for d in self.datas:
            ticker = d._name
            self.indicators[d] = {
                # Donchian Channel for entry (N-day high/low)
                'entry_high': bt.indicators.Highest(d.high, period=self.p.entry_period),
                'entry_low': bt.indicators.Lowest(d.low, period=self.p.entry_period),
                # Donchian Channel for exit (shorter period)
                'exit_high': bt.indicators.Highest(d.high, period=self.p.exit_period),
                'exit_low': bt.indicators.Lowest(d.low, period=self.p.exit_period),
                # ATR for position sizing and stops
                'atr': bt.indicators.ATR(d, period=self.p.atr_period),
            }
            self.entry_prices[ticker] = None
            self.stop_prices[ticker] = None

    def next(self):
        # Apply trading logic to each data feed
        for d in self.datas:
            ticker = d._name
            ind = self.indicators[d]
            pos = self.getposition(d)
            entry_price = self.entry_prices.get(ticker)
            stop_price = self.stop_prices.get(ticker)
            
            if not pos.size:
                # Entry: price breaks above N-day high
                if d.close[0] > ind['entry_high'][-1]:
                    # Calculate position size based on ATR and risk
                    atr_value = ind['atr'][0]
                    if atr_value > 0:
                        risk_amount = self.broker.getvalue() * self.p.risk_factor
                        stop_distance = 2 * atr_value  # 2 ATR stop
                        size = int(risk_amount / stop_distance)
                        
                        if size > 0:
                            self.buy(data=d, size=size)
                            self.entry_prices[ticker] = d.close[0]
                            self.stop_prices[ticker] = d.close[0] - stop_distance
            else:
                # Exit conditions
                # 1. Stop loss: price falls below entry - 2*ATR
                if stop_price and d.close[0] < stop_price:
                    self.close(data=d)
                    self.entry_prices[ticker] = None
                    self.stop_prices[ticker] = None
                # 2. Exit signal: price breaks below exit_period low
                elif d.close[0] < ind['exit_low'][-1]:
                    self.close(data=d)
                    self.entry_prices[ticker] = None
                    self.stop_prices[ticker] = None
                # 3. Trail stop using ATR (optional enhancement)
                elif entry_price:
                    new_stop = d.close[0] - 2 * ind['atr'][0]
                    if stop_price is None or new_stop > stop_price:
                        self.stop_prices[ticker] = new_stop
