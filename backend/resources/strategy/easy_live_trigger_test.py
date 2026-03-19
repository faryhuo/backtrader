import backtrader as bt


class UserStrategy(bt.Strategy):
    """
    Testing-only strategy for live/paper trading verification.

    Behavior:
    - Once the feed is LIVE, it alternates between buy and close on each bar.
    - It is intentionally noisy so strategy logs, orders, positions, and PnL
      updates are easy to verify from the UI.

    Do not use this for real trading.
    """

    params = (
        ("target_trade_value_usd", 25.0),
        ("min_trade_value_usd", 12.0),
        ("size_precision", 8),
        ("printlog", False),
    )

    def __init__(self):
        self.order = None
        self.bar_counter = 0

    def log(self, txt, dt=None, level="info"):
        dt = dt or self.datas[0].datetime.datetime(0)
        print(f"{dt} | {level.upper()} | {txt}")

    def next(self):
        self.bar_counter += 1

        if self.order:
            self.log(f"skip bar={self.bar_counter} pending_order={self.order.ref}", level="debug")
            return

        price = float(self.data.close[0])
        cash = float(self.broker.getcash())
        position_size = float(self.position.size) if self.position else 0.0

        self.log(
            f"bar={self.bar_counter} price={price:.6f} cash={cash:.2f} pos={position_size:.8f}",
            level="debug",
        )

        if position_size == 0:
            trade_value = min(max(self.p.target_trade_value_usd, self.p.min_trade_value_usd), cash * 0.5)
            if trade_value < self.p.min_trade_value_usd or price <= 0:
                self.log(
                    f"buy skipped trade_value={trade_value:.2f} price={price:.6f}",
                    level="warning",
                )
                return

            size = round(trade_value / price, self.p.size_precision)
            if size <= 0:
                self.log(f"buy skipped invalid size={size}", level="warning")
                return

            self.log(
                f"BUY trigger bar={self.bar_counter} trade_value={trade_value:.2f} size={size:.8f}",
                level="info",
            )
            self.order = self.buy(size=size)
        else:
            self.log(
                f"SELL trigger bar={self.bar_counter} close_position size={position_size:.8f}",
                level="info",
            )
            self.order = self.close()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status == order.Completed:
            side = "BUY" if order.isbuy() else "SELL"
            self.log(
                f"{side} completed ref={order.ref} size={abs(order.executed.size):.8f} "
                f"price={order.executed.price:.6f}",
                level="info",
            )
        elif order.status == order.Canceled:
            self.log(f"Order canceled ref={order.ref}", level="warning")
        elif order.status == order.Rejected:
            self.log(f"Order rejected ref={order.ref} info={order.info}", level="warning")
        elif order.status in (order.Margin, order.Expired):
            self.log(f"Order ended with status={order.getstatusname()} ref={order.ref}", level="warning")

        if self.order is order:
            self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log(
            f"trade closed pnl={trade.pnl:.6f} pnlcomm={trade.pnlcomm:.6f}",
            level="info",
        )
