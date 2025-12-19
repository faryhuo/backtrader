"""
Triple Moving Average Strategy - Trend Following

Uses three moving averages (fast, medium, slow) to identify trend strength
and direction. Enters when all three align (fast > medium > slow for uptrend).
More robust than dual MA crossover with fewer false signals.

Suitable for: Trending markets, stocks, ETFs, indices
Difficulty: Beginner
"""
import backtrader as bt


class UserStrategy(bt.Strategy):
    """
    Triple Moving Average Strategy
    
    Parameters:
        fast_period: Fast MA period (default: 10)
        medium_period: Medium MA period (default: 20)
        slow_period: Slow MA period (default: 50)
    """
    params = (
        ("fast_period", 10),
        ("medium_period", 20),
        ("slow_period", 50),
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(self.data.close, period=self.p.fast_period)
        self.medium_ma = bt.indicators.SMA(self.data.close, period=self.p.medium_period)
        self.slow_ma = bt.indicators.SMA(self.data.close, period=self.p.slow_period)

    def next(self):
        if not self.position:
            # All MAs aligned bullish: fast > medium > slow
            if self.fast_ma[0] > self.medium_ma[0] > self.slow_ma[0]:
                self.buy()
        else:
            # Exit when fast crosses below medium
            if self.fast_ma[0] < self.medium_ma[0]:
                self.close()
