"""
Keltner Channel Strategy - Mean Reversion

Keltner Channel uses EMA as the middle band and ATR for volatility measurement.
It's smoother and more stable than Bollinger Bands. This strategy trades
mean reversion by buying at the lower band and selling at the upper band.

Suitable for: Markets with changing volatility, stocks, futures
Difficulty: Intermediate
"""
import backtrader as bt


class UserStrategy(bt.Strategy):
    """
    Keltner Channel Mean Reversion Strategy
    
    Parameters:
        ema_period: EMA period for middle band (default: 20)
        atr_period: ATR period for volatility (default: 10)
        atr_multiplier: ATR multiplier for bands (default: 2.0)
    """
    params = (
        ("ema_period", 20),
        ("atr_period", 10),
        ("atr_multiplier", 2.0),
    )

    def __init__(self):
        self.ema = bt.indicators.EMA(self.data.close, period=self.p.ema_period)
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        
        # Calculate Keltner Channel bands
        self.upper = self.ema + self.atr * self.p.atr_multiplier
        self.lower = self.ema - self.atr * self.p.atr_multiplier

    def next(self):
        if not self.position:
            # Price crosses below lower band - oversold, buy
            if self.data.close[0] <= self.lower[0]:
                self.buy()
        else:
            # Price crosses above upper band - overbought, sell
            if self.data.close[0] >= self.upper[0]:
                self.close()
            # Exit at middle band
            elif self.data.close[0] >= self.ema[0]:
                self.close()
