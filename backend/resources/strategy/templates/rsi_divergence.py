"""
RSI Divergence Strategy - Mean Reversion + Momentum (Multi-Data Support)

This strategy combines RSI with price action to identify bullish and bearish
divergences. A bullish divergence occurs when price makes a lower low but RSI
makes a higher low, signaling potential reversal. Vice versa for bearish divergence.

Suitable for: Swing trading, stocks, forex, crypto
Difficulty: Intermediate
"""
import backtrader as bt


class UserStrategy(bt.Strategy):
    """
    RSI Divergence Strategy
    
    Parameters:
        rsi_period: RSI calculation period (default: 14)
        rsi_oversold: Oversold threshold (default: 30)
        rsi_overbought: Overbought threshold (default: 70)
        lookback: Bars to look back for divergence (default: 5)
    """
    params = (
        ("rsi_period", 14),
        ("rsi_oversold", 30),
        ("rsi_overbought", 70),
        ("lookback", 5),
    )

    def __init__(self):
        self.indicators = {}
        
        # Create indicators for EACH data feed
        for d in self.datas:
            self.indicators[d] = {
                'rsi': bt.indicators.RSI(d.close, period=self.p.rsi_period)
            }
        
    def find_bullish_divergence(self, d, rsi):
        """Check for bullish divergence: price lower low, RSI higher low."""
        if len(d) < self.p.lookback + 1:
            return False
        
        # Current price is lower than lookback bars ago
        price_lower = d.low[0] < min([d.low[-i] for i in range(1, self.p.lookback + 1)])
        # Current RSI is higher than lookback bars ago (when price was at local low)
        rsi_higher = rsi[0] > min([rsi[-i] for i in range(1, self.p.lookback + 1)])
        
        return price_lower and rsi_higher and rsi[0] < self.p.rsi_oversold

    def find_bearish_divergence(self, d, rsi):
        """Check for bearish divergence: price higher high, RSI lower high."""
        if len(d) < self.p.lookback + 1:
            return False
        
        # Current price is higher than lookback bars ago
        price_higher = d.high[0] > max([d.high[-i] for i in range(1, self.p.lookback + 1)])
        # Current RSI is lower than lookback bars ago
        rsi_lower = rsi[0] < max([rsi[-i] for i in range(1, self.p.lookback + 1)])
        
        return price_higher and rsi_lower and rsi[0] > self.p.rsi_overbought

    def next(self):
        # Apply trading logic to each data feed
        for d in self.datas:
            ind = self.indicators[d]
            pos = self.getposition(d)
            rsi = ind['rsi']
            
            if not pos.size:
                if self.find_bullish_divergence(d, rsi):
                    self.buy(data=d)
            else:
                if self.find_bearish_divergence(d, rsi) or rsi[0] > self.p.rsi_overbought:
                    self.close(data=d)
