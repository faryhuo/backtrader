"""
Live Engine - Orchestrates Binance Spot live/paper trading sessions.

Manages the full session lifecycle: creation → Cerebro startup → real-time
event routing (broker → WebSocket + DB) → graceful shutdown.
"""

import asyncio
import logging
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

import backtrader as bt

from src.brokers.binance_adapter import BinanceBroker, BinanceData, BinanceStore
from src.db import SessionStorage
from src.service.backtest_engine import TradeRecorder, load_user_strategy
from src.service.session_manager import SessionStatus, get_session_manager
from src.utils.config_loader import get_exchange_config, get_risk_config, load_broker_config

logger = logging.getLogger(__name__)

# Lazy-initialised storage
_session_storage: Optional[SessionStorage] = None

# Reference to the FastAPI (uvicorn) event loop — set once at startup
_main_loop: Optional[asyncio.AbstractEventLoop] = None


def set_main_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Called from FastAPI startup to capture the main event loop."""
    global _main_loop
    _main_loop = loop
    logger.info(f"Main event loop captured: {loop}")


def _get_storage() -> SessionStorage:
    global _session_storage
    if _session_storage is None:
        from src.config.settings import ensure_database_dir
        ensure_database_dir()
        _session_storage = SessionStorage()
    return _session_storage


class LiveTradingError(Exception):
    """Raised when live trading encounters an error."""


# Event types emitted by broker
class BrokerEvent:
    """Lightweight event emitted by the broker."""
    ORDER_SUBMITTED = 'order_submitted'
    ORDER_FILLED = 'order_filled'
    ORDER_PARTIAL = 'order_partial'
    ORDER_CANCELLED = 'order_cancelled'
    ORDER_REJECTED = 'order_rejected'
    TRADE_EXECUTED = 'trade_executed'
    POSITION_UPDATE = 'position_update'
    PNL_UPDATE = 'pnl_update'


def _wrap_strategy_with_logging(strategy_cls, log_callback: Callable):
    """
    Create a dynamic subclass that intercepts next() and log() to forward
    strategy decisions to the frontend via WebSocket.
    """

    print(f"[WRAP] Creating LoggingStrategy wrapper, callback: {log_callback}")

    class LoggingStrategy(strategy_cls):
        def __init__(self, *args, **kwargs):
            print(f"[WRAP] LoggingStrategy.__init__ called")
            # Store callback as instance attr via __dict__ to avoid
            # Python descriptor protocol binding self as first arg
            self.__dict__['_log_cb'] = log_callback
            super().__init__(*args, **kwargs)
            print(f"[WRAP] LoggingStrategy.__init__ done")

        def log(self, txt, dt=None, level='info'):
            dt = dt or (self.datas[0].datetime.date(0) if len(self.datas[0]) else datetime.now())
            msg = f"{dt} | {txt}"
            print(f"[WRAP] Strategy log: {msg}")
            try:
                self._log_cb(level, msg)
            except Exception as e:
                print(f"[WRAP] log callback error: {e}")

        def next(self):
            print(f"[WRAP] LoggingStrategy.next() called at bar {len(self.datas[0])}")
            # Capture key state before strategy runs
            pos_before = self.position.size if self.position else 0

            super().next()

            # After strategy runs, log current state
            try:
                dt = self.datas[0].datetime.datetime(0)
                close = self.datas[0].close[0]
                pos_after = self.position.size if self.position else 0

                # Log position changes
                if pos_after != pos_before:
                    side = 'BUY' if pos_after > pos_before else 'SELL'
                    self._log_cb('info', f"{dt} | {side} signal | price={close:.2f} | pos: {pos_before} -> {pos_after}")

                # Log indicator values every 10 bars
                if len(self.datas[0]) % 10 == 0:
                    parts = [f"{dt} | close={close:.2f}"]
                    # Try to extract common indicators
                    for attr_name in ('fast_ma', 'slow_ma', 'sma', 'ema', 'rsi', 'crossover'):
                        ind = getattr(self, attr_name, None)
                        if ind is not None and len(ind) > 0:
                            val = ind[0]
                            parts.append(f"{attr_name}={val:.4f}")
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
                    self._log_cb('warning', f"Order CANCELED")
            except Exception:
                pass

        def notify_trade(self, trade):
            super().notify_trade(trade)
            try:
                if trade.isclosed:
                    self._log_cb('info', f"Trade closed: PnL={trade.pnl:.2f} ({trade.pnlcomm:.2f} after commission)")
            except Exception:
                pass

    LoggingStrategy.__name__ = strategy_cls.__name__
    LoggingStrategy.__qualname__ = strategy_cls.__qualname__
    return LoggingStrategy


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
    store: Optional[BinanceStore] = None

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

        # 4. Initialise Binance adapter components
        store = BinanceStore(
            mode=mode,
            exchange_id=ex_config.ccxt_id,
            config={'default_market': 'spot', 'markets': ['spot']},
            user_id=user_id,
        )
        store.start()

        # Set up ticker callback for real-time price broadcast via WebSocket
        def on_ticker(ticker):
            try:
                ws = _get_ws_manager()
                if ws:
                    _run_ws(ws.broadcast_ticker(
                        session_id=session_id,
                        symbol=symbol,
                        last_price=ticker.get('last'),
                        bid=ticker.get('bid'),
                        ask=ticker.get('ask'),
                        timestamp=ticker.get('timestamp'),
                    ))
            except Exception as e:
                logger.debug(f"Ticker broadcast error: {e}")

        store.set_ticker_callback(on_ticker)
        store.start_ticker_stream(symbol)

        broker = BinanceBroker(
            store=store,
            cash=initial_cash,
            commission=commission,
            session_id=session_id,
            max_position_size_usd=risk_config.position_limits.max_position_size_usd,
            max_positions_count=risk_config.position_limits.max_positions_count,
            min_order_size_usd=risk_config.order_limits.min_order_size_usd,
            max_order_size_usd=risk_config.order_limits.max_order_size_usd,
        )

        # Calculate backfill start time based on timeframe
        # For 1m timeframe, get last 100 bars ≈ 100 minutes
        # IMPORTANT: Use UTC to match Binance timestamps
        now = datetime.utcnow()
        backfill_minutes = 100 if timeframe == '1m' else 200
        backfill_start = now - timedelta(minutes=backfill_minutes)

        data_feed = BinanceData(
            store=store,
            symbol=symbol,
            timeframe=timeframe,
            backfill=True,
            backfill_start=backfill_start,
            limit=100,
        )

        logger.info(f"[SESSION {session_id}] BinanceData created: symbol={symbol}, timeframe={timeframe}")

        # 5. Wire event callback (broker → WS + DB)
        broker.set_event_callback(
            _make_event_handler(session_id, session_manager, symbol)
        )

        # 5.1 Wire log callback for strategy logs
        # Also store logs in session for REST fallback
        session._strategy_logs = []
        logger.info(f"[SESSION {session_id}] Setting up log callback")

        def on_strategy_log(level: str, message: str):
            try:
                logger.info(f"[STRATEGY LOG {session_id}] {level}: {message}")
                # Store in-memory for REST access
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'level': level,
                    'message': message,
                }
                session._strategy_logs.append(log_entry)
                if len(session._strategy_logs) > 200:
                    session._strategy_logs = session._strategy_logs[-100:]

                # Broadcast via WebSocket
                ws = _get_ws_manager()
                if ws:
                    _run_ws(ws.broadcast_log(
                        session_id=session_id,
                        level=level,
                        message=message,
                    ))
            except Exception as e:
                logger.warning(f"Strategy log broadcast error: {e}")

        broker.set_log_callback(on_strategy_log)

        # 5.2 Wrap strategy class with logging interceptor
        strategy_cls = _wrap_strategy_with_logging(strategy_cls, on_strategy_log)

        # 6. Build Cerebro
        cerebro = bt.Cerebro()
        cerebro.addstrategy(strategy_cls)
        cerebro.adddata(data_feed)
        cerebro.setbroker(broker)

        logger.info(f"[SESSION {session_id}] Cerebro broker set: {cerebro.broker}")

        from src.service.analyzer_config import AnalyzerMode, configure_analyzers
        configure_analyzers(cerebro, AnalyzerMode.LIVE, TradeRecorder)

        # 6.1 Send historical OHLCV to frontend after WebSocket connects
        def send_initial_ohlcv():
            try:
                logger.info(f"send_initial_ohlcv called for session {session_id}")

                # Wait for WebSocket client to connect (frontend needs time after receiving session response)
                ws = _get_ws_manager()
                for i in range(15):  # Wait up to 15 seconds
                    if ws and ws.get_connection_count(session_id) > 0:
                        logger.info(f"WebSocket client connected after {i}s")
                        break
                    time.sleep(1)
                else:
                    logger.warning(f"No WebSocket client connected after 15s, sending anyway")

                # Calculate since time (150 minutes ago for 1m bars)
                since_ms = int((datetime.now() - timedelta(minutes=150)).timestamp() * 1000)

                logger.info(f"Fetching OHLCV for {symbol} timeframe={timeframe}")

                bars = store.fetch_ohlcv(
                    symbol=symbol,
                    interval=timeframe,
                    limit=100,
                    since_ms=since_ms,
                )

                logger.info(f"Fetched {len(bars) if bars else 0} bars")

                if bars:
                    ws = _get_ws_manager()
                    logger.info(f"WebSocket manager: {ws}")
                    if ws:
                        _run_ws(ws.broadcast_ohlcv(
                            session_id=session_id,
                            symbol=symbol,
                            ohlcv_list=bars,
                        ))
                        logger.info(f"Sent {len(bars)} historical bars to frontend")
                    else:
                        logger.warning("WS is None, cannot broadcast OHLCV")
                else:
                    logger.warning("No bars fetched")
            except Exception as e:
                logger.warning(f"Failed to send initial OHLCV: {e}")

        # 7. Store runtime objects
        session.cerebro = cerebro
        session.store = store

        # 8. Persist to DB
        _get_storage().save_session(session)

        # 9. Run Cerebro in background thread
        def _run():
            try:
                logger.info(f"[SESSION {session_id}] Starting Cerebro run...")
                session_manager.update_session(session_id, status=SessionStatus.RUNNING)
                _get_storage().save_session(session)
                _broadcast_status(session_id, 'starting', 'running')

                # Send initial OHLCV in a separate thread so it doesn't block Cerebro
                ohlcv_thread = threading.Thread(
                    target=send_initial_ohlcv, daemon=True,
                    name=f"OHLCV-{session_id[:8]}"
                )
                ohlcv_thread.start()

                logger.info(f"[SESSION {session_id}] Calling cerebro.run()...")
                cerebro.run()
                logger.info(f"[SESSION {session_id}] Cerebro.run() returned normally")

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
        logger.info(f"[SESSION {session_id}] Starting background thread...")
        thread.start()
        logger.info(f"[SESSION {session_id}] Background thread started")
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
    if not isinstance(broker, BinanceBroker):
        raise LiveTradingError("Broker does not support order cancellation")

    # Find order by ref or binance order id
    target = broker._orders.get(int(order_id)) if order_id.isdigit() else None

    if target:
        broker.cancel(target)
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
        'volume': ticker.get('volume'),
        'timestamp': ticker.get('timestamp'),
    }


def get_ohlcv(session_id: str, limit: int = 100) -> Dict:
    """Fetch historical OHLCV bars via REST (fallback for WebSocket)."""
    session = get_session_manager().get_session(session_id)
    if not session:
        raise LiveTradingError(f"Session {session_id} not found")

    if not session.store or not session.store._running:
        raise LiveTradingError("Exchange connection is not active")

    try:
        since_ms = int((datetime.now() - timedelta(minutes=limit * 2)).timestamp() * 1000)
        bars = session.store.fetch_ohlcv(
            symbol=session.symbol,
            interval=session.timeframe,
            limit=limit,
            since_ms=since_ms,
        )
        formatted = []
        for bar in (bars or []):
            formatted.append({
                'time': bar[0] / 1000,
                'open': bar[1],
                'high': bar[2],
                'low': bar[3],
                'close': bar[4],
                'volume': bar[5] if len(bar) > 5 else 0,
            })
        return {'symbol': session.symbol, 'bars': formatted}
    except Exception as e:
        raise LiveTradingError(f"Failed to fetch OHLCV: {e}") from e


def get_strategy_logs(session_id: str, limit: int = 100) -> Dict:
    """Get recent strategy log entries from in-memory buffer."""
    session = get_session_manager().get_session(session_id)
    if not session:
        raise LiveTradingError(f"Session {session_id} not found")

    logs = getattr(session, '_strategy_logs', [])
    return {'session_id': session_id, 'logs': logs[-limit:]}


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
        ws = get_websocket_manager()
        if ws is None:
            logger.warning("WebSocket manager is None")
        return ws
    except Exception as e:
        logger.warning(f"Failed to get WebSocket manager: {e}")
        return None


def _run_ws(coro) -> None:
    """Run a WebSocket manager coroutine from a background (sync) thread.

    The key insight: WebSocket send_json() must run on the FastAPI event loop
    (the one uvicorn is running), NOT the thread-local loop. We use
    asyncio.run_coroutine_threadsafe() to schedule the coroutine on the
    captured main loop.
    """
    global _main_loop
    if _main_loop is None or _main_loop.is_closed():
        logger.warning("[_run_ws] Main event loop not available, broadcast skipped")
        return

    try:
        future = asyncio.run_coroutine_threadsafe(coro, _main_loop)
        # Don't block waiting for result — fire and forget
        future.add_done_callback(_ws_broadcast_done)
    except Exception as e:
        logger.warning(f"[_run_ws] Failed to schedule broadcast: {e}")


def _ws_broadcast_done(future):
    """Callback for completed WebSocket broadcasts."""
    try:
        future.result()  # Raise any exception
    except Exception as e:
        logger.warning(f"[_run_ws] Broadcast failed: {e}")


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
            'exchange_order_id': data.get('binance_order_id'),
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
