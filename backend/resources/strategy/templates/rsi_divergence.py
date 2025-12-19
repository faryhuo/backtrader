"""
RSI Divergence Strategy - Mean Reversion + Momentum

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
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)
        
    def find_bullish_divergence(self):
        """Check for bullish divergence: price lower low, RSI higher low."""
        if len(self.data) < self.p.lookback + 1:
            return False
        
        # Current price is lower than lookback bars ago
        price_lower = self.data.low[0] < min([self.data.low[-i] for i in range(1, self.p.lookback + 1)])
        # Current RSI is higher than lookback bars ago (when price was at local low)
        rsi_higher = self.rsi[0] > min([self.rsi[-i] for i in range(1, self.p.lookback + 1)])
        
        return price_lower and rsi_higher and self.rsi[0] < self.p.rsi_oversold

    def find_bearish_divergence(self):
        """Check for bearish divergence: price higher high, RSI lower high."""
        if len(self.data) < self.p.lookback + 1:
            return False
        
        # Current price is higher than lookback bars ago
        price_higher = self.data.high[0] > max([self.data.high[-i] for i in range(1, self.p.lookback + 1)])
        # Current RSI is lower than lookback bars ago
        rsi_lower = self.rsi[0] < max([self.rsi[-i] for i in range(1, self.p.lookback + 1)])
        
        return price_higher and rsi_lower and self.rsi[0] > self.p.rsi_overbought

    def next(self):
        if not self.position:
            if self.find_bullish_divergence():
                self.buy()
        else:
            if self.find_bearish_divergence() or self.rsi[0] > self.p.rsi_overbought:
                self.close()
