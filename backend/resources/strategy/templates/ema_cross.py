"""
EMA Crossover Strategy - Trend Following (Multi-Data Support)

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
        self.indicators = {}
        
        # Create indicators for EACH data feed
        for d in self.datas:
            self.indicators[d] = {
                'fast_ema': bt.indicators.EMA(d.close, period=self.p.fast_period),
                'slow_ema': bt.indicators.EMA(d.close, period=self.p.slow_period),
            }
            self.indicators[d]['crossover'] = bt.indicators.CrossOver(
                self.indicators[d]['fast_ema'],
                self.indicators[d]['slow_ema']
            )

    def next(self):
        # Apply trading logic to each data feed
        for d in self.datas:
            ind = self.indicators[d]
            pos = self.getposition(d)
            
            if not pos.size:
                # Fast EMA crosses above slow EMA - bullish signal
                if ind['crossover'] > 0:
                    self.buy(data=d)
            else:
                # Fast EMA crosses below slow EMA - bearish signal
                if ind['crossover'] < 0:
                    self.close(data=d)
