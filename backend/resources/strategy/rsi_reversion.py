import backtrader as bt


class UserStrategy(bt.Strategy):
    """
    RSI Mean Reversion Strategy - Multi-Data Support
    
    Buys when RSI is oversold (below lower threshold),
    sells when RSI is overbought (above upper threshold).
    Supports multiple data feeds for portfolio backtesting.
    """
    params = (
        ("period", 14),
        ("lower", 30),
        ("upper", 70),
    )

    def __init__(self):
        self.indicators = {}
        
        # Create RSI indicator for EACH data feed
        for d in self.datas:
            self.indicators[d] = {
                'rsi': bt.indicators.RSI_SMA(d.close, period=self.p.period)
            }

    def next(self):
        # Apply trading logic to each data feed
        for d in self.datas:
            ind = self.indicators[d]
            pos = self.getposition(d)
            
            if not pos.size and ind['rsi'] < self.p.lower:
                self.buy(data=d)
            elif pos.size and ind['rsi'] > self.p.upper:
                self.close(data=d)
