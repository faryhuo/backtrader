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

from src.brokers.binance_adapter import BinanceBroker, BinanceData, BinanceStore, TIMEFRAME_SECONDS
from src.config.config_manager import get_global_config_manager, get_user_config_manager
from src.contracts.sizer_config import SizerConfig, SizerType
from src.db import SessionStorage
from src.db.storage.session import build_session_order_pk
from src.service.backtest_engine import TradeRecorder, load_user_strategy
from src.service.live_strategy_bridge import wrap_strategy_with_live_gate
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


def _get_config_manager(user_id: Optional[str]):
    return get_user_config_manager(user_id) if user_id else get_global_config_manager()


def _get_exchange_credentials(exchange: str, mode: str, user_id: Optional[str]) -> Dict[str, str]:
    config_manager = _get_config_manager(user_id)
    credentials = config_manager.get_ccxt_credentials(exchange, mode)
    api_key = credentials.get('api_key')
    api_secret = credentials.get('secret')

    if not api_key or not api_secret:
        raise LiveTradingError(
            f"Missing {exchange} {mode} API credentials. "
            f"Configure API key and secret before starting the session."
        )

    return {
        'api_key': api_key,
        'api_secret': api_secret,
    }


def _extract_quote_asset(symbol: str) -> str:
    if '/' not in symbol:
        raise LiveTradingError(f"Unsupported symbol format: {symbol}")
    base_asset, quote_asset = symbol.split('/', 1)
    if not base_asset or not quote_asset:
        raise LiveTradingError(f"Unsupported symbol format: {symbol}")
    return quote_asset.upper()


def _extract_symbol_assets(symbol: str) -> tuple[str, str]:
    if '/' not in symbol:
        raise LiveTradingError(f"Unsupported symbol format: {symbol}")
    base_asset, quote_asset = symbol.split('/', 1)
    if not base_asset or not quote_asset:
        raise LiveTradingError(f"Unsupported symbol format: {symbol}")
    return base_asset.upper(), quote_asset.upper()


def _get_free_quote_balance(account: dict, quote_asset: str) -> float:
    balances = account.get('balances')
    if not isinstance(balances, list):
        raise LiveTradingError("Exchange account response did not include balances.")

    for balance in balances:
        if balance.get('asset', '').upper() != quote_asset:
            continue
        free_value = balance.get('free')
        if free_value in (None, ''):
            raise LiveTradingError(
                f"Exchange account did not provide free balance for quote asset {quote_asset}."
            )
        return float(free_value)

    raise LiveTradingError(
        f"Exchange account does not contain quote asset balance for {quote_asset}."
    )


def _extract_balance_components(account: dict, symbol: str) -> Dict[str, float]:
    """Extract base/quote balance components for a symbol from an exchange account payload."""
    balances = account.get('balances')
    if not isinstance(balances, list):
        raise LiveTradingError("Exchange account response did not include balances.")

    base_asset, quote_asset = _extract_symbol_assets(symbol)
    balance_map = {
        str(item.get('asset') or '').upper(): item
        for item in balances
    }
    base_balance = balance_map.get(base_asset, {})
    quote_balance = balance_map.get(quote_asset, {})

    base_free = _safe_float(base_balance.get('free')) or 0.0
    base_locked = _safe_float(base_balance.get('locked')) or 0.0
    quote_free = _safe_float(quote_balance.get('free')) or 0.0
    quote_locked = _safe_float(quote_balance.get('locked')) or 0.0

    return {
        'base_free': base_free,
        'base_locked': base_locked,
        'base_size': base_free + base_locked,
        'quote_free': quote_free,
        'quote_locked': quote_locked,
    }


def _safe_float(value) -> Optional[float]:
    if value in (None, ''):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_exchange_timestamp(value) -> Optional[str]:
    timestamp_ms = None
    if isinstance(value, (int, float)):
        timestamp_ms = int(value)
    elif isinstance(value, str) and value.isdigit():
        timestamp_ms = int(value)

    if timestamp_ms is None or timestamp_ms <= 0:
        return None
    return datetime.fromtimestamp(timestamp_ms / 1000).isoformat()


def _build_session_result(current_pnl: float, baseline_value: float) -> Dict[str, float | str | bool]:
    """Build a normalized session profit/loss payload for REST and WebSocket consumers."""
    safe_pnl = float(current_pnl or 0.0)
    safe_baseline = float(baseline_value or 0.0)
    pnl_percent = ((safe_pnl / safe_baseline) * 100.0) if safe_baseline > 0 else 0.0

    if safe_pnl > 0:
        status = 'profit'
    elif safe_pnl < 0:
        status = 'loss'
    else:
        status = 'flat'

    return {
        'status': status,
        'amount': safe_pnl,
        'absolute_amount': abs(safe_pnl),
        'percent': pnl_percent,
        'baseline_value': safe_baseline,
        'is_profit': status == 'profit',
        'is_loss': status == 'loss',
        'is_flat': status == 'flat',
    }


def _get_timeframe_seconds(timeframe: str) -> int:
    """Return the live timeframe duration in seconds."""
    return max(int(TIMEFRAME_SECONDS.get(timeframe, 60)), 1)


def _calculate_ohlcv_since_ms(
    timeframe: str,
    limit: int,
    *,
    multiplier: int = 2,
    now: Optional[datetime] = None,
) -> int:
    """Calculate a lookback window large enough to fetch the requested closed bars."""
    bar_seconds = _get_timeframe_seconds(timeframe)
    lookback_seconds = max(bar_seconds * max(limit, 1) * max(multiplier, 1), bar_seconds)
    current_time = now or datetime.utcnow()
    return int((current_time - timedelta(seconds=lookback_seconds)).timestamp() * 1000)


def _normalize_order_status(status: Optional[str]) -> str:
    mapping = {
        'NEW': 'open',
        'PARTIALLY_FILLED': 'partial',
        'FILLED': 'filled',
        'CANCELED': 'cancelled',
        'CANCELLED': 'cancelled',
        'PENDING_CANCEL': 'cancelled',
        'REJECTED': 'rejected',
        'EXPIRED': 'expired',
    }
    if not status:
        return 'unknown'
    return mapping.get(str(status).upper(), str(status).lower())


def _classify_trading_error(reason: Optional[str]) -> str:
    text = str(reason or '').lower()

    if 'lot_size' in text:
        return 'BINANCE_LOT_SIZE'
    if 'min_notional' in text or 'notional' in text:
        return 'BINANCE_MIN_NOTIONAL'
    if 'insufficient balance' in text or 'insufficient cash' in text:
        return 'INSUFFICIENT_BALANCE'
    if 'insufficient position' in text:
        return 'INSUFFICIENT_POSITION'
    if 'position size limit exceeded' in text:
        return 'POSITION_LIMIT_EXCEEDED'
    if 'max positions count exceeded' in text:
        return 'MAX_POSITIONS_EXCEEDED'
    if 'below minimum' in text:
        return 'ORDER_VALUE_TOO_SMALL'
    if 'above maximum' in text:
        return 'ORDER_VALUE_TOO_LARGE'
    return 'ORDER_REJECTED'


def _normalize_exchange_symbol(symbol: Optional[str]) -> Optional[str]:
    if not symbol:
        return None
    text = str(symbol)
    if '/' in text:
        return text
    if text.endswith('USDT') and len(text) > 4:
        return f"{text[:-4]}/USDT"
    return text


def _aggregate_exchange_trades(trades: List[dict]) -> Dict[str, Dict]:
    grouped: Dict[str, Dict] = {}

    for trade in trades:
        order_id = trade.get('orderId')
        if order_id in (None, ''):
            continue

        key = str(order_id)
        qty = _safe_float(trade.get('qty')) or 0.0
        quote_qty = _safe_float(trade.get('quoteQty')) or 0.0
        price = _safe_float(trade.get('price'))
        fee = _safe_float(trade.get('commission')) or 0.0
        fee_asset = trade.get('commissionAsset')
        trade_time = _format_exchange_timestamp(trade.get('time'))

        bucket = grouped.setdefault(key, {
            'filled_size': 0.0,
            'executed_quote_qty': 0.0,
            'fee': 0.0,
            'fee_assets': set(),
            'trade_count': 0,
            'last_fill_at': None,
        })

        bucket['filled_size'] += qty
        bucket['executed_quote_qty'] += quote_qty
        bucket['fee'] += fee
        bucket['trade_count'] += 1

        if fee_asset:
            bucket['fee_assets'].add(str(fee_asset).upper())

        if trade_time and (not bucket['last_fill_at'] or trade_time > bucket['last_fill_at']):
            bucket['last_fill_at'] = trade_time

        if qty > 0 and price is not None:
            weighted_quote = bucket.get('_weighted_quote', 0.0) + (qty * price)
            bucket['_weighted_quote'] = weighted_quote

    for bucket in grouped.values():
        weighted_quote = bucket.pop('_weighted_quote', 0.0)
        filled_size = bucket['filled_size']
        bucket['filled_price'] = (weighted_quote / filled_size) if filled_size > 0 else None
        bucket['fee_asset'] = ', '.join(sorted(bucket['fee_assets'])) if bucket['fee_assets'] else None
        bucket.pop('fee_assets', None)

    return grouped


def _normalize_exchange_order(exchange_order: dict, session_id: str) -> Dict:
    exchange_order_id = str(
        exchange_order.get('orderId')
        or exchange_order.get('id')
        or exchange_order.get('clientOrderId')
        or ''
    )
    client_order_id = exchange_order.get('clientOrderId')
    size = _safe_float(exchange_order.get('origQty') or exchange_order.get('orig_qty')) or 0.0
    filled_size = _safe_float(
        exchange_order.get('executedQty') or exchange_order.get('executed_qty')
    ) or 0.0
    price = _safe_float(exchange_order.get('price'))
    cummulative_quote_qty = _safe_float(
        exchange_order.get('cummulativeQuoteQty') or exchange_order.get('cumulativeQuoteQty')
    )
    filled_price = None
    if filled_size > 0:
        filled_price = _safe_float(exchange_order.get('avgPrice'))
        if filled_price is None and cummulative_quote_qty is not None:
            filled_price = cummulative_quote_qty / filled_size

    return {
        'order_id': exchange_order_id or str(client_order_id or ''),
        'db_order_id': build_session_order_pk(
            session_id,
            str(client_order_id or exchange_order_id or ''),
        ) if (client_order_id or exchange_order_id) else None,
        'exchange_order_id': exchange_order_id or None,
        'symbol': _normalize_exchange_symbol(exchange_order.get('symbol')),
        'side': str(exchange_order.get('side') or '').lower() or None,
        'type': str(exchange_order.get('type') or '').lower() or None,
        'size': size,
        'price': price,
        'status': _normalize_order_status(exchange_order.get('status')),
        'filled_size': filled_size,
        'filled_price': filled_price,
        'executed_quote_qty': cummulative_quote_qty,
        'fee': None,
        'fee_asset': None,
        'trade_count': 0,
        'last_fill_at': None,
        'created_at': _format_exchange_timestamp(
            exchange_order.get('time') or exchange_order.get('transactTime')
        ),
        'updated_at': _format_exchange_timestamp(exchange_order.get('updateTime')),
        'metadata': {
            'source': 'exchange',
            'client_order_id': client_order_id,
            'in_session': None,
        },
    }


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


def start_session(
    strategy_name: str,
    symbol: str,
    mode: str = 'paper',
    timeframe: str = '1m',
    params: Optional[dict] = None,
    sizer_type: str = 'fixed_size',
    sizer_config: Optional[dict] = None,
    initial_cash: float = 10000.0,
    commission: float = 0.0,
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
    effective_initial_cash = float(initial_cash)
    effective_commission = 0.0

    try:
        # 1. Load strategy class
        strategy_cls = load_user_strategy(strategy_name)

        # 2. Load broker config & risk limits
        broker_config = load_broker_config()
        risk_config = get_risk_config(broker_config)
        ex_config = get_exchange_config(exchange, broker_config)
        credentials = _get_exchange_credentials(exchange, mode, user_id)
        quote_asset = _extract_quote_asset(symbol)

        # 3. Initialise Binance adapter components and verify exchange-backed data.
        store = BinanceStore(
            api_key=credentials['api_key'],
            api_secret=credentials['api_secret'],
            mode=mode,
            exchange_id=ex_config.ccxt_id,
            config={'default_market': 'spot', 'markets': ['spot']},
            user_id=user_id,
            session_id=session_id,
        )
        store.start()
        account = store.get_account()
        balance_snapshot = _extract_balance_components(account, symbol)
        effective_initial_cash = balance_snapshot['quote_free']

        bars_probe = store.fetch_ohlcv(
            symbol=symbol,
            interval=timeframe,
            limit=2,
        )
        if not bars_probe:
            raise LiveTradingError(
                f"Exchange API returned no OHLCV data for {symbol} [{timeframe}]."
            )

        ticker = store.fetch_ticker(symbol)
        baseline_price = _safe_float(ticker.get('last')) or 0.0
        baseline_portfolio_value = (
            balance_snapshot['quote_free']
            + balance_snapshot['quote_locked']
            + (balance_snapshot['base_size'] * baseline_price)
        )

        # 4. Create in-memory session with exchange-derived cash snapshot.
        session = session_manager.create_session(
            session_id=session_id,
            strategy_name=strategy_name,
            symbol=symbol,
            exchange=exchange,
            mode=mode,
            timeframe=timeframe,
            initial_cash=effective_initial_cash,
            commission=effective_commission,
            user_id=user_id,
        )
        session_manager.update_session(
            session_id,
            baseline_quote_free=balance_snapshot['quote_free'],
            baseline_quote_locked=balance_snapshot['quote_locked'],
            baseline_base_size=balance_snapshot['base_size'],
            baseline_price=baseline_price,
            baseline_portfolio_value=baseline_portfolio_value,
        )

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
            cash=effective_initial_cash,
            commission=effective_commission,
            session_id=session_id,
            quote_asset=quote_asset,
            max_position_size_usd=risk_config.position_limits.max_position_size_usd,
            max_positions_count=risk_config.position_limits.max_positions_count,
            min_order_size_usd=risk_config.order_limits.min_order_size_usd,
            max_order_size_usd=risk_config.order_limits.max_order_size_usd,
        )

        # Calculate backfill start time based on timeframe
        # For 1m timeframe, get last 100 bars ≈ 100 minutes
        # IMPORTANT: Use UTC to match Binance timestamps
        backfill_start = datetime.utcnow() - timedelta(
            seconds=_get_timeframe_seconds(timeframe) * 100
        )

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
        session._trade_errors = []
        session.feed_status = 'warming_up'
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
        def on_data_status(status: str, data) -> None:
            normalized = 'live' if status == 'live' else 'warming_up'
            session.feed_status = normalized
            session_manager.update_session(session_id, feed_status=normalized)
            ws = _get_ws_manager()
            if ws:
                _run_ws(ws.broadcast_feed_status(
                    session_id=session_id,
                    status=normalized,
                    symbol=getattr(data, '_symbol', symbol),
                ))

        strategy_cls = wrap_strategy_with_live_gate(
            strategy_cls,
            on_strategy_log,
            on_data_status,
        )

        # 6. Build Cerebro
        strategy_params = dict(params or {})

        cerebro = bt.Cerebro()
        cerebro.addstrategy(strategy_cls, **strategy_params)
        cerebro.adddata(data_feed)
        cerebro.setbroker(broker)
        _apply_live_sizer(cerebro, sizer_type, sizer_config)

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

                since_ms = _calculate_ohlcv_since_ms(timeframe, limit=100)

                logger.info(f"Fetching OHLCV for {symbol} timeframe={timeframe}")

                bars = store.fetch_ohlcv(
                    symbol=symbol,
                    interval=timeframe,
                    limit=100,
                    since_ms=since_ms,
                )

                logger.info(f"Fetched {len(bars) if bars else 0} bars")

                if not bars:
                    raise LiveTradingError(
                        f"Exchange API returned no OHLCV data for {symbol} [{timeframe}]."
                    )

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


def _apply_live_sizer(
    cerebro: bt.Cerebro,
    sizer_type: str = 'fixed_size',
    sizer_config: Optional[dict] = None,
) -> None:
    """Apply backtrader sizer configuration for live sessions."""
    config = SizerConfig.from_dict({
        'type': sizer_type,
        **(sizer_config or {}),
    })

    if config.type == SizerType.PERCENT_SIZER:
        cerebro.addsizer(bt.sizers.PercentSizer, percents=config.percents)
    elif config.type == SizerType.ALL_IN_SIZER:
        cerebro.addsizer(bt.sizers.AllInSizerInt)
    elif config.type == SizerType.RISK_SIZER:
        cerebro.addsizer(bt.sizers.PercentSizerInt, percents=config.risk_percent)
    elif config.type == SizerType.KELLY_SIZER:
        kelly_fraction = min(max(config.risk_percent / 100.0, 0.01), 1.0) * 100.0
        cerebro.addsizer(bt.sizers.PercentSizer, percents=kelly_fraction)
    else:
        cerebro.addsizer(bt.sizers.FixedSize, stake=config.stake)


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
    """Get session orders directly from the exchange API."""
    session = get_session_manager().get_session(session_id)
    if not session:
        raise LiveTradingError(f"Session {session_id} not found")

    if not session.store or not getattr(session.store, '_running', False):
        raise LiveTradingError("Exchange connection is not active")

    try:
        exchange_orders = session.store.get_all_orders(session.symbol, limit=100)
        session_start_ms = int(session.start_time.timestamp() * 1000) if session.start_time else None
        trade_map = {}
        try:
            exchange_trades = session.store.get_my_trades(session.symbol, limit=200)
            trade_map = _aggregate_exchange_trades(exchange_trades)
        except Exception as trade_error:
            logger.warning(
                "Failed to fetch exchange trade details for %s; continuing with raw order history: %s",
                session_id,
                trade_error,
            )
        normalized = []
        for order in exchange_orders:
            order_time = _safe_float(order.get('time') or order.get('transactTime'))
            normalized_order = _normalize_exchange_order(order, session_id)
            normalized_order['metadata']['in_session'] = (
                bool(session_start_ms and order_time and order_time >= session_start_ms)
                if session_start_ms else None
            )
            trade_data = trade_map.get(str(normalized_order.get('exchange_order_id') or normalized_order.get('order_id')))
            if trade_data:
                normalized_order.update({
                    'filled_size': trade_data.get('filled_size', normalized_order['filled_size']),
                    'filled_price': trade_data.get('filled_price') or normalized_order['filled_price'],
                    'executed_quote_qty': trade_data.get('executed_quote_qty'),
                    'fee': trade_data.get('fee'),
                    'fee_asset': trade_data.get('fee_asset'),
                    'trade_count': trade_data.get('trade_count', 0),
                    'last_fill_at': trade_data.get('last_fill_at'),
                })
            normalized.append(normalized_order)
        return sorted(
            normalized,
            key=lambda item: item.get('last_fill_at') or item.get('created_at') or '',
            reverse=True,
        )
    except Exception as e:
        logger.warning(f"Failed to fetch exchange-backed orders for {session_id}: {e}")
        raise LiveTradingError(f"Failed to fetch orders from exchange: {e}") from e


def get_session_positions(session_id: str) -> List[Dict]:
    """Get current session symbol position from exchange account balances."""
    session = get_session_manager().get_session(session_id)
    if not session:
        raise LiveTradingError(f"Session {session_id} not found")

    if not session.store or not getattr(session.store, '_running', False):
        raise LiveTradingError("Exchange connection is not active")

    try:
        base_asset, _quote_asset = _extract_symbol_assets(session.symbol)
        account = session.store.get_account()
        balances = account.get('balances')
        if not isinstance(balances, list):
            raise LiveTradingError("Exchange account response did not include balances.")

        balance = next(
            (item for item in balances if str(item.get('asset') or '').upper() == base_asset),
            None,
        )
        if not balance:
            return []

        free_amount = _safe_float(balance.get('free')) or 0.0
        locked_amount = _safe_float(balance.get('locked')) or 0.0
        size = free_amount + locked_amount
        if size <= 0:
            return []

        ticker = session.store.fetch_ticker(session.symbol)
        current_price = _safe_float(ticker.get('last'))

        return [{
            'symbol': session.symbol,
            'side': 'long',
            'size': size,
            'avg_price': None,
            'current_price': current_price,
            'pnl': None,
            'pnl_percent': None,
            'free_size': free_amount,
            'locked_size': locked_amount,
            'source': 'exchange_balance',
        }]
    except LiveTradingError:
        raise
    except Exception as e:
        raise LiveTradingError(f"Failed to fetch positions from exchange: {e}") from e


def get_session_account_snapshot(session_id: str) -> Dict:
    """Get exchange-backed cash and portfolio value snapshot for the session symbol."""
    session = get_session_manager().get_session(session_id)
    if not session:
        raise LiveTradingError(f"Session {session_id} not found")

    if not session.store or not getattr(session.store, '_running', False):
        raise LiveTradingError("Exchange connection is not active")

    try:
        account = session.store.get_account()
        balance_snapshot = _extract_balance_components(account, session.symbol)
        base_free = balance_snapshot['base_free']
        base_locked = balance_snapshot['base_locked']
        quote_free = balance_snapshot['quote_free']
        quote_locked = balance_snapshot['quote_locked']
        base_size = balance_snapshot['base_size']

        ticker = session.store.fetch_ticker(session.symbol)
        current_price = _safe_float(ticker.get('last')) or 0.0

        base_value = base_size * current_price
        portfolio_value = quote_free + quote_locked + base_value
        baseline_portfolio_value = _safe_float(
            getattr(session, 'baseline_portfolio_value', None)
        )
        if baseline_portfolio_value is None or baseline_portfolio_value <= 0:
            baseline_portfolio_value = float(session.initial_cash)
        current_pnl = portfolio_value - baseline_portfolio_value
        session_result = _build_session_result(current_pnl, baseline_portfolio_value)

        return {
            'session_id': session_id,
            'symbol': session.symbol,
            'cash': quote_free,
            'cash_locked': quote_locked,
            'base_size': base_size,
            'base_value': base_value,
            'current_price': current_price,
            'baseline_portfolio_value': baseline_portfolio_value,
            'portfolio_value': portfolio_value,
            'current_pnl': current_pnl,
            'total_pnl_percent': session_result['percent'],
            'session_result': session_result,
        }
    except LiveTradingError:
        raise
    except Exception as e:
        raise LiveTradingError(f"Failed to fetch account snapshot: {e}") from e


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

    if session.store and order_id.isdigit():
        session.store.cancel_order(session.symbol, int(order_id))
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


def get_session_order_book(session_id: str, limit: int = 10) -> Dict:
    """Get the current order book depth for the session symbol."""
    session = get_session_manager().get_session(session_id)
    if not session:
        raise LiveTradingError(f"Session {session_id} not found")

    if not session.store or not session.store._running:
        raise LiveTradingError("Exchange connection is not active")

    safe_limit = max(1, min(int(limit or 10), 20))

    try:
        order_book = session.store.get_order_book(session.symbol, limit=safe_limit)
        bids = [
            {
                'price': _safe_float(level[0]) or 0.0,
                'size': _safe_float(level[1]) or 0.0,
                'total': (_safe_float(level[0]) or 0.0) * (_safe_float(level[1]) or 0.0),
            }
            for level in order_book.get('bids', [])[:safe_limit]
        ]
        asks = [
            {
                'price': _safe_float(level[0]) or 0.0,
                'size': _safe_float(level[1]) or 0.0,
                'total': (_safe_float(level[0]) or 0.0) * (_safe_float(level[1]) or 0.0),
            }
            for level in order_book.get('asks', [])[:safe_limit]
        ]
        best_bid = bids[0]['price'] if bids else None
        best_ask = asks[0]['price'] if asks else None
        spread = (best_ask - best_bid) if best_bid is not None and best_ask is not None else None

        return {
            'session_id': session_id,
            'symbol': session.symbol,
            'limit': safe_limit,
            'bids': bids,
            'asks': asks,
            'best_bid': best_bid,
            'best_ask': best_ask,
            'spread': spread,
            'timestamp': datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise LiveTradingError(f"Failed to fetch order book: {e}") from e


def get_ohlcv(session_id: str, limit: int = 100) -> Dict:
    """Fetch historical OHLCV bars via REST (fallback for WebSocket)."""
    session = get_session_manager().get_session(session_id)
    if not session:
        raise LiveTradingError(f"Session {session_id} not found")

    if not session.store or not session.store._running:
        raise LiveTradingError("Exchange connection is not active")

    try:
        since_ms = _calculate_ohlcv_since_ms(session.timeframe, limit=limit)
        bars = session.store.fetch_ohlcv(
            symbol=session.symbol,
            interval=session.timeframe,
            limit=limit,
            since_ms=since_ms,
        )
        if not bars:
            raise LiveTradingError(
                f"Exchange API returned no OHLCV data for {session.symbol} [{session.timeframe}]."
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


def get_trade_errors(session_id: str, limit: int = 20) -> Dict:
    """Get recent trading errors for a session."""
    session = get_session_manager().get_session(session_id)
    if not session:
        raise LiveTradingError(f"Session {session_id} not found")

    errors = getattr(session, '_trade_errors', [])
    return {'session_id': session_id, 'errors': errors[-limit:]}


def get_symbol_trading_rules(symbol: str, mode: str = 'paper', user_id: Optional[str] = None) -> Dict:
    """Fetch exchange trading rules for a symbol."""
    exchange = 'binance'
    broker_config = load_broker_config()
    ex_config = get_exchange_config(exchange, broker_config)
    credentials = _get_exchange_credentials(exchange, mode, user_id)
    store: Optional[BinanceStore] = None

    try:
        store = BinanceStore(
            api_key=credentials['api_key'],
            api_secret=credentials['api_secret'],
            mode=mode,
            exchange_id=ex_config.ccxt_id,
            config={'default_market': 'spot', 'markets': ['spot']},
            user_id=user_id,
        )
        store.start()
        return store.get_symbol_trading_rules(symbol)
    except Exception as e:
        raise LiveTradingError(f"Failed to fetch symbol trading rules: {e}") from e
    finally:
        if store:
            store.stop()


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
        _update_order_status(session_id, data['order_id'], 'filled', data)

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
        _update_order_status(session_id, data['order_id'], 'cancelled', data)

    elif event_type == BrokerEvent.ORDER_REJECTED:
        error_code = _classify_trading_error(data.get('reason'))
        session = session_manager.get_session(session_id)
        if session:
            trade_errors = getattr(session, '_trade_errors', [])
            trade_errors.append({
                'timestamp': datetime.now().isoformat(),
                'message': data.get('reason', 'unknown'),
                'code': error_code,
            })
            session._trade_errors = trade_errors[-20:]
        _run_ws(ws.broadcast_order_update(
            session_id=session_id,
            order_id=data['order_id'],
            symbol=data.get('symbol', ''),
            side=data.get('side', ''),
            size=data.get('size', 0),
            price=data.get('price') or 0,
            status='rejected',
        ))
        _run_ws(ws.broadcast_error(
            session_id=session_id,
            error_message=f"Order rejected: {data.get('reason', 'unknown')}",
            error_code=error_code,
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
            'metadata': {
                'client_order_id': str(data['order_id']),
            },
        })
    except Exception as e:
        logger.warning(f"Failed to persist order: {e}")


def _update_order_status(session_id: str, order_id: str, status: str, data: dict) -> None:
    """Update an existing order's status in DB."""
    try:
        storage = _get_storage()
        with storage.managed_session() as db:
            from src.db.models import OrderModel, OrderStatusEnum
            order = db.query(OrderModel).filter(
                OrderModel.order_id == build_session_order_pk(session_id, order_id)
            ).first()
            if order:
                order.status = OrderStatusEnum[status.upper()]
                if status == 'filled':
                    order.filled_size = data.get('size', 0)
                    order.filled_price = data.get('price', 0)
                    order.commission = data.get('commission', 0)
                    order.cost = data.get('cost', 0)
                    order.filled_at = datetime.utcnow()
                order.updated_at = datetime.utcnow()
    except Exception as e:
        logger.warning(f"Failed to update order status: {e}")
