import backtrader as bt


class UserStrategy(bt.Strategy):
    """
    Simple Buy and Hold Strategy - Multi-Data Support
    
    Buys and holds all assets in the portfolio.
    Supports multiple data feeds for portfolio backtesting.
    """
    
    def __init__(self):
        # Track which assets have been bought
        self.ordered = {d._name: False for d in self.datas}

    def next(self):
        # Apply buy-and-hold logic to each data feed
        for d in self.datas:
            ticker = d._name
            pos = self.getposition(d)
            
            if not pos.size and not self.ordered.get(ticker, False):
                self.buy(data=d)
                self.ordered[ticker] = True
