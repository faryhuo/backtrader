"""
Volume Breakout Strategy - Volume + Price Action (Multi-Data Support)

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
        self.indicators = {}
        
        # Create indicators for EACH data feed
        for d in self.datas:
            self.indicators[d] = {
                'highest': bt.indicators.Highest(d.high, period=self.p.price_period),
                'lowest': bt.indicators.Lowest(d.low, period=self.p.price_period),
                'volume_avg': bt.indicators.SMA(d.volume, period=self.p.volume_period),
            }

    def next(self):
        # Apply trading logic to each data feed
        for d in self.datas:
            ind = self.indicators[d]
            pos = self.getposition(d)
            
            if not pos.size:
                # Breakout with volume confirmation
                is_high_volume = d.volume[0] > ind['volume_avg'][0] * self.p.volume_multiplier
                
                if d.close[0] > ind['highest'][-1] and is_high_volume:
                    self.buy(data=d)
            else:
                # Exit on breakdown below channel
                if d.close[0] < ind['lowest'][-1]:
                    self.close(data=d)
