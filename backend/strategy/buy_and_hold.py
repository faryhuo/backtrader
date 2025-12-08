import backtrader as bt

class UserStrategy(bt.Strategy):
    def __init__(self):
        self.ordered = False

    def next(self):
        if not self.position and not self.ordered:
            self.buy()
            self.ordered = True
