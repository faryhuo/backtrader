"""
Dual Thrust Strategy - Range Breakout (Multi-Data Support)

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
        self.entry_prices = {}
        
        # Initialize tracking for each data feed
        for d in self.datas:
            ticker = d._name
            self.entry_prices[ticker] = None
        
    def next(self):
        # Apply trading logic to each data feed
        for d in self.datas:
            ticker = d._name
            pos = self.getposition(d)
            
            if len(d) < self.p.lookback + 1:
                continue
                
            # Calculate range using lookback period
            hh = max([d.high[-i] for i in range(1, self.p.lookback + 1)])
            lc = min([d.close[-i] for i in range(1, self.p.lookback + 1)])
            hc = max([d.close[-i] for i in range(1, self.p.lookback + 1)])
            ll = min([d.low[-i] for i in range(1, self.p.lookback + 1)])
            
            range_val = max(hh - lc, hc - ll)
            
            # Today's open (approximated by previous close in daily data)
            open_price = d.open[0]
            
            upper_trigger = open_price + self.p.k1 * range_val
            lower_trigger = open_price - self.p.k2 * range_val
            
            if not pos.size:
                if d.close[0] > upper_trigger:
                    self.buy(data=d)
                    self.entry_prices[ticker] = d.close[0]
            else:
                # Exit on opposite signal or end of day (simplified)
                if d.close[0] < lower_trigger:
                    self.close(data=d)
                    self.entry_prices[ticker] = None
