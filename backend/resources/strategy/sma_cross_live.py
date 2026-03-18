"""
Simple Moving Average Crossover Strategy for Live Trading
Designed for Binance Spot - works without accessing data lines in __init__
"""
import backtrader as bt
import logging

logger = logging.getLogger(__name__)


class UserStrategy(bt.Strategy):
    """Simple SMA crossover strategy - works with live trading"""

    params = (
        ('fast_period', 10),
        ('slow_period', 30),
        ('printlog', False),
    )

    def __init__(self):
        # DO NOT access self.datas here - data isn't available yet!
        # Just set up the indicators
        print("[STRATEGY] UserStrategy __init__ called")

        self.fast_ma = bt.indicators.SimpleMovingAverage(
            self.data.close,
            period=self.p.fast_period
        )
        self.slow_ma = bt.indicators.SimpleMovingAverage(
            self.data.close,
            period=self.p.slow_period
        )
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

        # Track pending orders
        self.order = None
        self.buy_price = None
        self.buy_comm = None
        print("[STRATEGY] UserStrategy init complete, indicators ready")

    def _get_broker(self):
        """Get the broker, trying multiple ways to access it."""
        if hasattr(self, 'cerebro') and self.cerebro:
            return self.cerebro.broker
        return None

    def _send_log(self, level: str, message: str):
        """Send log to WebSocket via broker callback."""
        # Always print to console for debugging
        print(f"[STRATEGY LOG] {level}: {message}")

        # Try multiple ways to access broker
        broker = None

        # Method 1: via cerebro
        try:
            if hasattr(self, 'cerebro') and self.cerebro:
                broker = getattr(self.cerebro, 'broker', None)
                print(f"[STRATEGY] Got broker from cerebro: {broker}")
        except Exception as e:
            print(f"[STRATEGY] Error getting broker from cerebro: {e}")

        # Method 2: via strategy's broker attribute
        if not broker:
            try:
                broker = getattr(self, 'broker', None)
                print(f"[STRATEGY] Got broker from strategy: {broker}")
            except Exception as e:
                print(f"[STRATEGY] Error getting broker from strategy: {e}")

        if broker:
            # Try _log_callback
            if hasattr(broker, '_log_callback') and broker._log_callback:
                try:
                    broker._log_callback(level, message)
                    print(f"[STRATEGY] Sent log via _log_callback")
                except Exception as e:
                    print(f"[STRATEGY LOG ERROR] Failed to send log: {e}")
            else:
                print(f"[STRATEGY LOG ERROR] Broker has no _log_callback: {broker}")
        else:
            print(f"[STRATEGY LOG ERROR] Could not get broker at all")

    def log(self, txt, dt=None):
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self._send_log('buy', f'BUY EXECUTED, Price: {order.executed.price:.2f}')
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}')
                self.buy_price = order.executed.price
                self.buy_comm = order.executed.comm
            else:
                self._send_log('sell', f'SELL EXECUTED, Price: {order.executed.price:.2f}')
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self._send_log('info', f'TRADE PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')
        self.log(f'TRADE PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')

    def next(self):
        # Debug: log every bar
        print(f"[STRATEGY NEXT] Called at bar {len(self.datas[0])}, price={self.data.close[0]:.2f}")

        # Check if an order is pending
        if self.order:
            return

        # Log current state
        fast = self.fast_ma[0]
        slow = self.slow_ma[0]
        price = self.data.close[0]

        # Check if we are in the market
        if not self.position:
            # Not in market - look for buy signal
            if self.crossover > 0:
                print(f"[STRATEGY] BUY SIGNAL: Fast MA {fast:.2f} crossed above Slow MA {slow:.2f}, Price: {price:.2f}")
                self._send_log('buy', f'BUY SIGNAL: Fast MA {fast:.2f} crossed above Slow MA {slow:.2f}, Price: {price:.2f}')
                self.order = self.buy()
        else:
            # In market - look for sell signal
            if self.crossover < 0:
                print(f"[STRATEGY] SELL SIGNAL: Fast MA {fast:.2f} crossed below Slow MA {slow:.2f}, Price: {price:.2f}")
                self._send_log('sell', f'SELL SIGNAL: Fast MA {fast:.2f} crossed below Slow MA {slow:.2f}, Price: {price:.2f}')
                self.order = self.sell()
