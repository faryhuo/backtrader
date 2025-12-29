"""
Keltner Channel Strategy - Mean Reversion (Multi-Data Support)

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
        self.indicators = {}
        
        # Create indicators for EACH data feed
        for d in self.datas:
            ema = bt.indicators.EMA(d.close, period=self.p.ema_period)
            atr = bt.indicators.ATR(d, period=self.p.atr_period)
            
            self.indicators[d] = {
                'ema': ema,
                'atr': atr,
                # Calculate Keltner Channel bands
                'upper': ema + atr * self.p.atr_multiplier,
                'lower': ema - atr * self.p.atr_multiplier,
            }

    def next(self):
        # Apply trading logic to each data feed
        for d in self.datas:
            ind = self.indicators[d]
            pos = self.getposition(d)
            
            if not pos.size:
                # Price crosses below lower band - oversold, buy
                if d.close[0] <= ind['lower'][0]:
                    self.buy(data=d)
            else:
                # Price crosses above upper band - overbought, sell
                if d.close[0] >= ind['upper'][0]:
                    self.close(data=d)
                # Exit at middle band
                elif d.close[0] >= ind['ema'][0]:
                    self.close(data=d)
