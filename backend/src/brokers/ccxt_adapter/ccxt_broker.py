"""
CCXT Broker - Backtrader broker implementation using CCXT for order execution.

This module provides a Backtrader-compatible broker that routes orders to
cryptocurrency exchanges via CCXT.
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, Optional

import backtrader as bt
import ccxt

from .ccxt_store import CCXTStore

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Helper to run async function from sync context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coro)


class CCXTOrder(bt.Order):
    """Extended order class that tracks CCXT exchange order ID."""

    def __init__(self):
        super().__init__()
        self.ccxt_order_id: Optional[str] = None


class CCXTBroker(bt.BrokerBase):
    """
    Broker implementation that routes orders to CCXT exchange.

    This class:
    - Submits orders to exchange via CCXT
    - Tracks positions and cash balance
    - Handles order lifecycle (submitted → filled → closed)
    - Provides portfolio valuation

    Attributes:
        store: CCXTStore instance
        exchange: CCXT exchange instance
        cash: Current cash balance
        value: Total portfolio value
    """

    params = (
        ('cash', 10000.0),  # Initial cash for paper trading
        ('commission', 0.001),  # Commission rate (0.1%)
        ('leverage', 1),  # Leverage multiplier
        ('session_id', None),  # Session ID for WebSocket broadcasting
    )

    def __init__(self, store: CCXTStore, **kwargs):
        """
        Initialize CCXT broker.

        Args:
            store: CCXTStore instance
            **kwargs: Additional parameters (cash, commission, leverage, session_id)
        """
        super().__init__()

        self.store = store
        self.exchange = store.get_exchange()

        # Override params with kwargs
        for key, value in kwargs.items():
            if hasattr(self.params, key):
                setattr(self.params, key, value)

        # Initialize cash
        self._cash = self.params.cash
        self._value = self.params.cash

        # Track positions: {data -> position object}
        self._positions: Dict[bt.DataBase, bt.Position] = defaultdict(bt.Position)

        # Track orders: {order_id -> order object}
        self._orders: Dict[int, CCXTOrder] = {}

        # Track submitted orders waiting for fill
        self._submitted_orders: Dict[int, CCXTOrder] = {}

        # Counter for generating order IDs
        self._order_id_counter = 0

        # Notifier for order/trade events
        self._notifiers = []

        # WebSocket manager (lazy import to avoid circular dependency)
        self._ws_manager = None
        self._session_id = self.params.session_id

        logger.info(
            f"Initialized CCXTBroker with cash={self._cash}, "
            f"commission={self.params.commission}, leverage={self.params.leverage}, "
            f"session_id={self._session_id}"
        )

    def _get_ws_manager(self):
        """Lazy import WebSocket manager to avoid circular dependency."""
        if self._ws_manager is None:
            try:
                from src.service.websocket_manager import get_websocket_manager
                self._ws_manager = get_websocket_manager()
            except ImportError:
                pass  # WebSocket not available
        return self._ws_manager

    def _broadcast_ws(self, coro):
        """Broadcast WebSocket message if session_id is set."""
        if self._session_id and self._get_ws_manager():
            try:
                _run_async(coro)
            except Exception as e:
                logger.debug(f"WebSocket broadcast failed: {e}")

    def start(self):
        """Called when broker starts."""
        super().start()

        # In paper mode, use configured cash
        if self.store.mode == 'paper':
            self._cash = self.params.cash
            logger.info(f"Paper trading mode: starting with ${self._cash}")
        else:
            # In live mode, fetch actual balance from exchange
            self._sync_balance()

    def stop(self):
        """Called when broker stops."""
        # Cancel all open orders
        for order in list(self._submitted_orders.values()):
            self.cancel(order)

        super().stop()

    def add_notifier(self, notifier):
        """Add notifier for order/trade events."""
        self._notifiers.append(notifier)

    def notify(self, order):
        """Notify all registered notifiers about order event."""
        for notifier in self._notifiers:
            if hasattr(notifier, 'notify_order'):
                notifier.notify_order(order)

    def submit(self, order: bt.Order) -> bt.Order:
        """
        Submit order to exchange.

        Args:
            order: Backtrader order object

        Returns:
            Order object with updated status
        """
        # Generate unique order ID
        self._order_id_counter += 1
        order_id = self._order_id_counter

        # Create CCXT order
        ccxt_order = CCXTOrder()
        ccxt_order.ref = order_id
        ccxt_order.created = bt.Order.Created
        ccxt_order.status = bt.Order.Submitted

        # Copy order details
        ccxt_order.data = order.data
        ccxt_order.size = order.size
        ccxt_order.price = order.price
        ccxt_order.pricelimit = order.pricelimit
        ccxt_order.trailamount = order.trailamount
        ccxt_order.trailpercent = order.trailpercent
        ccxt_order.exectype = order.exectype
        ccxt_order.valid = order.valid

        # Track order
        self._orders[order_id] = ccxt_order
        self._submitted_orders[order_id] = ccxt_order

        # Submit to exchange
        try:
            self._submit_order_to_exchange(ccxt_order)
            logger.info(
                f"Order submitted: {order_id} - "
                f"{self._order_side(ccxt_order)} {abs(ccxt_order.size)} "
                f"{ccxt_order.data._name} @ {ccxt_order.price or 'market'}"
            )
        except Exception as e:
            logger.error(f"Failed to submit order {order_id}: {e}")
            ccxt_order.status = bt.Order.Rejected
            self._submitted_orders.pop(order_id, None)
            self.notify(ccxt_order)

        return ccxt_order

    def cancel(self, order: bt.Order) -> bt.Order:
        """
        Cancel order on exchange.

        Args:
            order: Order to cancel

        Returns:
            Order object with updated status
        """
        if order.ref not in self._submitted_orders:
            logger.warning(f"Order {order.ref} not found or already filled/cancelled")
            return order

        try:
            if order.ccxt_order_id:
                # Cancel on exchange
                symbol = self._get_symbol(order.data)
                self.store.run_coroutine(
                    self.exchange.cancel_order(order.ccxt_order_id, symbol)
                )

            order.status = bt.Order.Cancelled
            self._submitted_orders.pop(order.ref, None)
            self.notify(order)

            logger.info(f"Order cancelled: {order.ref}")

        except Exception as e:
            logger.error(f"Failed to cancel order {order.ref}: {e}")

        return order

    def get_cash(self) -> float:
        """
        Get current cash balance.

        Returns:
            Available cash
        """
        return self._cash

    def get_value(self, datas: Optional[list] = None) -> float:
        """
        Get total portfolio value (cash + positions).

        Args:
            datas: Optional list of data feeds to value (default: all)

        Returns:
            Total portfolio value
        """
        # Start with cash
        value = self._cash

        # Add value of all positions
        for data, position in self._positions.items():
            if datas and data not in datas:
                continue

            if position.size != 0:
                # Get current price
                price = data.close[0] if len(data) > 0 else 0
                value += position.size * price

        self._value = value
        return value

    def getposition(self, data: bt.DataBase) -> bt.Position:
        """
        Get current position for given data feed.

        Args:
            data: Data feed

        Returns:
            Position object
        """
        return self._positions[data]

    def _submit_order_to_exchange(self, order: CCXTOrder) -> None:
        """
        Submit order to CCXT exchange.

        Args:
            order: CCXT order object

        Raises:
            Exception: If order submission fails
        """
        symbol = self._get_symbol(order.data)
        side = 'buy' if order.size > 0 else 'sell'
        amount = abs(order.size)

        # Determine order type
        order_type = self._get_order_type(order)

        # Build order parameters
        params = {}

        if order_type == 'market':
            # Market order
            ccxt_order = self.store.run_coroutine(
                self.exchange.create_market_order(symbol, side, amount, params)
            )
        elif order_type == 'limit':
            # Limit order
            price = order.price or order.pricelimit
            ccxt_order = self.store.run_coroutine(
                self.exchange.create_limit_order(symbol, side, amount, price, params)
            )
        else:
            raise ValueError(f"Unsupported order type: {order_type}")

        # Store CCXT order ID
        order.ccxt_order_id = ccxt_order['id']

        # Update order status based on exchange response
        if ccxt_order['status'] == 'closed':
            self._process_filled_order(order, ccxt_order)
        else:
            # Order is pending, will be checked in next() call
            order.status = bt.Order.Accepted

    def _process_filled_order(self, order: CCXTOrder, ccxt_order: dict) -> None:
        """
        Process filled order from exchange.

        Args:
            order: CCXT order object
            ccxt_order: Raw CCXT order response
        """
        # Extract fill details
        filled = ccxt_order.get('filled', 0)
        avg_price = ccxt_order.get('average', 0) or ccxt_order.get('price', 0)
        cost = ccxt_order.get('cost', filled * avg_price)
        fee_cost = ccxt_order.get('fee', {}).get('cost', 0) or cost * self.params.commission

        # Update order
        order.executed.size = filled if order.size > 0 else -filled
        order.executed.price = avg_price
        order.executed.value = cost
        order.executed.comm = fee_cost
        order.executed.dt = datetime.now()
        order.status = bt.Order.Completed

        # Update position
        position = self._positions[order.data]
        old_position_size = position.size
        position.update(order.executed.size, avg_price)

        # Update cash
        if order.size > 0:
            # Buy: decrease cash
            self._cash -= (cost + fee_cost)
        else:
            # Sell: increase cash
            self._cash += (cost - fee_cost)

        # Calculate P&L for the portfolio
        portfolio_value = self.get_value()
        pnl = portfolio_value - self.params.cash

        # Remove from submitted orders
        self._submitted_orders.pop(order.ref, None)

        # Notify
        self.notify(order)

        # Broadcast WebSocket updates
        ws_manager = self._get_ws_manager()
        if ws_manager and self._session_id:
            symbol = self._get_symbol(order.data)
            side = 'buy' if order.size > 0 else 'sell'

            # Broadcast order update
            self._broadcast_ws(ws_manager.broadcast_order_update(
                session_id=self._session_id,
                order_id=str(order.ref),
                symbol=symbol,
                side=side,
                size=abs(filled),
                price=avg_price,
                status='filled',
                filled_size=abs(filled),
                filled_price=avg_price
            ))

            # Broadcast trade executed
            self._broadcast_ws(ws_manager.broadcast_trade_executed(
                session_id=self._session_id,
                symbol=symbol,
                side=side,
                size=abs(filled),
                price=avg_price,
                commission=fee_cost,
                pnl=pnl if order.size < 0 else None  # P&L only on sells
            ))

            # Broadcast position update if position exists
            if position.size != 0:
                current_price = order.data.close[0] if len(order.data) > 0 else avg_price
                position_pnl = (current_price - position.price) * position.size

                self._broadcast_ws(ws_manager.broadcast_position_update(
                    session_id=self._session_id,
                    symbol=symbol,
                    size=position.size,
                    avg_price=position.price,
                    current_price=current_price,
                    pnl=position_pnl
                ))

            # Broadcast P&L update
            self._broadcast_ws(ws_manager.broadcast_pnl_update(
                session_id=self._session_id,
                current_pnl=pnl,
                total_pnl_percent=(pnl / self.params.cash * 100) if self.params.cash > 0 else 0,
                cash=self._cash,
                portfolio_value=portfolio_value
            ))

        logger.info(
            f"Order filled: {order.ref} - "
            f"{filled} @ {avg_price:.2f}, "
            f"cost={cost:.2f}, fee={fee_cost:.2f}, "
            f"new position={position.size}, cash={self._cash:.2f}"
        )

    def next(self) -> None:
        """
        Called on each bar to check order status.

        This method polls exchange for order updates and processes fills.
        """
        # Check status of submitted orders
        orders_to_update = list(self._submitted_orders.values())

        for order in orders_to_update:
            if not order.ccxt_order_id:
                continue

            try:
                symbol = self._get_symbol(order.data)
                ccxt_order = self.store.run_coroutine(
                    self.exchange.fetch_order(order.ccxt_order_id, symbol)
                )

                # Process based on status
                if ccxt_order['status'] == 'closed':
                    self._process_filled_order(order, ccxt_order)
                elif ccxt_order['status'] == 'canceled':
                    order.status = bt.Order.Cancelled
                    self._submitted_orders.pop(order.ref, None)
                    self.notify(order)

            except Exception as e:
                logger.error(f"Failed to fetch order status for {order.ref}: {e}")

    def _sync_balance(self) -> None:
        """Sync balance from exchange (for live trading)."""
        try:
            balance = self.store.run_coroutine(self.exchange.fetch_balance())
            # Assume trading in USDT for now
            self._cash = balance.get('USDT', {}).get('free', 0)
            logger.info(f"Synced balance from exchange: ${self._cash}")
        except Exception as e:
            logger.error(f"Failed to sync balance: {e}")

    def _get_symbol(self, data: bt.DataBase) -> str:
        """
        Get CCXT symbol from data feed.

        Args:
            data: Data feed

        Returns:
            CCXT symbol (e.g., 'BTC/USDT')
        """
        if hasattr(data, '_symbol'):
            return data._symbol
        elif hasattr(data, '_name'):
            return data._name
        else:
            raise ValueError("Data feed has no symbol information")

    def _get_order_type(self, order: CCXTOrder) -> str:
        """
        Determine CCXT order type from Backtrader order.

        Args:
            order: Backtrader order

        Returns:
            Order type ('market' or 'limit')
        """
        if order.exectype in (bt.Order.Market, bt.Order.Close):
            return 'market'
        elif order.exectype in (bt.Order.Limit, bt.Order.Stop, bt.Order.StopLimit):
            return 'limit'
        else:
            # Default to market
            return 'market'

    def _order_side(self, order: CCXTOrder) -> str:
        """Get order side ('buy' or 'sell')."""
        return 'buy' if order.size > 0 else 'sell'
