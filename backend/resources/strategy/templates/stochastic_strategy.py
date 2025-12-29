"""
Stochastic Oscillator Strategy - Momentum (Multi-Data Support)

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
        self.indicators = {}
        
        # Create indicators for EACH data feed
        for d in self.datas:
            self.indicators[d] = {
                'stoch': bt.indicators.Stochastic(
                    d,
                    period=self.p.period_k,
                    period_dfast=self.p.period_d
                )
            }
        
    def next(self):
        # Apply trading logic to each data feed
        for d in self.datas:
            ind = self.indicators[d]
            pos = self.getposition(d)
            stoch = ind['stoch']
            
            if not pos.size:
                # Buy when %K crosses above %D in oversold zone
                if (stoch.percK[-1] < stoch.percD[-1] and 
                    stoch.percK[0] > stoch.percD[0] and
                    stoch.percK[0] < self.p.oversold + 10):
                    self.buy(data=d)
            else:
                # Sell when %K crosses below %D in overbought zone
                if (stoch.percK[-1] > stoch.percD[-1] and 
                    stoch.percK[0] < stoch.percD[0] and
                    stoch.percK[0] > self.p.overbought - 10):
                    self.close(data=d)
