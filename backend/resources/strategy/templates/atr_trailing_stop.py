"""
ATR Trailing Stop Strategy - Trend Following with Dynamic Exit (Multi-Data Support)

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
        self.indicators = {}
        self.trailing_stops = {}
        
        # Create indicators for EACH data feed
        for d in self.datas:
            ticker = d._name
            self.indicators[d] = {
                'atr': bt.indicators.ATR(d, period=self.p.atr_period),
                'ma': bt.indicators.SMA(d.close, period=self.p.ma_period),
            }
            self.trailing_stops[ticker] = None

    def next(self):
        # Apply trading logic to each data feed
        for d in self.datas:
            ticker = d._name
            ind = self.indicators[d]
            pos = self.getposition(d)
            trailing_stop = self.trailing_stops.get(ticker)
            
            if not pos.size:
                # Enter long when price above MA (uptrend)
                if d.close[0] > ind['ma'][0]:
                    self.buy(data=d)
                    # Set initial trailing stop
                    self.trailing_stops[ticker] = d.close[0] - ind['atr'][0] * self.p.atr_multiplier
            else:
                # Update trailing stop (only move up, never down)
                new_stop = d.close[0] - ind['atr'][0] * self.p.atr_multiplier
                if trailing_stop is None or new_stop > trailing_stop:
                    self.trailing_stops[ticker] = new_stop
                    trailing_stop = new_stop
                
                # Exit if price falls below trailing stop
                if d.close[0] < trailing_stop:
                    self.close(data=d)
                    self.trailing_stops[ticker] = None
