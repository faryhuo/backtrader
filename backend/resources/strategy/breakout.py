import backtrader as bt



class UserStrategy(bt.Strategy):

    params = (

        ("lookback", 20),

        ("stop_loss", 0.05),  # e.g., 0.05 for 5%

        ("take_profit", 0.1),  # e.g., 0.1 for 10%

    )



    def __init__(self):

        self.highest = bt.indicators.Highest(self.data.high, period=self.p.lookback)

        self.lowest = bt.indicators.Lowest(self.data.low, period=self.p.lookback)

        self.entry_price = None



    def next(self):

        if not self.position:

            if self.data.close[0] > self.highest[-1]:

                order = self.buy()

                self.entry_price = self.data.close[0]

        else:

            if self.data.close[0] < self.lowest[-1]:

                self.close()

                self.entry_price = None

            elif self.p.stop_loss is not None and self.entry_price is not None:

                if self.data.close[0] <= self.entry_price * (1 - self.p.stop_loss):

                    self.close()

                    self.entry_price = None

            elif self.p.take_profit is not None and self.entry_price is not None:

                if self.data.close[0] >= self.entry_price * (1 + self.p.take_profit):

                    self.close()

                    self.entry_price = None

