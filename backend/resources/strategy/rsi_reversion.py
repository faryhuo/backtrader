import backtrader as bt

class UserStrategy(bt.Strategy):
    params = (
        ("period", 14),
        ("lower", 30),
        ("upper", 70),
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI_SMA(self.data.close, period=self.p.period)

    def next(self):
        if not self.position and self.rsi < self.p.lower:
            self.buy()
        elif self.position and self.rsi > self.p.upper:
            self.close()
