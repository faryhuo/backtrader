"""
Bollinger Bands Strategy - Mean Reversion (Multi-Data Support)

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
        self.indicators = {}
        
        # Create indicators for EACH data feed
        for d in self.datas:
            self.indicators[d] = {
                'boll': bt.indicators.BollingerBands(
                    d.close,
                    period=self.p.period,
                    devfactor=self.p.devfactor
                )
            }

    def next(self):
        # Apply trading logic to each data feed
        for d in self.datas:
            ind = self.indicators[d]
            pos = self.getposition(d)
            boll = ind['boll']
            
            if not pos.size:
                # Price touches or crosses below lower band - oversold, buy
                if d.close[0] <= boll.lines.bot[0]:
                    self.buy(data=d)
            else:
                # Price touches or crosses above upper band - overbought, sell
                if d.close[0] >= boll.lines.top[0]:
                    self.close(data=d)
