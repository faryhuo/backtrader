"""
Mean Reversion with Z-Score Strategy - Statistical Arbitrage (Multi-Data Support)

Uses Z-Score to measure how far price deviates from its mean in standard
deviation units. Enters when price is extremely oversold (low Z-Score) and
exits when it returns to mean. Pure statistical mean reversion approach.

Suitable for: Range-bound markets, pairs trading, ETFs
Difficulty: Intermediate
"""
import backtrader as bt


class UserStrategy(bt.Strategy):
    """
    Z-Score Mean Reversion Strategy
    
    Parameters:
        lookback: Period for mean and std calculation (default: 20)
        entry_zscore: Z-Score threshold for entry (default: -2.0)
        exit_zscore: Z-Score threshold for exit (default: 0.0)
    """
    params = (
        ("lookback", 20),
        ("entry_zscore", -2.0),
        ("exit_zscore", 0.0),
    )

    def __init__(self):
        self.indicators = {}
        
        # Create indicators for EACH data feed
        for d in self.datas:
            self.indicators[d] = {
                'mean': bt.indicators.SMA(d.close, period=self.p.lookback),
                'std': bt.indicators.StdDev(d.close, period=self.p.lookback),
            }
        
    def get_zscore(self, d):
        """Calculate current Z-Score for a specific data feed."""
        ind = self.indicators[d]
        if ind['std'][0] == 0:
            return 0
        return (d.close[0] - ind['mean'][0]) / ind['std'][0]

    def next(self):
        # Apply trading logic to each data feed
        for d in self.datas:
            pos = self.getposition(d)
            zscore = self.get_zscore(d)
            
            if not pos.size:
                # Enter when extremely oversold
                if zscore < self.p.entry_zscore:
                    self.buy(data=d)
            else:
                # Exit when price returns to mean
                if zscore > self.p.exit_zscore:
                    self.close(data=d)
