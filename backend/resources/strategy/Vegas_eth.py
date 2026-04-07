import backtrader as bt

class UserStrategy(bt.Strategy):
    params = (
        ('ema_s1', 48),
        ('ema_s2', 72),
        ('ema_l1', 144),
        ('ema_l2', 169),
        ('ema_fast', 12),
        ('take_profit_pct', 0.04),
        ('stop_lookback', 7),
        ('stop_buffer_pct', 0.003),
        ('entry_buffer_pct', 0.002),
    )

    def __init__(self):
        # 隧道線
        self.tunnel_fast_top = bt.indicators.EMA(period=self.p.ema_s2)
        self.tunnel_fast_bot = bt.indicators.EMA(period=self.p.ema_s1)
        self.tunnel_slow = bt.indicators.EMA(period=self.p.ema_l1)
        self.tunnel_slower = bt.indicators.EMA(period=self.p.ema_l2)
        self.ema12 = bt.indicators.EMA(period=self.p.ema_fast)
        
        # 買入信號：價格在長線上方 + EMA12 金叉隧道頂部
        self.long_signal = bt.indicators.CrossOver(self.ema12, self.tunnel_fast_top)
        self.trend_up = (
            (self.data.close > self.tunnel_slow)
            & (self.tunnel_slow > self.tunnel_slower)
        )

    def next(self):
        if not self.position:
            breakout_price = self.tunnel_fast_top[0] * (1.0 + self.p.entry_buffer_pct)
            if self.trend_up[0] and self.long_signal > 0 and self.data.close[0] >= breakout_price:
                # 計算止損：近期低點
                lookback = min(len(self.data), int(self.p.stop_lookback))
                if lookback <= 0:
                    return
                stop_price = min(self.data.low.get(ago=0, size=lookback)) * (
                    1.0 - self.p.stop_buffer_pct
                )
                limit_price = self.data.close[0] * (1.0 + self.p.take_profit_pct)
                self.buy_bracket(
                    limitprice=limit_price,
                    stopprice=stop_price,
                    exectype=bt.Order.Market,
                )
        else:
            # 簡單離場邏輯：EMA12 跌破隧道
            if self.ema12 < self.tunnel_fast_bot:
                self.close()
