"""
ATR Trailing Stop Strategy - Trend Following with Dynamic Exit

This strategy uses Average True Range (ATR) to set dynamic trailing stops.
Entry is based on simple trend filter, and exit adapts to market volatility.
Wider stops in volatile markets, tighter in calm markets.

Suitable for: Trending markets, stocks, futures, crypto
Difficulty: Intermediate
"""
import backtrader as bt


class UserStrategy(bt.Strategy):
    """
    ATR Trailing Stop Strategy
    
    Parameters:
        atr_period: ATR calculation period (default: 14)
        atr_multiplier: Stop distance in ATR units (default: 2.0)
        ma_period: Trend filter period (default: 50)
    """
    params = (
        ("atr_period", 14),
        ("atr_multiplier", 2.0),
        ("ma_period", 50),
    )

    def __init__(self):
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        self.ma = bt.indicators.SMA(self.data.close, period=self.p.ma_period)
        self.trailing_stop = None

    def next(self):
        if not self.position:
            # Enter long when price above MA (uptrend)
            if self.data.close[0] > self.ma[0]:
                self.buy()
                # Set initial trailing stop
                self.trailing_stop = self.data.close[0] - self.atr[0] * self.p.atr_multiplier
        else:
            # Update trailing stop (only move up, never down)
            new_stop = self.data.close[0] - self.atr[0] * self.p.atr_multiplier
            if new_stop > self.trailing_stop:
                self.trailing_stop = new_stop
            
            # Exit if price falls below trailing stop
            if self.data.close[0] < self.trailing_stop:
                self.close()
                self.trailing_stop = None
