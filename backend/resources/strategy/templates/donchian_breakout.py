"""
Donchian Channel Breakout Strategy - Trend Following

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
        # Entry channel (longer period)
        self.upper_entry = bt.indicators.Highest(self.data.high, period=self.p.entry_period)
        self.lower_entry = bt.indicators.Lowest(self.data.low, period=self.p.entry_period)
        
        # Exit channel (shorter period)
        self.upper_exit = bt.indicators.Highest(self.data.high, period=self.p.exit_period)
        self.lower_exit = bt.indicators.Lowest(self.data.low, period=self.p.exit_period)

    def next(self):
        if not self.position:
            # Breakout above entry channel - buy
            if self.data.close[0] > self.upper_entry[-1]:
                self.buy()
        else:
            # Break below exit channel - close position
            if self.data.close[0] < self.lower_exit[-1]:
                self.close()
