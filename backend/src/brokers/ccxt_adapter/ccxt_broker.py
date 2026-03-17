"""
CCXT Broker - Backtrader broker implementation for Binance Spot via CCXT.

Routes orders to Binance, tracks positions/cash, handles order lifecycle,
and emits events for WebSocket broadcasting.
"""

import logging
from collections import defaultdict, deque
from datetime import datetime
from typing import Callable, Dict, List, Optional

import backtrader as bt

from .ccxt_store import CCXTStore

logger = logging.getLogger(__name__)


class CCXTOrder(bt.Order):
    """Extended order with CCXT exchange order ID tracking."""

    def __init__(self):
        super().__init__()
        self.ccxt_order_id: Optional[str] = None
        self.filled_size: float = 0.0  # cumulative filled
        self.filled_cost: float = 0.0  # cumulative cost
        self.filled_commission: float = 0.0


# ─────────────────────── Event types emitted by broker ───────────────────────

class BrokerEvent:
    """Lightweight event emitted by the broker for external consumers."""
    ORDER_SUBMITTED = 'order_submitted'
    ORDER_FILLED = 'order_filled'
    ORDER_PARTIAL = 'order_partial'
    ORDER_CANCELLED = 'order_cancelled'
    ORDER_REJECTED = 'order_rejected'
    TRADE_EXECUTED = 'trade_executed'
    POSITION_UPDATE = 'position_update'
    PNL_UPDATE = 'pnl_update'


class CCXTBroker(bt.BrokerBase):
    """
    Broker that routes orders to Binance Spot via CCXT.

    Key improvements over previous version:
    - Event-based: emits BrokerEvents via callback instead of direct WS calls
    - Risk checks: validates order against configurable limits before submission
    - Partial fill handling: tracks cumulative fills
    - Order cancellation: cancel() sends cancel to exchange
    """

    params = (
        ('cash', 10000.0),
        ('commission', 0.001),
        ('session_id', None),
        # Risk limits (populated from broker_config.json)
        ('max_position_size_usd', 5000.0),
        ('max_positions_count', 5),
        ('min_order_size_usd', 10.0),
        ('max_order_size_usd', 5000.0),
    )

    def __init__(self, store: CCXTStore, **kwargs):
        super().__init__()

        self.store = store
        self.exchange = store.get_exchange()

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
        self._orders: Dict[int, CCXTOrder] = {}
        self._open_orders: Dict[int, CCXTOrder] = {}
        self._order_id_counter = 0

        # Notification queue for Cerebro
        self._notifications: deque = deque()

        # Event callback: fn(event_type: str, data: dict)
        self._event_callback: Optional[Callable] = None
        self._session_id = self.params.session_id

        logger.info(
            f"CCXTBroker initialized: cash={self._cash}, "
            f"commission={self.params.commission}, session={self._session_id}"
        )

    # ──────────────────────────── event system ────────────────────────────

    def set_event_callback(self, callback: Callable) -> None:
        """Set callback for broker events: fn(event_type: str, data: dict)."""
        self._event_callback = callback

    def _emit(self, event_type: str, data: dict) -> None:
        """Emit an event to the registered callback."""
        if self._event_callback:
            try:
                self._event_callback(event_type, data)
            except Exception as e:
                logger.warning(f"Event callback error ({event_type}): {e}")

    # ──────────────────────────── lifecycle ────────────────────────────

    def start(self):
        super().start()
        if self.store.mode == 'paper':
            self._cash = float(self.params.cash)
            logger.info(f"Paper trading mode: starting with ${self._cash:.2f}")
        else:
            self._sync_balance()

    def stop(self):
        # Cancel all open orders on shutdown
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

    def submit(self, order: bt.Order) -> bt.Order:
        """Submit order to Binance after risk checks."""
        self._order_id_counter += 1
        order_id = self._order_id_counter

        # Build CCXT order wrapper
        ccxt_order = CCXTOrder()
        ccxt_order.ref = order_id
        ccxt_order.created = bt.Order.Created
        ccxt_order.data = order.data
        ccxt_order.size = order.size
        ccxt_order.price = order.price
        ccxt_order.pricelimit = order.pricelimit
        ccxt_order.trailamount = order.trailamount
        ccxt_order.trailpercent = order.trailpercent
        ccxt_order.exectype = order.exectype
        ccxt_order.valid = order.valid

        symbol = self._get_symbol(ccxt_order.data)
        side = 'buy' if ccxt_order.size > 0 else 'sell'
        amount = abs(ccxt_order.size)

        # Risk check
        rejection = self._check_risk(ccxt_order, symbol, amount)
        if rejection:
            logger.warning(f"Order {order_id} rejected: {rejection}")
            ccxt_order.status = bt.Order.Rejected
            self._orders[order_id] = ccxt_order
            self.notify(ccxt_order)
            self._emit(BrokerEvent.ORDER_REJECTED, {
                'order_id': str(order_id),
                'symbol': symbol,
                'side': side,
                'size': amount,
                'reason': rejection,
            })
            return ccxt_order

        # Track
        ccxt_order.status = bt.Order.Submitted
        self._orders[order_id] = ccxt_order
        self._open_orders[order_id] = ccxt_order

        # Submit to exchange
        try:
            self._submit_to_exchange(ccxt_order)
            logger.info(
                f"Order {order_id} submitted: {side} {amount} {symbol} "
                f"@ {ccxt_order.price or 'market'}"
            )
            self._emit(BrokerEvent.ORDER_SUBMITTED, {
                'order_id': str(order_id),
                'symbol': symbol,
                'side': side,
                'size': amount,
                'price': ccxt_order.price,
                'order_type': self._get_order_type(ccxt_order),
            })
        except Exception as e:
            logger.error(f"Failed to submit order {order_id}: {e}")
            ccxt_order.status = bt.Order.Rejected
            self._open_orders.pop(order_id, None)
            self.notify(ccxt_order)
            self._emit(BrokerEvent.ORDER_REJECTED, {
                'order_id': str(order_id),
                'symbol': symbol,
                'side': side,
                'size': amount,
                'reason': str(e),
            })

        return ccxt_order

    def cancel(self, order: bt.Order) -> bt.Order:
        """Cancel an open order on exchange."""
        if order.ref not in self._open_orders:
            logger.warning(f"Order {order.ref} not open – cannot cancel")
            return order

        try:
            if order.ccxt_order_id:
                symbol = self._get_symbol(order.data)
                self.store.run_coroutine(
                    self.exchange.cancel_order(order.ccxt_order_id, symbol)
                )

            order.status = bt.Order.Cancelled
            self._open_orders.pop(order.ref, None)
            self.notify(order)

            symbol = self._get_symbol(order.data)
            self._emit(BrokerEvent.ORDER_CANCELLED, {
                'order_id': str(order.ref),
                'ccxt_order_id': order.ccxt_order_id,
                'symbol': symbol,
            })
            logger.info(f"Order {order.ref} cancelled")

        except Exception as e:
            logger.error(f"Failed to cancel order {order.ref}: {e}")

        return order

    def cancel_by_ccxt_id(self, ccxt_order_id: str, symbol: str) -> bool:
        """Cancel an order using its exchange order ID. Returns True on success."""
        # Find the matching internal order
        target = None
        for order in self._open_orders.values():
            if order.ccxt_order_id == ccxt_order_id:
                target = order
                break

        if target:
            self.cancel(target)
            return True

        # Not tracked locally — try cancelling directly on exchange
        try:
            self.store.run_coroutine(
                self.exchange.cancel_order(ccxt_order_id, symbol)
            )
            logger.info(f"Cancelled exchange order {ccxt_order_id} directly")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel exchange order {ccxt_order_id}: {e}")
            return False

    # ──────────────────────────── order polling (called each bar) ────────────────────────────

    def next(self) -> None:
        """Poll exchange for open order updates. Called each bar by Cerebro."""
        for order in list(self._open_orders.values()):
            if not order.ccxt_order_id:
                continue

            try:
                symbol = self._get_symbol(order.data)
                ccxt_result = self.store.run_coroutine(
                    self.exchange.fetch_order(order.ccxt_order_id, symbol),
                    timeout=10,
                )
                self._process_exchange_order(order, ccxt_result)

            except Exception as e:
                logger.error(f"Failed to poll order {order.ref}: {e}")

    # ──────────────────────────── query helpers ────────────────────────────

    def get_open_orders_list(self) -> List[Dict]:
        """Return serializable list of currently open orders."""
        result = []
        for order in self._open_orders.values():
            symbol = self._get_symbol(order.data) if order.data else ''
            result.append({
                'order_id': str(order.ref),
                'ccxt_order_id': order.ccxt_order_id,
                'symbol': symbol,
                'side': 'buy' if order.size > 0 else 'sell',
                'size': abs(order.size),
                'price': order.price,
                'type': self._get_order_type(order),
                'filled_size': order.filled_size,
                'status': 'open',
            })
        return result

    def get_positions_list(self) -> List[Dict]:
        """Return serializable list of current positions."""
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
                'pnl_percent': (pnl / (abs(position.size) * position.price) * 100)
                if position.price > 0 else 0,
                'side': 'long' if position.size > 0 else 'short',
            })
        return result

    # ──────────────────────────── internals ────────────────────────────

    def _check_risk(self, order: CCXTOrder, symbol: str, amount: float) -> Optional[str]:
        """Validate order against risk limits. Returns rejection reason or None."""
        price_est = order.price or (order.data.close[0] if len(order.data) > 0 else 0)
        if price_est <= 0:
            return None  # cannot estimate, allow

        notional = amount * price_est

        if notional < self.params.min_order_size_usd:
            return f"Order size ${notional:.2f} below minimum ${self.params.min_order_size_usd}"

        if notional > self.params.max_order_size_usd:
            return f"Order size ${notional:.2f} exceeds maximum ${self.params.max_order_size_usd}"

        # Check max positions
        active_positions = sum(1 for p in self._positions.values() if p.size != 0)
        if order.size > 0 and active_positions >= self.params.max_positions_count:
            # Only block new buys, not sells/closes
            return f"Max {self.params.max_positions_count} concurrent positions reached"

        # Check max position size
        if notional > self.params.max_position_size_usd:
            return f"Position notional ${notional:.2f} exceeds max ${self.params.max_position_size_usd}"

        return None

    def _submit_to_exchange(self, order: CCXTOrder) -> None:
        """Submit order to Binance via CCXT."""
        symbol = self._get_symbol(order.data)
        side = 'buy' if order.size > 0 else 'sell'
        amount = abs(order.size)
        order_type = self._get_order_type(order)

        if order_type == 'market':
            ccxt_result = self.store.run_coroutine(
                self.exchange.create_market_order(symbol, side, amount)
            )
        elif order_type == 'limit':
            price = order.price or order.pricelimit
            ccxt_result = self.store.run_coroutine(
                self.exchange.create_limit_order(symbol, side, amount, price)
            )
        else:
            raise ValueError(f"Unsupported order type: {order_type}")

        order.ccxt_order_id = ccxt_result['id']

        # If immediately filled (market orders often are)
        if ccxt_result.get('status') == 'closed':
            self._process_exchange_order(order, ccxt_result)
        else:
            order.status = bt.Order.Accepted

    def _process_exchange_order(self, order: CCXTOrder, ccxt_result: dict) -> None:
        """Process exchange order response — handles filled, partial, cancelled."""
        status = ccxt_result.get('status', '')
        filled = float(ccxt_result.get('filled', 0) or 0)
        avg_price = float(ccxt_result.get('average', 0) or ccxt_result.get('price', 0) or 0)

        symbol = self._get_symbol(order.data)
        side = 'buy' if order.size > 0 else 'sell'

        if status == 'closed' and filled > 0:
            # Fully filled
            cost = float(ccxt_result.get('cost', filled * avg_price) or filled * avg_price)
            fee_info = ccxt_result.get('fee') or {}
            fee_cost = float(fee_info.get('cost', 0) or 0) or cost * self.params.commission

            # Update order execution info
            order.executed.size = filled if order.size > 0 else -filled
            order.executed.price = avg_price
            order.executed.value = cost
            order.executed.comm = fee_cost
            order.executed.dt = datetime.now()
            order.status = bt.Order.Completed
            order.filled_size = filled
            order.filled_cost = cost
            order.filled_commission = fee_cost

            # Update position
            position = self._positions[order.data]
            position.update(order.executed.size, avg_price)

            # Update cash
            if order.size > 0:
                self._cash -= (cost + fee_cost)
            else:
                self._cash += (cost - fee_cost)

            # Remove from open
            self._open_orders.pop(order.ref, None)
            self.notify(order)

            # Emit events
            portfolio_value = self.get_value()
            pnl = portfolio_value - self.startingcash

            self._emit(BrokerEvent.ORDER_FILLED, {
                'order_id': str(order.ref),
                'ccxt_order_id': order.ccxt_order_id,
                'symbol': symbol,
                'side': side,
                'size': filled,
                'price': avg_price,
                'cost': cost,
                'commission': fee_cost,
            })

            self._emit(BrokerEvent.TRADE_EXECUTED, {
                'symbol': symbol,
                'side': side,
                'size': filled,
                'price': avg_price,
                'commission': fee_cost,
                'pnl': pnl if order.size < 0 else None,
            })

            self._emit_position_and_pnl(order, symbol, pnl, portfolio_value)

            logger.info(
                f"Order {order.ref} filled: {filled} @ {avg_price:.2f}, "
                f"fee={fee_cost:.4f}, cash={self._cash:.2f}"
            )

        elif status == 'canceled':
            order.status = bt.Order.Cancelled
            self._open_orders.pop(order.ref, None)
            self.notify(order)

            self._emit(BrokerEvent.ORDER_CANCELLED, {
                'order_id': str(order.ref),
                'ccxt_order_id': order.ccxt_order_id,
                'symbol': symbol,
            })

        elif filled > order.filled_size:
            # Partial fill progress
            order.filled_size = filled
            order.filled_cost = float(ccxt_result.get('cost', filled * avg_price) or filled * avg_price)

            self._emit(BrokerEvent.ORDER_PARTIAL, {
                'order_id': str(order.ref),
                'ccxt_order_id': order.ccxt_order_id,
                'symbol': symbol,
                'side': side,
                'filled_size': filled,
                'total_size': abs(order.size),
                'avg_price': avg_price,
            })

    def _emit_position_and_pnl(
        self, order: CCXTOrder, symbol: str, pnl: float, portfolio_value: float
    ) -> None:
        """Emit position and P&L update events after a fill."""
        position = self._positions[order.data]

        if position.size != 0:
            current_price = order.data.close[0] if len(order.data) > 0 else position.price
            pos_pnl = (current_price - position.price) * position.size
            self._emit(BrokerEvent.POSITION_UPDATE, {
                'symbol': symbol,
                'size': position.size,
                'avg_price': position.price,
                'current_price': current_price,
                'pnl': pos_pnl,
                'pnl_percent': (pos_pnl / (abs(position.size) * position.price) * 100)
                if position.price > 0 else 0,
                'side': 'long' if position.size > 0 else 'short',
            })

        self._emit(BrokerEvent.PNL_UPDATE, {
            'current_pnl': pnl,
            'total_pnl_percent': (pnl / self.startingcash * 100) if self.startingcash > 0 else 0,
            'cash': self._cash,
            'portfolio_value': portfolio_value,
        })

    def _sync_balance(self) -> None:
        """Sync balance from exchange for live mode."""
        try:
            balance_info = self.store.get_account_balance('USDT')
            self._cash = balance_info['free']
            logger.info(f"Synced balance from exchange: ${self._cash:.2f}")
        except Exception as e:
            logger.error(f"Failed to sync balance: {e}")

    def _get_symbol(self, data: bt.DataBase) -> str:
        if hasattr(data, '_symbol'):
            return data._symbol
        elif hasattr(data, '_name'):
            return data._name
        raise ValueError("Data feed has no symbol information")

    def _get_order_type(self, order: CCXTOrder) -> str:
        if order.exectype in (bt.Order.Market, bt.Order.Close):
            return 'market'
        elif order.exectype in (bt.Order.Limit, bt.Order.Stop, bt.Order.StopLimit):
            return 'limit'
        return 'market'
