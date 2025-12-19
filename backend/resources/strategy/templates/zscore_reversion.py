"""
Mean Reversion with Z-Score Strategy - Statistical Arbitrage

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
        self.mean = bt.indicators.SMA(self.data.close, period=self.p.lookback)
        self.std = bt.indicators.StdDev(self.data.close, period=self.p.lookback)
        
    def get_zscore(self):
        """Calculate current Z-Score."""
        if self.std[0] == 0:
            return 0
        return (self.data.close[0] - self.mean[0]) / self.std[0]

    def next(self):
        zscore = self.get_zscore()
        
        if not self.position:
            # Enter when extremely oversold
            if zscore < self.p.entry_zscore:
                self.buy()
        else:
            # Exit when price returns to mean
            if zscore > self.p.exit_zscore:
                self.close()
