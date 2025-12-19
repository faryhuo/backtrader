"""
Turtle Trading Strategy - Trend Following

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
        # Donchian Channel for entry (N-day high/low)
        self.entry_high = bt.indicators.Highest(self.data.high, period=self.p.entry_period)
        self.entry_low = bt.indicators.Lowest(self.data.low, period=self.p.entry_period)
        
        # Donchian Channel for exit (shorter period)
        self.exit_high = bt.indicators.Highest(self.data.high, period=self.p.exit_period)
        self.exit_low = bt.indicators.Lowest(self.data.low, period=self.p.exit_period)
        
        # ATR for position sizing and stops
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        
        self.entry_price = None
        self.stop_price = None

    def next(self):
        if not self.position:
            # Entry: price breaks above N-day high
            if self.data.close[0] > self.entry_high[-1]:
                # Calculate position size based on ATR and risk
                atr_value = self.atr[0]
                if atr_value > 0:
                    risk_amount = self.broker.getvalue() * self.p.risk_factor
                    stop_distance = 2 * atr_value  # 2 ATR stop
                    size = int(risk_amount / stop_distance)
                    
                    if size > 0:
                        self.buy(size=size)
                        self.entry_price = self.data.close[0]
                        self.stop_price = self.entry_price - stop_distance
        else:
            # Exit conditions
            # 1. Stop loss: price falls below entry - 2*ATR
            if self.stop_price and self.data.close[0] < self.stop_price:
                self.close()
                self.entry_price = None
                self.stop_price = None
            # 2. Exit signal: price breaks below exit_period low
            elif self.data.close[0] < self.exit_low[-1]:
                self.close()
                self.entry_price = None
                self.stop_price = None
            # 3. Trail stop using ATR (optional enhancement)
            elif self.entry_price:
                new_stop = self.data.close[0] - 2 * self.atr[0]
                if new_stop > self.stop_price:
                    self.stop_price = new_stop
