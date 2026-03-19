import backtrader as bt


class UserStrategy(bt.Strategy):
    """
    Minimal live test strategy.

    Behavior:
    - If there is no position, submit one buy order.
    - As soon as the buy is completed, immediately submit one close order.
    - No indicator logic. This is only for verifying the live order pipeline.
    """

    params = (("printlog", False),)

    def __init__(self):
        self.order = None
        self.bar_counter = 0

    def log(self, txt, dt=None, level="info"):
        dt = dt or self.datas[0].datetime.datetime(0)
        print(f"{dt} | {level.upper()} | {txt}")

    def next(self):
        self.bar_counter += 1

        if self.order and self.order.status not in [self.order.Submitted, self.order.Accepted]:
            self.log(
                f"clear stale order ref={self.order.ref} status={self.order.getstatusname()}",
                level="debug",
            )
            self.order = None

        if self.order:
            self.log(f"skip bar={self.bar_counter} pending_order={self.order.ref}", level="debug")
            return

        position_size = float(self.position.size) if self.position else 0.0
        self.log(
            f"bar={self.bar_counter} pos={position_size:.8f}",
            level="debug",
        )

        if position_size <= 0:
            self.log(
                f"BUY trigger bar={self.bar_counter} using broker sizer",
                level="info",
            )
            self.order = self.buy()
            return

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
            executed_size = abs(float(order.executed.size))
            self.log(
                f"{side} completed ref={order.ref} size={executed_size:.8f} "
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
