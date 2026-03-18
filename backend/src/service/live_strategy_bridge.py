"""Helpers for adapting Backtrader strategies to the live trading runtime."""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Optional


def wrap_strategy_with_live_gate(
    strategy_cls,
    log_callback: Callable[[str, str], None],
    data_status_callback: Optional[Callable[[str, object], None]] = None,
):
    """Wrap a strategy so historical warmup bars do not execute trading logic."""

    class LiveGatedStrategy(strategy_cls):
        def __init__(self, *args, **kwargs):
            self.__dict__['_log_cb'] = log_callback
            self.__dict__['_data_live'] = False
            super().__init__(*args, **kwargs)

        def log(self, txt, dt=None, level='info'):
            dt = dt or (self.datas[0].datetime.date(0) if len(self.datas[0]) else datetime.now())
            self._log_cb(level, f"{dt} | {txt}")

        def notify_data(self, data, status, *args, **kwargs):
            status_name = data._getstatusname(status).lower()
            if status == data.LIVE:
                self._data_live = True
                self._log_cb('info', f"Data feed entered LIVE mode: {getattr(data, '_symbol', 'unknown')}")
            elif status == data.DELAYED:
                self._data_live = False
                self._log_cb('info', f"Data feed warming up with historical bars: {getattr(data, '_symbol', 'unknown')}")

            if data_status_callback:
                data_status_callback(status_name, data)

            notify_data = getattr(super(), 'notify_data', None)
            if callable(notify_data):
                notify_data(data, status, *args, **kwargs)

        def next(self):
            if not self._data_live:
                return

            pos_before = self.position.size if self.position else 0
            super().next()

            try:
                dt = self.datas[0].datetime.datetime(0)
                close = self.datas[0].close[0]
                pos_after = self.position.size if self.position else 0

                if pos_after != pos_before:
                    side = 'BUY' if pos_after > pos_before else 'SELL'
                    self._log_cb('info', f"{dt} | {side} signal | price={close:.2f} | pos: {pos_before} -> {pos_after}")

                if len(self.datas[0]) % 10 == 0:
                    parts = [f"{dt} | close={close:.2f}"]
                    for attr_name in ('fast_ma', 'slow_ma', 'sma', 'ema', 'rsi', 'crossover'):
                        ind = getattr(self, attr_name, None)
                        if ind is not None and len(ind) > 0:
                            parts.append(f"{attr_name}={ind[0]:.4f}")
                    self._log_cb('debug', ' | '.join(parts))
            except Exception:
                pass

        def notify_order(self, order):
            super().notify_order(order)
            try:
                if order.status == order.Completed:
                    side = 'BUY' if order.isbuy() else 'SELL'
                    self._log_cb('info', f"Order {side} completed: size={order.executed.size:.6f} @ {order.executed.price:.2f}")
                elif order.status == order.Rejected:
                    self._log_cb('warning', f"Order REJECTED: {order.info}")
                elif order.status == order.Canceled:
                    self._log_cb('warning', 'Order CANCELED')
            except Exception:
                pass

        def notify_trade(self, trade):
            super().notify_trade(trade)
            try:
                if trade.isclosed:
                    self._log_cb('info', f"Trade closed: PnL={trade.pnl:.2f} ({trade.pnlcomm:.2f} after commission)")
            except Exception:
                pass

    LiveGatedStrategy.__name__ = strategy_cls.__name__
    LiveGatedStrategy.__qualname__ = strategy_cls.__qualname__
    return LiveGatedStrategy
