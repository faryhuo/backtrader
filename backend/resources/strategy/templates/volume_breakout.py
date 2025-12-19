"""
Volume Breakout Strategy - Volume + Price Action

This strategy combines price breakout with volume confirmation. A breakout
is only valid when accompanied by above-average volume, filtering out
false breakouts with low conviction.

Suitable for: Stocks, ETFs, trending markets
Difficulty: Intermediate
"""
import backtrader as bt


class UserStrategy(bt.Strategy):
    """
    Volume Breakout Strategy
    
    Parameters:
        price_period: Price channel period (default: 20)
        volume_period: Volume average period (default: 20)
        volume_multiplier: Required volume vs average (default: 1.5)
    """
    params = (
        ("price_period", 20),
        ("volume_period", 20),
        ("volume_multiplier", 1.5),
    )

    def __init__(self):
        self.highest = bt.indicators.Highest(self.data.high, period=self.p.price_period)
        self.lowest = bt.indicators.Lowest(self.data.low, period=self.p.price_period)
        self.volume_avg = bt.indicators.SMA(self.data.volume, period=self.p.volume_period)

    def next(self):
        if not self.position:
            # Breakout with volume confirmation
            is_high_volume = self.data.volume[0] > self.volume_avg[0] * self.p.volume_multiplier
            
            if self.data.close[0] > self.highest[-1] and is_high_volume:
                self.buy()
        else:
            # Exit on breakdown below channel
            if self.data.close[0] < self.lowest[-1]:
                self.close()
