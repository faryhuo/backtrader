"""
MACD Crossover Strategy - Trend Following

This strategy uses the Moving Average Convergence Divergence (MACD) indicator
to identify trend direction and momentum. It generates buy signals on golden cross
(MACD line crosses above signal line) and sell signals on death cross.

Suitable for: Trending markets, stocks, ETFs, futures, crypto
Difficulty: Beginner
"""
import backtrader as bt


class UserStrategy(bt.Strategy):
    """
    MACD Crossover Strategy
    
    Parameters:
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal line period (default: 9)
    """
    params = (
        ("fast_period", 12),
        ("slow_period", 26),
        ("signal_period", 9),
    )

    def __init__(self):
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.p.fast_period,
            period_me2=self.p.slow_period,
            period_signal=self.p.signal_period
        )
        self.crossover = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)

    def next(self):
        if not self.position:
            # Golden cross: MACD line crosses above signal line
            if self.crossover > 0:
                self.buy()
        else:
            # Death cross: MACD line crosses below signal line
            if self.crossover < 0:
                self.close()
