"""
Dual Thrust Strategy - Range Breakout

Dual Thrust is a famous intraday breakout strategy. It calculates a range
based on previous day's high, low, close, and open, then sets upper and lower
trigger lines. Breaking above upper triggers buy, breaking below triggers sell.

Suitable for: Intraday trading, futures, commodities, forex
Difficulty: Intermediate
"""
import backtrader as bt


class UserStrategy(bt.Strategy):
    """
    Dual Thrust Range Breakout Strategy
    
    Parameters:
        lookback: Bars to calculate range (default: 4)
        k1: Upper trigger multiplier (default: 0.5)
        k2: Lower trigger multiplier (default: 0.5)
    """
    params = (
        ("lookback", 4),
        ("k1", 0.5),
        ("k2", 0.5),
    )

    def __init__(self):
        self.entry_price = None
        
    def next(self):
        if len(self.data) < self.p.lookback + 1:
            return
            
        # Calculate range using lookback period
        hh = max([self.data.high[-i] for i in range(1, self.p.lookback + 1)])
        lc = min([self.data.close[-i] for i in range(1, self.p.lookback + 1)])
        hc = max([self.data.close[-i] for i in range(1, self.p.lookback + 1)])
        ll = min([self.data.low[-i] for i in range(1, self.p.lookback + 1)])
        
        range_val = max(hh - lc, hc - ll)
        
        # Today's open (approximated by previous close in daily data)
        open_price = self.data.open[0]
        
        upper_trigger = open_price + self.p.k1 * range_val
        lower_trigger = open_price - self.p.k2 * range_val
        
        if not self.position:
            if self.data.close[0] > upper_trigger:
                self.buy()
                self.entry_price = self.data.close[0]
        else:
            # Exit on opposite signal or end of day (simplified)
            if self.data.close[0] < lower_trigger:
                self.close()
                self.entry_price = None
