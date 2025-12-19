"""
Bollinger Bands Strategy - Mean Reversion

This strategy uses Bollinger Bands to identify overbought and oversold conditions.
The bands consist of a middle band (SMA) with upper and lower bands at N standard
deviations. Buy when price touches lower band, sell when it touches upper band.

Suitable for: Range-bound markets, stable volatility assets
Difficulty: Beginner
"""
import backtrader as bt


class UserStrategy(bt.Strategy):
    """
    Bollinger Bands Mean Reversion Strategy
    
    Parameters:
        period: Bollinger Bands period (default: 20)
        devfactor: Standard deviation multiplier (default: 2.0)
    """
    params = (
        ("period", 20),
        ("devfactor", 2.0),
    )

    def __init__(self):
        self.boll = bt.indicators.BollingerBands(
            self.data.close,
            period=self.p.period,
            devfactor=self.p.devfactor
        )

    def next(self):
        if not self.position:
            # Price touches or crosses below lower band - oversold, buy
            if self.data.close[0] <= self.boll.lines.bot[0]:
                self.buy()
        else:
            # Price touches or crosses above upper band - overbought, sell
            if self.data.close[0] >= self.boll.lines.top[0]:
                self.close()
            # Optional: exit at middle band for faster mean reversion
            # elif self.data.close[0] >= self.boll.lines.mid[0]:
            #     self.close()
