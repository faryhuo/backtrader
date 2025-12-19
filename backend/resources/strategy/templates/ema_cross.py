"""
EMA Crossover Strategy - Trend Following

This strategy uses Exponential Moving Average (EMA) crossovers to identify
trend changes. EMA gives more weight to recent prices, making it more
responsive to new information compared to Simple Moving Average (SMA).

Suitable for: Trending markets, indices, large-cap stocks
Difficulty: Beginner
"""
import backtrader as bt


class UserStrategy(bt.Strategy):
    """
    EMA Crossover Strategy
    
    Parameters:
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
    """
    params = (
        ("fast_period", 12),
        ("slow_period", 26),
    )

    def __init__(self):
        self.fast_ema = bt.indicators.EMA(self.data.close, period=self.p.fast_period)
        self.slow_ema = bt.indicators.EMA(self.data.close, period=self.p.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ema, self.slow_ema)

    def next(self):
        if not self.position:
            # Fast EMA crosses above slow EMA - bullish signal
            if self.crossover > 0:
                self.buy()
        else:
            # Fast EMA crosses below slow EMA - bearish signal
            if self.crossover < 0:
                self.close()
