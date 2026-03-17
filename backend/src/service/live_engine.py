"""
Live Engine - Orchestrates Binance Spot live/paper trading sessions.

Manages the full session lifecycle: creation → Cerebro startup → real-time
event routing (broker → WebSocket + DB) → graceful shutdown.
"""

import logging
import threading
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import backtrader as bt

from src.brokers.ccxt_adapter import CCXTBroker, CCXTData, CCXTStore
from src.brokers.ccxt_adapter.ccxt_broker import BrokerEvent
from src.db import SessionStorage
from src.service.backtest_engine import TradeRecorder, load_user_strategy
from src.service.session_manager import SessionStatus, get_session_manager
from src.utils.config_loader import get_exchange_config, get_risk_config, load_broker_config

logger = logging.getLogger(__name__)

# Lazy-initialised storage
_session_storage: Optional[SessionStorage] = None


def _get_storage() -> SessionStorage:
    global _session_storage
    if _session_storage is None:
        from src.config.settings import ensure_database_dir
        ensure_database_dir()
        _session_storage = SessionStorage()
    return _session_storage


class LiveTradingError(Exception):
    """Raised when live trading encounters an error."""


# ─────────────────────────────── public API ───────────────────────────────


def start_session(
    strategy_name: str,
    symbol: str,
    mode: str = 'paper',
    timeframe: str = '1m',
    initial_cash: float = 10000.0,
    commission: float = 0.001,
    user_id: Optional[str] = None,
) -> Dict:
    """
    Start a new Binance Spot live-trading session.

    Returns a session dict (including *session_id* and *ws_token*).
    """
    session_id = str(uuid.uuid4())
    exchange = 'binance'

    logger.info(
        f"Starting live session {session_id}: {strategy_name} "
        f"on {symbol} ({exchange} {mode})"
    )

    session_manager = get_session_manager()
    store: Optional[CCXTStore] = None

    try:
        # 1. Create in-memory session
        session = session_manager.create_session(
            session_id=session_id,
            strategy_name=strategy_name,
            symbol=symbol,
            exchange=exchange,
            mode=mode,
            timeframe=timeframe,
            initial_cash=initial_cash,
            commission=commission,
            user_id=user_id,
        )

        # 2. Load strategy class
        strategy_cls = load_user_strategy(strategy_name)

        # 3. Load broker config & risk limits
        broker_config = load_broker_config()
        risk_config = get_risk_config(broker_config)
        ex_config = get_exchange_config(exchange, broker_config)

        # 4. Initialise CCXT components
        store = CCXTStore(
            exchange_id=ex_config.ccxt_id,
            mode=mode,
            config={'default_market': 'spot', 'markets': ['spot']},
            user_id=user_id,
        )
        store.start()

        broker = CCXTBroker(
            store=store,
            cash=initial_cash,
            commission=commission,
            session_id=session_id,
            max_position_size_usd=risk_config.position_limits.max_position_size_usd,
            max_positions_count=risk_config.position_limits.max_positions_count,
            min_order_size_usd=risk_config.order_limits.min_order_size_usd,
            max_order_size_usd=risk_config.order_limits.max_order_size_usd,
        )

        data_feed = CCXTData(store=store, symbol=symbol, timeframe=timeframe)

        # 5. Wire event callback (broker → WS + DB)
        broker.set_event_callback(
            _make_event_handler(session_id, session_manager, symbol)
        )

        # 6. Build Cerebro
        cerebro = bt.Cerebro()
        cerebro.addstrategy(strategy_cls)
        cerebro.adddata(data_feed)
        cerebro.setbroker(broker)

        from src.service.analyzer_config import AnalyzerMode, configure_analyzers
        configure_analyzers(cerebro, AnalyzerMode.LIVE, TradeRecorder)

        # 7. Store runtime objects
        session.cerebro = cerebro
        session.store = store

        # 8. Persist to DB
        _get_storage().save_session(session)

        # 9. Run Cerebro in background thread
        def _run():
            try:
                session_manager.update_session(session_id, status=SessionStatus.RUNNING)
                _get_storage().save_session(session)
                _broadcast_status(session_id, 'starting', 'running')

                logger.info(f"Cerebro started for session {session_id}")
                cerebro.run()

                session.status = SessionStatus.STOPPED
                session.end_time = datetime.now()
                session_manager.update_session(
                    session_id, status=SessionStatus.STOPPED, end_time=session.end_time,
                )
                _get_storage().save_session(session)
                _broadcast_status(session_id, 'running', 'stopped')
                logger.info(f"Cerebro stopped normally for {session_id}")

            except Exception as e:
                session.status = SessionStatus.ERROR
                session.error_message = str(e)
                session.end_time = datetime.now()
                session_manager.update_session(
                    session_id,
                    status=SessionStatus.ERROR,
                    error_message=str(e),
                    end_time=session.end_time,
                )
                _get_storage().save_session(session)
                _broadcast_status(session_id, 'running', 'error')
                logger.exception(f"Error in session {session_id}: {e}")
            finally:
                if store:
                    store.stop()

        thread = threading.Thread(
            target=_run, daemon=True, name=f"Live-{session_id[:8]}"
        )
        thread.start()
        session.thread = thread

        logger.info(f"Session {session_id} launched")
        return session.to_dict()

    except Exception as e:
        session_manager.remove_session(session_id)
        if store:
            store.stop()
        logger.exception(f"Failed to start live session: {e}")
        raise LiveTradingError(f"Failed to start session: {e}") from e


def stop_session(session_id: str) -> Dict:
    """Gracefully stop a live-trading session."""
    logger.info(f"Stopping session {session_id}")

    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)
    if not session:
        raise LiveTradingError(f"Session {session_id} not found")

    success = session_manager.stop_session(session_id, timeout=10.0)
    if not success:
        raise LiveTradingError(f"Failed to stop session {session_id}")

    _get_storage().save_session(session)

    return {
        'session_id': session_id,
        'status': session.status.value,
        'final_pnl': session.current_pnl,
        'total_trades': session.total_trades,
        'end_time': session.end_time.isoformat() if session.end_time else None,
    }


def get_session_status(session_id: str) -> Dict:
    """Return session status dict. Raises if not found."""
    session = get_session_manager().get_session(session_id)
    if not session:
        raise LiveTradingError(f"Session {session_id} not found")
    return session.to_dict()


def get_session_orders(session_id: str) -> List[Dict]:
    """Get orders for a session (from in-memory broker or DB)."""
    session = get_session_manager().get_session(session_id)

    # Try in-memory broker first
    if session and session.cerebro:
        broker = session.cerebro.broker
        if hasattr(broker, 'get_open_orders_list'):
            return broker.get_open_orders_list()

    # Fallback to DB
    return _get_storage().get_session_orders(session_id)


def cancel_order(session_id: str, order_id: str) -> Dict:
    """Cancel an open order within a session."""
    session = get_session_manager().get_session(session_id)
    if not session:
        raise LiveTradingError(f"Session {session_id} not found")

    if not session.cerebro:
        raise LiveTradingError("Session has no active Cerebro instance")

    broker = session.cerebro.broker
    if not isinstance(broker, CCXTBroker):
        raise LiveTradingError("Broker does not support order cancellation")

    # Find order by ref or ccxt_order_id
    target = broker._orders.get(int(order_id)) if order_id.isdigit() else None

    if target:
        broker.cancel(target)
        return {'order_id': order_id, 'status': 'cancelled'}

    # Try by ccxt exchange order id
    success = broker.cancel_by_ccxt_id(order_id, session.symbol)
    if success:
        return {'order_id': order_id, 'status': 'cancelled'}

    raise LiveTradingError(f"Order {order_id} not found in session {session_id}")


def get_ticker_price(session_id: str) -> Dict:
    """Get current ticker price for the session's symbol."""
    session = get_session_manager().get_session(session_id)
    if not session:
        raise LiveTradingError(f"Session {session_id} not found")

    if not session.store:
        raise LiveTradingError("Session has no active exchange connection")

    if not session.store._running:
        raise LiveTradingError("Exchange connection is not active (session may have ended)")

    try:
        ticker = session.store.fetch_ticker(session.symbol)
    except RuntimeError as e:
        raise LiveTradingError(f"Cannot fetch ticker: {e}") from e

    return {
        'symbol': session.symbol,
        'last': ticker.get('last'),
        'bid': ticker.get('bid'),
        'ask': ticker.get('ask'),
        'high': ticker.get('high'),
        'low': ticker.get('low'),
        'volume': ticker.get('baseVolume'),
        'timestamp': ticker.get('timestamp'),
    }


# ─────────────────────────────── event handling ───────────────────────────────


def _make_event_handler(session_id: str, session_manager, symbol: str):
    """Create a broker event callback that routes events to WS + DB."""

    def handler(event_type: str, data: dict):
        try:
            _route_broker_event(session_id, session_manager, event_type, data)
        except Exception as e:
            logger.warning(f"Event routing error ({event_type}): {e}")

    return handler


def _route_broker_event(
    session_id: str, session_manager, event_type: str, data: dict
) -> None:
    """Route broker events to WebSocket manager and DB."""
    ws = _get_ws_manager()
    if not ws:
        return

    if event_type == BrokerEvent.ORDER_SUBMITTED:
        _run_ws(ws.broadcast_order_update(
            session_id=session_id,
            order_id=data['order_id'],
            symbol=data['symbol'],
            side=data['side'],
            size=data['size'],
            price=data.get('price') or 0,
            status='submitted',
        ))
        _persist_order(session_id, data, 'submitted')

    elif event_type == BrokerEvent.ORDER_FILLED:
        _run_ws(ws.broadcast_order_update(
            session_id=session_id,
            order_id=data['order_id'],
            symbol=data['symbol'],
            side=data['side'],
            size=data['size'],
            price=data['price'],
            status='filled',
            filled_size=data['size'],
            filled_price=data['price'],
        ))
        _update_order_status(data['order_id'], 'filled', data)

    elif event_type == BrokerEvent.ORDER_PARTIAL:
        _run_ws(ws.broadcast_order_update(
            session_id=session_id,
            order_id=data['order_id'],
            symbol=data['symbol'],
            side=data['side'],
            size=data['total_size'],
            price=data['avg_price'],
            status='partial',
            filled_size=data['filled_size'],
            filled_price=data['avg_price'],
        ))

    elif event_type == BrokerEvent.ORDER_CANCELLED:
        _run_ws(ws.broadcast_order_update(
            session_id=session_id,
            order_id=data['order_id'],
            symbol=data.get('symbol', ''),
            side='',
            size=0,
            price=0,
            status='cancelled',
        ))
        _update_order_status(data['order_id'], 'cancelled', data)

    elif event_type == BrokerEvent.ORDER_REJECTED:
        _run_ws(ws.broadcast_error(
            session_id=session_id,
            error_message=f"Order rejected: {data.get('reason', 'unknown')}",
            error_code='ORDER_REJECTED',
        ))

    elif event_type == BrokerEvent.TRADE_EXECUTED:
        _run_ws(ws.broadcast_trade_executed(
            session_id=session_id,
            symbol=data['symbol'],
            side=data['side'],
            size=data['size'],
            price=data['price'],
            commission=data.get('commission', 0),
            pnl=data.get('pnl'),
        ))
        # Update session trade count
        session = session_manager.get_session(session_id)
        if session:
            session.total_trades += 1

    elif event_type == BrokerEvent.POSITION_UPDATE:
        _run_ws(ws.broadcast_position_update(
            session_id=session_id,
            symbol=data['symbol'],
            size=data['size'],
            avg_price=data['avg_price'],
            current_price=data['current_price'],
            pnl=data['pnl'],
        ))

    elif event_type == BrokerEvent.PNL_UPDATE:
        _run_ws(ws.broadcast_pnl_update(
            session_id=session_id,
            current_pnl=data['current_pnl'],
            total_pnl_percent=data['total_pnl_percent'],
            cash=data['cash'],
            portfolio_value=data['portfolio_value'],
        ))
        session = session_manager.get_session(session_id)
        if session:
            session.current_pnl = data['current_pnl']


# ─────────────────────────────── helpers ───────────────────────────────


def _get_ws_manager():
    """Lazy import to avoid circular dependency."""
    try:
        from src.service.websocket_manager import get_websocket_manager
        return get_websocket_manager()
    except ImportError:
        return None


def _run_ws(coro) -> None:
    """Run a WebSocket manager coroutine from sync context."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(coro, loop=loop)
        else:
            loop.run_until_complete(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(coro)


def _broadcast_status(session_id: str, old: str, new: str) -> None:
    ws = _get_ws_manager()
    if ws:
        _run_ws(ws.broadcast_status_change(session_id, old, new))


def _persist_order(session_id: str, data: dict, status: str) -> None:
    """Save a new order to DB."""
    try:
        _get_storage().save_order({
            'order_id': data['order_id'],
            'session_id': session_id,
            'exchange_order_id': data.get('ccxt_order_id'),
            'symbol': data['symbol'],
            'side': data['side'],
            'type': data.get('order_type', 'market'),
            'size': data['size'],
            'price': data.get('price'),
            'status': status,
        })
    except Exception as e:
        logger.warning(f"Failed to persist order: {e}")


def _update_order_status(order_id: str, status: str, data: dict) -> None:
    """Update an existing order's status in DB."""
    try:
        storage = _get_storage()
        with storage.managed_session() as db:
            from src.db.models import OrderModel, OrderStatusEnum
            order = db.query(OrderModel).filter(
                OrderModel.order_id == order_id
            ).first()
            if order:
                order.status = OrderStatusEnum[status.upper()]
                if status == 'filled':
                    order.filled_size = data.get('size', 0)
                    order.filled_price = data.get('price', 0)
                    order.commission = data.get('commission', 0)
                    order.cost = data.get('cost', 0)
                    order.filled_at = datetime.utcnow()
    except Exception as e:
        logger.warning(f"Failed to update order status: {e}")
