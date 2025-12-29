"""
Triple Moving Average Strategy - Trend Following (Multi-Data Support)

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
        self.indicators = {}
        
        # Create indicators for EACH data feed
        for d in self.datas:
            self.indicators[d] = {
                'fast_ma': bt.indicators.SMA(d.close, period=self.p.fast_period),
                'medium_ma': bt.indicators.SMA(d.close, period=self.p.medium_period),
                'slow_ma': bt.indicators.SMA(d.close, period=self.p.slow_period),
            }

    def next(self):
        # Apply trading logic to each data feed
        for d in self.datas:
            ind = self.indicators[d]
            pos = self.getposition(d)
            
            if not pos.size:
                # All MAs aligned bullish: fast > medium > slow
                if ind['fast_ma'][0] > ind['medium_ma'][0] > ind['slow_ma'][0]:
                    self.buy(data=d)
            else:
                # Exit when fast crosses below medium
                if ind['fast_ma'][0] < ind['medium_ma'][0]:
                    self.close(data=d)
