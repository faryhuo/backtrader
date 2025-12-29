import backtrader as bt


class UserStrategy(bt.Strategy):
    """
    Breakout Strategy - Multi-Data Support
    
    Buys when price breaks above the highest high of lookback period,
    sells when price breaks below the lowest low, or hits stop-loss/take-profit.
    Supports multiple data feeds for portfolio backtesting.
    """
    params = (
        ("lookback", 20),
        ("stop_loss", 0.05),   # e.g., 0.05 for 5%
        ("take_profit", 0.1),  # e.g., 0.1 for 10%
    )

    def __init__(self):
        self.indicators = {}
        self.entry_prices = {}
        
        # Create indicators for EACH data feed
        for d in self.datas:
            ticker = d._name
            self.indicators[d] = {
                'highest': bt.indicators.Highest(d.high, period=self.p.lookback),
                'lowest': bt.indicators.Lowest(d.low, period=self.p.lookback),
            }
            self.entry_prices[ticker] = None

    def next(self):
        # Apply trading logic to each data feed
        for d in self.datas:
            ticker = d._name
            ind = self.indicators[d]
            pos = self.getposition(d)
            entry_price = self.entry_prices.get(ticker)
            
            if not pos.size:
                # Breakout above highest high
                if d.close[0] > ind['highest'][-1]:
                    self.buy(data=d)
                    self.entry_prices[ticker] = d.close[0]
            else:
                # Exit conditions
                should_close = False
                
                # Breakdown below lowest low
                if d.close[0] < ind['lowest'][-1]:
                    should_close = True
                
                # Stop loss
                elif self.p.stop_loss is not None and entry_price is not None:
                    if d.close[0] <= entry_price * (1 - self.p.stop_loss):
                        should_close = True
                
                # Take profit
                elif self.p.take_profit is not None and entry_price is not None:
                    if d.close[0] >= entry_price * (1 + self.p.take_profit):
                        should_close = True
                
                if should_close:
                    self.close(data=d)
                    self.entry_prices[ticker] = None
