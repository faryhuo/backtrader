import backtrader as bt


class UserStrategy(bt.Strategy):
    """
    SMA Crossover Strategy - Multi-Data Support
    
    Generates buy signals when fast MA crosses above slow MA,
    and sell signals when fast MA crosses below slow MA.
    Supports multiple data feeds for portfolio backtesting.
    """
    params = (
        ("fast_period", 10),
        ("slow_period", 30),
    )

    def __init__(self):
        self.indicators = {}
        
        # Create indicators for EACH data feed
        for d in self.datas:
            self.indicators[d] = {
                'fast_ma': bt.indicators.SMA(d.close, period=self.p.fast_period),
                'slow_ma': bt.indicators.SMA(d.close, period=self.p.slow_period),
            }
            self.indicators[d]['crossover'] = bt.indicators.CrossOver(
                self.indicators[d]['fast_ma'],
                self.indicators[d]['slow_ma']
            )

    def next(self):
        # Apply trading logic to each data feed
        for d in self.datas:
            ind = self.indicators[d]
            pos = self.getposition(d)
            
            if not pos.size and ind['crossover'] > 0:
                self.buy(data=d)
            elif pos.size and ind['crossover'] < 0:
                self.close(data=d)
