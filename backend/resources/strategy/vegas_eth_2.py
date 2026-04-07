import backtrader as bt


class UserStrategy(bt.Strategy):
    """ETH pullback trend strategy with adaptive exits."""

    params = (
        # Entry structure: the fast tunnel defines the pullback zone, while the
        # trigger EMA confirms that momentum has turned back up after the dip.
        ('ema_s1', 8),
        ('ema_s2', 13),
        ('ema_fast', 5),

        # Higher-timeframe trend filter. Longs only when price and fast tunnel
        # are stacked above the slow trend EMAs.
        ('ema_l1', 34),
        ('ema_l2', 55),

        # Pullback and re-entry confirmation.
        ('pullback_lookback', 6),
        ('bounce_confirm_bars', 2),
        ('max_pullback_pct', 0.035),
        ('rsi_period', 8),
        ('rsi_floor', 45),

        # Entry sizing and breakout confirmation.
        ('order_size', 1.0),
        ('entry_buffer_pct', 0.001),

        # Swing-low protection. Stop starts below the recent low with a small
        # extra buffer to reduce accidental stop-outs on noise.
        ('stop_lookback', 6),
        ('stop_buffer_pct', 0.002),

        # ATR-based adaptive risk management. These make the bracket react to
        # current volatility instead of always using a fixed dollar distance.
        ('atr_period', 14),
        ('atr_stop_mult', 1.2),
        ('atr_target_mult', 2.4),

        # Fixed percentage profit target floor. The strategy uses the larger of
        # this value and the ATR-based target so take-profit is not too tight.
        ('take_profit_pct', 0.035),

        # Safety exit: do not let positions drift forever if momentum fades.
        ('max_hold_bars', 18),
    )

    def __init__(self):
        # Fast pullback tunnel plus higher-timeframe trend filters.
        self.tunnel_fast_top = bt.indicators.EMA(period=self.p.ema_s2)
        self.tunnel_fast_bot = bt.indicators.EMA(period=self.p.ema_s1)
        self.tunnel_slow = bt.indicators.EMA(period=self.p.ema_l1)
        self.tunnel_slower = bt.indicators.EMA(period=self.p.ema_l2)
        self.ema12 = bt.indicators.EMA(period=self.p.ema_fast)
        self.atr = bt.indicators.ATR(period=self.p.atr_period)
        self.rsi = bt.indicators.RSI(period=self.p.rsi_period)

        self.active_orders = []
        self.entry_bar = None

    def _has_pending_orders(self):
        return any(
            order.status in (order.Submitted, order.Accepted)
            for order in self.active_orders
        )

    def _clear_finished_orders(self):
        self.active_orders = [
            order
            for order in self.active_orders
            if order.status not in (
                order.Completed,
                order.Canceled,
                order.Margin,
                order.Rejected,
                order.Expired,
            )
        ]

    def _cancel_open_orders(self):
        for order in list(self.active_orders):
            if order.status in (order.Submitted, order.Accepted):
                self.cancel(order)

    def notify_order(self, order):
        if order not in self.active_orders:
            self.active_orders.append(order)

        if order.status == order.Completed and order.isbuy():
            self.entry_bar = len(self)
        elif order.status == order.Completed and order.issell() and not self.position:
            self.entry_bar = None
        elif order.status in (order.Canceled, order.Margin, order.Rejected, order.Expired):
            if not self.position:
                self.entry_bar = None

        self._clear_finished_orders()

    def next(self):
        self._clear_finished_orders()

        if self._has_pending_orders():
            return

        if not self.position:
            trend_up = (
                self.data.close[0] > self.tunnel_slow[0]
                and self.tunnel_fast_bot[0] > self.tunnel_slow[0]
                and self.tunnel_slow[0] > self.tunnel_slower[0]
            )
            if len(self.data) <= self.p.bounce_confirm_bars:
                return

            recent_high = max(
                self.data.high.get(
                    ago=0,
                    size=min(len(self.data), int(self.p.pullback_lookback)),
                )
            )
            if recent_high <= 0:
                return

            pullback_pct = max(0.0, (recent_high - self.data.close[0]) / recent_high)
            in_pullback_zone = (
                self.data.low[0] <= self.tunnel_fast_top[0]
                and self.data.close[0] >= self.tunnel_fast_bot[0]
                and pullback_pct <= self.p.max_pullback_pct
            )
            reclaimed_fast_tunnel = (
                self.data.close[-1] <= self.tunnel_fast_bot[-1]
                or self.ema12[-1] <= self.tunnel_fast_bot[-1]
            ) and (
                self.data.close[0] > self.tunnel_fast_bot[0]
                and self.ema12[0] > self.tunnel_fast_bot[0]
            )
            bounce_confirmed = (
                self.data.close[0] > self.data.close[-1]
                and self.ema12[0] > self.ema12[-1]
                and self.data.close[0] > self.tunnel_fast_bot[0] * (1.0 + self.p.entry_buffer_pct)
            )
            momentum_ok = self.rsi[0] >= self.p.rsi_floor

            if trend_up and in_pullback_zone and reclaimed_fast_tunnel and bounce_confirmed and momentum_ok:
                lookback = min(len(self.data), int(self.p.stop_lookback))
                if lookback <= 0:
                    return

                recent_low_stop = min(self.data.low.get(ago=0, size=lookback)) * (1.0 - self.p.stop_buffer_pct)
                atr_value = max(float(self.atr[0]), self.data.close[0] * 0.005)
                atr_stop = self.data.close[0] - (atr_value * self.p.atr_stop_mult)
                stop_price = min(recent_low_stop, atr_stop)

                pct_target = self.data.close[0] * (1.0 + self.p.take_profit_pct)
                atr_target = self.data.close[0] + (atr_value * self.p.atr_target_mult)
                limit_price = max(pct_target, atr_target)

                self.active_orders = list(self.buy_bracket(
                    size=self.p.order_size,
                    limitprice=limit_price,
                    stopprice=stop_price,
                    exectype=bt.Order.Market,
                ))
        else:
            bars_held = (len(self) - self.entry_bar) if self.entry_bar is not None else 0
            trend_broken = self.data.close[0] < self.tunnel_slow[0]
            momentum_broken = self.ema12[0] < self.tunnel_fast_bot[0] or self.rsi[0] < 40
            if trend_broken or momentum_broken or bars_held >= self.p.max_hold_bars:
                self._cancel_open_orders()
                self.close()
