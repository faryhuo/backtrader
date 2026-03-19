"""
Binance Broker - Backtrader-compatible broker using python-binance.

Routes orders to Binance Spot, tracks positions/cash.
"""

import logging
from collections import defaultdict, deque
from datetime import datetime
from typing import Callable, Dict, List, Optional

import backtrader as bt

from .common import data_symbol
from .binance_store import BinanceStore

logger = logging.getLogger(__name__)


class BinanceBuyOrder(bt.BuyOrder):
    """Buy-side order carrying Binance-specific tracking fields."""


class BinanceSellOrder(bt.SellOrder):
    """Sell-side order carrying Binance-specific tracking fields."""


class BinanceBroker(bt.BrokerBase):
    """
    Backtrader broker for Binance Spot using python-binance.

    Handles:
    - Order submission to Binance
    - Position and cash tracking
    - Paper trading simulation
    """

    params = (
        ('cash', 10000.0),
        ('commission', 0.001),
        ('session_id', None),
        ('quote_asset', 'USDT'),
        ('max_position_size_usd', None),
        ('max_positions_count', None),
        ('min_order_size_usd', None),
        ('max_order_size_usd', None),
    )

    def __init__(self, store: BinanceStore, **kwargs):
        super().__init__()

        self.store = store

        # Override params
        for key, value in kwargs.items():
            if hasattr(self.params, key):
                setattr(self.params, key, value)

        # Cash & value
        self._cash = float(self.params.cash)
        self._value = float(self.params.cash)
        self.startingcash = float(self.params.cash)

        # Positions: {data -> bt.Position}
        self._positions: Dict[bt.DataBase, bt.Position] = defaultdict(bt.Position)

        # Orders
        self._orders: Dict[int, bt.Order] = {}
        self._open_orders: Dict[int, bt.Order] = {}
        self._order_id_counter = 0

        # Notifications
        self._notifications: deque = deque()

        # Event callbacks
        self._event_callback: Optional[Callable] = None
        self._log_callback: Optional[Callable] = None
        self._session_id = self.params.session_id

        logger.info(
            f"BinanceBroker initialized: cash={self._cash}, "
            f"commission={self.params.commission}, session={self._session_id}"
        )

    # ──────────────────────────── callbacks ────────────────────────────

    def set_event_callback(self, callback: Callable) -> None:
        """Set callback for broker events."""
        self._event_callback = callback

    def set_log_callback(self, callback: Callable) -> None:
        """Set callback for strategy logs."""
        self._log_callback = callback

    def _emit(self, event_type: str, data: dict) -> None:
        """Emit an event."""
        if self._event_callback:
            try:
                self._event_callback(event_type, data)
            except Exception as e:
                logger.warning(f"Event callback error: {e}")

    # ──────────────────────────── lifecycle ────────────────────────────

    def start(self):
        super().start()
        self._sync_balance()
        logger.info(
            "%s mode account synced: cash=%s",
            "Paper/testnet" if self.store.is_paper_mode() else "Live",
            f"${self._cash:.2f}",
        )

    def stop(self):
        for order in list(self._open_orders.values()):
            self.cancel(order)
        super().stop()

    # ──────────────────────────── Backtrader interface ────────────────────────────

    def notify(self, order):
        self._notifications.append(order)

    def get_notification(self):
        try:
            return self._notifications.popleft()
        except IndexError:
            return None

    def get_cash(self) -> float:
        return self._cash

    def getcash(self) -> float:
        return self._cash

    def get_value(self, datas: Optional[list] = None) -> float:
        value = self._cash
        for data, position in self._positions.items():
            if datas and data not in datas:
                continue
            if position.size != 0:
                price = data.close[0] if len(data) > 0 else 0
                value += position.size * price
        self._value = value
        return value

    def getvalue(self, datas: Optional[list] = None) -> float:
        return self.get_value(datas)

    def getposition(self, data: bt.DataBase) -> bt.Position:
        return self._positions[data]

    # ──────────────────────────── order submission ────────────────────────────

    def buy(self, owner, data, size, price=None, plimit=None,
            exectype=bt.Order.Market, valid=None, tradeid=0, oco=None,
            trailamount=None, trailpercent=None, args=None, **kwargs):
        """Handle buy order."""
        logger.info(f"[BROKER] buy() called: size={size}, price={price}")

        order = self._create_order(
            owner=owner, data=data, size=abs(size), price=price,
            plimit=plimit, exectype=exectype, valid=valid, tradeid=tradeid,
            ordtype=bt.Order.Buy,
        )
        return self.submit(order)

    def sell(self, owner, data, size, price=None, plimit=None,
             exectype=bt.Order.Market, valid=None, tradeid=0, oco=None,
             trailamount=None, trailpercent=None, args=None, **kwargs):
        """Handle sell order."""
        logger.info(f"[BROKER] sell() called: size={size}, price={price}")

        order = self._create_order(
            owner=owner, data=data, size=abs(size), price=price,
            plimit=plimit, exectype=exectype, valid=valid, tradeid=tradeid,
            ordtype=bt.Order.Sell,
        )
        return self.submit(order)

    def _create_order(
        self, owner, data, size, price, plimit, exectype, valid, tradeid, ordtype,
    ) -> bt.Order:
        """Create a Backtrader order with Binance-specific tracking fields."""
        order_cls = BinanceBuyOrder if ordtype == bt.Order.Buy else BinanceSellOrder
        order = order_cls(
            data=data,
            size=size,
            price=price,
            pricelimit=plimit,
            exectype=exectype or bt.Order.Market,
            valid=valid,
            tradeid=tradeid,
            owner=owner,
            simulated=self.store.is_paper_mode(),
        )
        # Init extra tracking attrs (cannot be in __init__ due to bt metaclass)
        order.binance_order_id = None
        order.filled_size = 0.0
        order.filled_cost = 0.0
        return order

    def submit(self, order: bt.Order) -> bt.Order:
        """Submit order to Binance."""
        logger.info(f"Broker.submit() called: size={order.size}, price={order.price}")

        order_id = self._register_order(order)
        symbol = self._get_symbol(order.data)
        side = 'BUY' if order.ordtype == bt.Order.Buy else 'SELL'
        order_type = self._get_order_type(order)
        amount = abs(order.size)

        # Check cash for buy orders
        if order.ordtype == bt.Order.Buy:
            price_est = order.price or (order.data.close[0] if len(order.data) > 0 else 0)
            required = amount * price_est
            risk_error = self._validate_order_value(required)
            if risk_error:
                logger.warning(f"Order rejected: {risk_error}")
                order.status = bt.Order.Rejected
                self.notify(order)
                return order
            if required > self._cash:
                logger.warning(f"Order rejected: insufficient cash ({required} > {self._cash})")
                order.status = bt.Order.Rejected
                self.notify(order)
                return order
            if self._exceeds_position_limit(order.data, amount, price_est):
                logger.warning("Order rejected: position size limit exceeded")
                order.status = bt.Order.Rejected
                self.notify(order)
                return order
            if self._exceeds_positions_count(order.data, amount):
                logger.warning("Order rejected: max positions count exceeded")
                order.status = bt.Order.Rejected
                self.notify(order)
                return order
        else:
            position = self._positions[order.data]
            price_est = order.price or (order.data.close[0] if len(order.data) > 0 else 0)
            risk_error = self._validate_order_value(amount * price_est)
            if risk_error:
                logger.warning(f"Order rejected: {risk_error}")
                order.status = bt.Order.Rejected
                self.notify(order)
                return order
            if position.size < amount:
                logger.warning(f"Order rejected: insufficient position ({amount} > {position.size})")
                order.status = bt.Order.Rejected
                self.notify(order)
                return order

        # Submit to exchange
        self._mark_order_submitted(order)

        try:
            result = self.store.create_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=amount,
                price=order.price,
            )

            order.binance_order_id = result.get('orderId')
            self._emit('order_submitted', self._build_order_submission_event(order, symbol, side, amount))

            # Check if immediately filled
            status = result.get('status', '').upper()
            if status == 'FILLED':
                self._process_fill(order, result)
            else:
                order.status = bt.Order.Accepted

            logger.info(
                f"Order {order_id} submitted: {side} {amount} {symbol} "
                f"@ {order.price or 'market'}, binance_id={order.binance_order_id}"
            )

        except Exception as e:
            logger.error(f"Failed to submit order: {e}")
            self._reject_order(order, symbol, str(e))

        return order

    def cancel(self, order: bt.Order) -> bt.Order:
        """Cancel an order."""
        if order.ref not in self._open_orders:
            logger.warning(f"Order {order.ref} not open")
            return order

        try:
            if order.binance_order_id:
                symbol = self._get_symbol(order.data)
                self.store.cancel_order(symbol, order.binance_order_id)

            order.status = bt.Order.Cancelled
            del self._open_orders[order.ref]
            self.notify(order)

            logger.info(f"Order {order.ref} cancelled")

        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")

        return order

    # ──────────────────────────── order polling ────────────────────────────

    def next(self) -> None:
        """Poll exchange for open order updates."""
        for order in list(self._open_orders.values()):
            if not order.binance_order_id:
                continue

            try:
                symbol = self._get_symbol(order.data)
                result = self.store.get_order(symbol, order.binance_order_id)

                status = result.get('status', '').upper()
                if status == 'FILLED':
                    self._process_fill(order, result)
                elif status == 'CANCELED':
                    order.status = bt.Order.Cancelled
                    del self._open_orders[order.ref]
                    self.notify(order)

            except Exception as e:
                logger.error(f"Failed to poll order: {e}")

    def _process_fill(self, order: bt.Order, result: dict) -> None:
        """Process a filled order."""
        fill = self._extract_fill(result)
        if not fill:
            return

        filled = fill['filled']
        price = fill['price']
        cost = fill['cost']
        commission = fill['commission']

        self._apply_execution_to_order(order, filled, price, cost, commission)

        position = self._positions[order.data]
        position.update(order.executed.size, price)

        if getattr(self.store, 'uses_exchange_account_data', lambda: False)():
            self._sync_balance()
        else:
            self._apply_cash_change(order, cost, commission)

        self._open_orders.pop(order.ref, None)
        self.notify(order)
        self._emit_fill_events(order, position, filled, price, cost, commission)

        logger.info(
            f"Order {order.ref} filled: {filled} @ {price:.2f}, "
            f"fee={commission:.4f}, cash={self._cash:.2f}"
        )

    # ──────────────────────────── helpers ────────────────────────────

    def _get_symbol(self, data) -> str:
        return data_symbol(data)

    def _register_order(self, order: bt.Order) -> int:
        self._order_id_counter += 1
        order.ref = self._order_id_counter
        self._orders[order.ref] = order
        return order.ref

    def _mark_order_submitted(self, order: bt.Order) -> None:
        order.status = bt.Order.Submitted
        self._open_orders[order.ref] = order

    def _reject_order(self, order: bt.Order, symbol: str, reason: str) -> None:
        order.status = bt.Order.Rejected
        self._open_orders.pop(order.ref, None)
        self.notify(order)
        self._emit('order_rejected', {
            'order_id': str(order.ref),
            'symbol': symbol,
            'reason': reason,
        })

    def _extract_fill(self, result: dict) -> Optional[Dict[str, float]]:
        filled = float(result.get('executedQty', 0))
        if filled == 0:
            return None

        price = self._resolve_fill_price(result, filled)
        cost = filled * price
        return {
            'filled': filled,
            'price': price,
            'cost': cost,
            'commission': cost * self.params.commission,
        }

    def _resolve_fill_price(self, result: dict, filled: float) -> float:
        price = float(result.get('price', 0) or 0)
        if price > 0:
            return price

        fills = result.get('fills') or []
        if fills:
            total_qty = 0.0
            total_cost = 0.0
            for fill in fills:
                fill_qty = float(fill.get('qty', 0) or 0)
                fill_price = float(fill.get('price', 0) or 0)
                total_qty += fill_qty
                total_cost += fill_qty * fill_price
            if total_qty > 0:
                return total_cost / total_qty

        cumulative_quote = float(result.get('cummulativeQuoteQty', 0) or 0)
        if cumulative_quote > 0 and filled > 0:
            return cumulative_quote / filled

        return 0.0

    def _apply_execution_to_order(
        self,
        order: bt.Order,
        filled: float,
        price: float,
        cost: float,
        commission: float,
    ) -> None:
        order.executed.size = filled if order.ordtype == bt.Order.Buy else -filled
        order.executed.price = price
        order.executed.value = cost
        order.executed.comm = commission
        order.executed.dt = datetime.now()
        order.status = bt.Order.Completed
        order.filled_size = filled
        order.filled_cost = cost

    def _apply_cash_change(self, order: bt.Order, cost: float, commission: float) -> None:
        if order.ordtype == bt.Order.Buy:
            self._cash -= (cost + commission)
        else:
            self._cash += (cost - commission)

    def _validate_order_value(self, order_value: float) -> Optional[str]:
        min_order_size = self.params.min_order_size_usd
        max_order_size = self.params.max_order_size_usd

        if min_order_size is not None and order_value < float(min_order_size):
            return f"order value below minimum ({order_value} < {min_order_size})"
        if max_order_size is not None and order_value > float(max_order_size):
            return f"order value above maximum ({order_value} > {max_order_size})"
        return None

    def _exceeds_position_limit(self, data: bt.DataBase, amount: float, price: float) -> bool:
        max_position_size = self.params.max_position_size_usd
        if max_position_size is None:
            return False

        position = self._positions[data]
        next_size = position.size + amount
        return abs(next_size * price) > float(max_position_size)

    def _exceeds_positions_count(self, data: bt.DataBase, amount: float) -> bool:
        max_positions_count = self.params.max_positions_count
        if max_positions_count is None or amount <= 0:
            return False

        position = self._positions[data]
        opening_new_position = position.size == 0
        if not opening_new_position:
            return False

        open_positions = sum(1 for pos in self._positions.values() if pos.size != 0)
        return open_positions >= int(max_positions_count)

    def _emit_fill_events(
        self,
        order: bt.Order,
        position: bt.Position,
        filled: float,
        price: float,
        cost: float,
        commission: float,
    ) -> None:
        symbol = self._get_symbol(order.data)
        side = 'buy' if order.ordtype == bt.Order.Buy else 'sell'
        portfolio_value = self.get_value()
        pnl = portfolio_value - self.startingcash

        self._emit('order_filled', {
            'order_id': str(order.ref),
            'binance_order_id': order.binance_order_id,
            'symbol': symbol,
            'side': side,
            'size': filled,
            'price': price,
            'cost': cost,
            'commission': commission,
        })
        self._emit('trade_executed', {
            'symbol': symbol,
            'side': side,
            'size': filled,
            'price': price,
            'commission': commission,
        })

        if position.size != 0:
            current_price = order.data.close[0] if len(order.data) > 0 else price
            pos_pnl = (current_price - position.price) * position.size
            self._emit('position_update', {
                'symbol': symbol,
                'size': position.size,
                'avg_price': position.price,
                'current_price': current_price,
                'pnl': pos_pnl,
                'side': 'long' if position.size > 0 else 'short',
            })

        self._emit('pnl_update', {
            'current_pnl': pnl,
            'total_pnl_percent': (pnl / self.startingcash * 100) if self.startingcash > 0 else 0,
            'cash': self._cash,
            'portfolio_value': portfolio_value,
        })

    def _build_order_submission_event(
        self,
        order: bt.Order,
        symbol: str,
        side: str,
        amount: float,
    ) -> Dict[str, object]:
        return {
            'order_id': str(order.ref),
            'binance_order_id': order.binance_order_id,
            'symbol': symbol,
            'side': side.lower(),
            'size': amount,
            'price': order.price,
        }

    def _get_order_type(self, order) -> str:
        if order.exectype in (bt.Order.Market, bt.Order.Close):
            return 'MARKET'
        elif order.exectype in (bt.Order.Limit, bt.Order.Stop, bt.Order.StopLimit):
            return 'LIMIT'
        return 'MARKET'

    def _sync_balance(self) -> None:
        """Sync balance from exchange."""
        try:
            account = self.store.get_account()
            quote_asset = str(self.params.quote_asset or 'USDT').upper()
            for balance in account.get('balances', []):
                if balance['asset'].upper() == quote_asset:
                    self._cash = float(balance.get('free', 0))
                    logger.info("Synced %s balance: $%.2f", quote_asset, self._cash)
                    break
            else:
                raise ValueError(f"Quote asset {quote_asset} not found in account balances")
        except Exception as e:
            logger.error(f"Failed to sync balance: {e}")

    # ──────────────────────────── state ────────────────────────────

    def get_open_orders_list(self) -> List[Dict]:
        """Get serializable list of open orders."""
        result = []
        for order in self._open_orders.values():
            symbol = self._get_symbol(order.data) if order.data else ''
            result.append({
                'order_id': str(order.ref),
                'binance_order_id': order.binance_order_id,
                'symbol': symbol,
                'side': 'buy' if order.ordtype == bt.Order.Buy else 'sell',
                'size': order.size,
                'price': order.price,
                'type': self._get_order_type(order),
                'filled_size': order.filled_size,
                'status': 'open',
            })
        return result

    def get_positions_list(self) -> List[Dict]:
        """Get serializable list of positions."""
        result = []
        for data, position in self._positions.items():
            if position.size == 0:
                continue
            symbol = self._get_symbol(data)
            current_price = data.close[0] if len(data) > 0 else position.price
            pnl = (current_price - position.price) * position.size
            result.append({
                'symbol': symbol,
                'size': position.size,
                'avg_price': position.price,
                'current_price': current_price,
                'pnl': pnl,
                'side': 'long' if position.size > 0 else 'short',
            })
        return result
