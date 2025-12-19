"""
Stochastic Oscillator Strategy - Momentum

This strategy uses the Stochastic Oscillator to identify overbought and oversold
conditions. The oscillator compares closing price to the high-low range over a
period. It's effective for range-bound markets and timing entries.

Suitable for: Range-bound markets, forex, stocks
Difficulty: Beginner
"""
import backtrader as bt


class UserStrategy(bt.Strategy):
    """
    Stochastic Oscillator Strategy
    
    Parameters:
        period_k: %K period (default: 14)
        period_d: %D smoothing period (default: 3)
        oversold: Oversold level (default: 20)
        overbought: Overbought level (default: 80)
    """
    params = (
        ("period_k", 14),
        ("period_d", 3),
        ("oversold", 20),
        ("overbought", 80),
    )

    def __init__(self):
        self.stoch = bt.indicators.Stochastic(
            self.data,
            period=self.p.period_k,
            period_dfast=self.p.period_d
        )
        
    def next(self):
        if not self.position:
            # Buy when %K crosses above %D in oversold zone
            if (self.stoch.percK[-1] < self.stoch.percD[-1] and 
                self.stoch.percK[0] > self.stoch.percD[0] and
                self.stoch.percK[0] < self.p.oversold + 10):
                self.buy()
        else:
            # Sell when %K crosses below %D in overbought zone
            if (self.stoch.percK[-1] > self.stoch.percD[-1] and 
                self.stoch.percK[0] < self.stoch.percD[0] and
                self.stoch.percK[0] > self.p.overbought - 10):
                self.close()
