"""
Donchian Channel Breakout Strategy - Trend Following (Multi-Data Support)

The Donchian Channel uses the highest high and lowest low over N periods.
This strategy enters on breakouts above the upper channel (bullish) and
exits on breakdowns below the lower channel. Classic trend-following approach.

Suitable for: Trending markets, futures, forex, commodities
Difficulty: Beginner
"""
import backtrader as bt


class UserStrategy(bt.Strategy):
    """
    Donchian Channel Breakout Strategy
    
    Parameters:
        entry_period: Period for entry channel (default: 20)
        exit_period: Period for exit channel (default: 10)
    """
    params = (
        ("entry_period", 20),
        ("exit_period", 10),
    )

    def __init__(self):
        self.indicators = {}
        
        # Create indicators for EACH data feed
        for d in self.datas:
            self.indicators[d] = {
                # Entry channel (longer period)
                'upper_entry': bt.indicators.Highest(d.high, period=self.p.entry_period),
                'lower_entry': bt.indicators.Lowest(d.low, period=self.p.entry_period),
                # Exit channel (shorter period)
                'upper_exit': bt.indicators.Highest(d.high, period=self.p.exit_period),
                'lower_exit': bt.indicators.Lowest(d.low, period=self.p.exit_period),
            }

    def next(self):
        # Apply trading logic to each data feed
        for d in self.datas:
            ind = self.indicators[d]
            pos = self.getposition(d)
            
            if not pos.size:
                # Breakout above entry channel - buy
                if d.close[0] > ind['upper_entry'][-1]:
                    self.buy(data=d)
            else:
                # Break below exit channel - close position
                if d.close[0] < ind['lower_exit'][-1]:
                    self.close(data=d)
