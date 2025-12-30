import logging
import threading
import uuid
import warnings
from datetime import datetime
from typing import Callable, Dict, Optional

import backtrader as bt

from src.brokers.ccxt_adapter import CCXTBroker, CCXTData, CCXTStore
from src.brokers.ibkr_adapter import IBKRStore
from src.config.worker_config import get_config as get_worker_config
from src.db import SessionStorage
from src.service.backtest_engine import TradeRecorder, load_user_strategy
from src.service.session_manager import SessionStatus, get_session_manager
from src.utils.config_loader import get_exchange_config, load_broker_config

logger = logging.getLogger(__name__)


# Session storage (lazy-initialized to avoid import-time database access)
_session_storage = None


def _get_session_storage():
    """Get or create session storage instance (lazy initialization)."""
    global _session_storage
    if _session_storage is None:
        from src.config.settings import ensure_database_dir
        ensure_database_dir()  # Ensure database directory exists before creating storage
        _session_storage = SessionStorage()
    return _session_storage


class LiveTradingError(Exception):
    """Raised when live trading encounters an error."""


# SafeReturns is now available from src.service.analyzer_config


def _build_components(
    exchange: str,
    mode: str,
    symbol: str,
    timeframe: str,
    initial_cash: float,
    commission: float,
    session_id: Optional[str],
    config,
    user_id: Optional[str] = None,
):
    """
    Create store/broker/data based on exchange adapter (ccxt/ibkr).

    Args:
        user_id: User identifier for loading user-specific credentials from database
    """
    ex_config = get_exchange_config(exchange, config)
    adapter = ex_config.adapter.lower()

    if adapter == 'ccxt':
        store = CCXTStore(
            exchange_id=ex_config.ccxt_id,
            mode=mode,
            config={
                'default_market': ex_config.default_market,
                'markets': ex_config.markets,
            },
            user_id=user_id,  # Pass user_id for database credential lookup
        )
        store.start()
        broker = CCXTBroker(
            store=store,
            cash=initial_cash,
            commission=commission,
            session_id=session_id
        )
        data_feed = CCXTData(
            store=store,
            symbol=symbol,
            timeframe=timeframe
        )
        logger.info("Initialized CCXT components for %s (%s)", symbol, exchange)
    elif adapter == 'ibkr':
        store = IBKRStore(mode=mode)
        store.start()
        broker = store.get_broker(initial_cash=initial_cash, commission=commission)
        data_feed = store.get_data(symbol=symbol, timeframe=timeframe)
        logger.info("Initialized IBKR components for %s", symbol)
    else:
        raise LiveTradingError(f"Unsupported adapter '{adapter}' for exchange '{exchange}'")

    return store, broker, data_feed, adapter


def run_live(
    strategy_name: str,
    symbol: str,
    exchange: str = 'binance',
    mode: str = 'paper',
    timeframe: str = '1m',
    initial_cash: float = 10000.0,
    commission: float = 0.001,
    session_id: Optional[str] = None,
    config: Optional[Dict] = None,
    user_id: Optional[str] = None,
    use_worker: Optional[bool] = None,
    event_callback: Optional[Callable] = None,
) -> Dict:
    """
    Start live trading session with worker isolation.

    When worker pool is enabled (default), strategy code executes in an
    isolated worker process for security. The API process never executes
    user strategy code.

    Args:
        strategy_name: Name of strategy file (without .py)
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        exchange: CCXT exchange ID ('binance', 'okx', 'bybit')
        mode: Trading mode ('paper' for testnet, 'live' for production)
        timeframe: Bar timeframe ('1m', '5m', '15m', '1h', etc.)
        initial_cash: Starting cash for paper trading
        commission: Commission rate (e.g., 0.001 = 0.1%)
        session_id: Optional session ID (auto-generated if None)
        config: Optional broker configuration dict
        user_id: Optional user identifier for loading user-specific credentials
        use_worker: Force worker pool on/off (None = use config)
        event_callback: Optional callback for receiving live trading events

    Returns:
        dict: Session information

    Raises:
        LiveTradingError: If initialization fails
    """
    # Generate session ID
    if not session_id:
        session_id = str(uuid.uuid4())

    logger.info(
        f"Starting live trading session {session_id}: "
        f"{strategy_name} on {symbol} ({exchange} {mode})"
    )

    # Determine whether to use worker pool
    worker_config = get_worker_config()
    should_use_worker = use_worker if use_worker is not None else worker_config.enabled

    if should_use_worker:
        return _run_live_worker(
            strategy_name=strategy_name,
            symbol=symbol,
            exchange=exchange,
            mode=mode,
            timeframe=timeframe,
            initial_cash=initial_cash,
            commission=commission,
            session_id=session_id,
            config=config,
            user_id=user_id,
            event_callback=event_callback,
        )
    else:
        # Legacy in-process execution (not secure for untrusted code!)
        logger.warning(
            "Running live trading in-process (worker pool disabled). "
            "This is NOT secure for untrusted strategy code!"
        )
        return _run_live_legacy(
            strategy_name=strategy_name,
            symbol=symbol,
            exchange=exchange,
            mode=mode,
            timeframe=timeframe,
            initial_cash=initial_cash,
            commission=commission,
            session_id=session_id,
            config=config,
            user_id=user_id,
        )


def _run_live_worker(
    strategy_name: str,
    symbol: str,
    exchange: str,
    mode: str,
    timeframe: str,
    initial_cash: float,
    commission: float,
    session_id: str,
    config: Optional[Dict],
    user_id: Optional[str],
    event_callback: Optional[Callable] = None,
) -> Dict:
    """
    Run live trading in isolated worker process (secure).

    The API process NEVER executes user strategy code - all execution
    happens in the worker process.
    """
    from src.service.worker.task_models import LiveTradingTask
    from src.service.worker.worker_pool import get_worker_pool, WorkerPoolError

    # Load broker config if not provided
    if config is None:
        config = load_broker_config()

    # Create task
    task = LiveTradingTask(
        task_id=str(uuid.uuid4()),
        session_id=session_id,
        strategy_name=strategy_name,
        symbol=symbol,
        exchange=exchange,
        mode=mode,
        timeframe=timeframe,
        initial_cash=initial_cash,
        commission=commission,
        user_id=user_id,
        broker_config=config,
    )

    # Start session in worker pool
    pool = get_worker_pool()

    # Setup event forwarding to session manager
    session_manager = get_session_manager()

    # Create session entry in manager
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

    def handle_worker_event(event):
        """Forward worker events to session manager and callback."""
        from src.service.worker.task_models import LiveEventType

        event_type = event.event_type
        data = event.data or {}

        if event_type == LiveEventType.STATUS_UPDATE:
            status_str = data.get("status", "")
            if status_str == "running":
                session_manager.update_session(session_id, status=SessionStatus.RUNNING)
            elif status_str == "error":
                session_manager.update_session(
                    session_id,
                    status=SessionStatus.ERROR,
                    error_message=data.get("error", "Unknown error")
                )
        elif event_type == LiveEventType.PNL_UPDATE:
            session.current_pnl = data.get("pnl", 0.0)
        elif event_type == LiveEventType.STOPPED:
            session_manager.update_session(
                session_id,
                status=SessionStatus.STOPPED,
                end_time=datetime.now()
            )
        elif event_type == LiveEventType.ERROR:
            session_manager.update_session(
                session_id,
                status=SessionStatus.ERROR,
                error_message=data.get("error", "Unknown error")
            )

        # Forward to user callback if provided
        if event_callback:
            try:
                event_callback(event)
            except Exception as e:
                logger.warning(f"Event callback error: {e}")

    try:
        pool.start_live_session(task, event_callback=handle_worker_event)
    except WorkerPoolError as e:
        session_manager.remove_session(session_id)
        raise LiveTradingError(f"Failed to start worker session: {e}") from e

    # Save session to database
    _get_session_storage().save_session(session)

    logger.info(f"Session {session_id} started in worker pool")
    return session.to_dict()


def _run_live_legacy(
    strategy_name: str,
    symbol: str,
    exchange: str,
    mode: str,
    timeframe: str,
    initial_cash: float,
    commission: float,
    session_id: str,
    config: Optional[Dict],
    user_id: Optional[str],
) -> Dict:
    """
    Legacy in-process live trading execution.

    WARNING: This executes user strategy code in the API process!
    Only use when worker pool is explicitly disabled.
    """
    session_manager = get_session_manager()
    store = None

    try:
        # 1. Create session in manager
        session = session_manager.create_session(
            session_id=session_id,
            strategy_name=strategy_name,
            symbol=symbol,
            exchange=exchange,
            mode=mode,
            timeframe=timeframe,
            initial_cash=initial_cash,
            commission=commission,
            user_id=user_id
        )

        # 2. Load strategy class (executes user code - NOT SECURE!)
        strategy_cls = load_user_strategy(strategy_name)
        logger.info(f"Loaded strategy: {strategy_name}")

        # 3. Load broker config if not provided
        if config is None:
            config = load_broker_config()

        # 4. Initialize components based on adapter
        store, broker, data_feed, adapter = _build_components(
            exchange=exchange,
            mode=mode,
            symbol=symbol,
            timeframe=timeframe,
            initial_cash=initial_cash,
            commission=commission,
            session_id=session_id,
            config=config,
            user_id=user_id
        )
        logger.info("Adapter '%s' initialized for exchange %s", adapter, exchange)

        # 5. Initialize Cerebro
        cerebro = bt.Cerebro()
        cerebro.addstrategy(strategy_cls)
        cerebro.adddata(data_feed)
        cerebro.setbroker(broker)

        # 6. Add analyzers using centralized configuration
        from src.service.analyzer_config import configure_analyzers, AnalyzerMode
        configure_analyzers(cerebro, AnalyzerMode.LIVE, TradeRecorder)
        logger.info("Added analyzers to Cerebro")

        # 7. Store runtime objects in session
        session.cerebro = cerebro
        session.store = store

        # 8. Save session to database
        _get_session_storage().save_session(session)

        # 9. Run Cerebro in background thread
        def run_cerebro():
            """Background thread function that runs Cerebro."""
            try:
                session.status = SessionStatus.RUNNING
                session_manager.update_session(session_id, status=SessionStatus.RUNNING)
                _get_session_storage().save_session(session)

                logger.info(f"Cerebro started for session {session_id}")
                cerebro.run()

                session.status = SessionStatus.STOPPED
                session.end_time = datetime.now()
                session_manager.update_session(
                    session_id,
                    status=SessionStatus.STOPPED,
                    end_time=session.end_time
                )
                _get_session_storage().save_session(session)

                logger.info(f"Cerebro stopped normally for session {session_id}")

            except Exception as e:
                session.status = SessionStatus.ERROR
                session.error_message = str(e)
                session.end_time = datetime.now()

                session_manager.update_session(
                    session_id,
                    status=SessionStatus.ERROR,
                    error_message=str(e),
                    end_time=session.end_time
                )
                _get_session_storage().save_session(session)

                logger.exception(f"Error in session {session_id}: {e}")

            finally:
                if store:
                    store.stop()

        thread = threading.Thread(
            target=run_cerebro,
            daemon=True,
            name=f"LiveTrading-{session_id[:8]}"
        )
        thread.start()
        session.thread = thread

        logger.info(f"Session {session_id} started successfully")
        return session.to_dict()

    except Exception as e:
        session_manager.remove_session(session_id)
        logger.exception(f"Failed to start live trading session: {e}")
        raise LiveTradingError(f"Failed to start session: {e}") from e


def stop_live(session_id: str, use_worker: Optional[bool] = None) -> Dict:
    """
    Stop live trading session gracefully.

    Args:
        session_id: Session ID to stop
        use_worker: Force worker pool on/off (None = use config)

    Returns:
        dict: Session stop information

    Raises:
        LiveTradingError: If session not found or cannot be stopped
    """
    logger.info(f"Stopping session {session_id}")

    # Check if using worker pool
    worker_config = get_worker_config()
    should_use_worker = use_worker if use_worker is not None else worker_config.enabled

    if should_use_worker:
        from src.service.worker.worker_pool import get_worker_pool
        pool = get_worker_pool()
        
        # Check if session exists in worker pool
        if session_id in pool.get_live_session_ids():
            success = pool.stop_live_session(session_id)
            if not success:
                raise LiveTradingError(f"Failed to stop worker session {session_id}")
            
            # Update session manager
            session_manager = get_session_manager()
            session = session_manager.get_session(session_id)
            if session:
                session_manager.update_session(
                    session_id,
                    status=SessionStatus.STOPPED,
                    end_time=datetime.now()
                )
                _get_session_storage().save_session(session)
            
            return {
                'session_id': session_id,
                'status': SessionStatus.STOPPED.value,
                'end_time': datetime.now().isoformat()
            }

    # Legacy session manager stop
    session_manager = get_session_manager()

    session = session_manager.get_session(session_id)
    if not session:
        raise LiveTradingError(f"Session {session_id} not found")

    success = session_manager.stop_session(session_id, timeout=10.0)

    if not success:
        raise LiveTradingError(f"Failed to stop session {session_id}")

    _get_session_storage().save_session(session)

    return {
        'session_id': session_id,
        'status': session.status.value,
        'final_pnl': session.current_pnl,
        'end_time': session.end_time.isoformat() if session.end_time else None
    }


def get_session_status(session_id: str) -> Dict:
    """
    Get status of live trading session.

    Args:
        session_id: Session ID

    Returns:
        dict: Session status information

    Raises:
        LiveTradingError: If session not found
    """
    logger.info(f"Getting status for session {session_id}")

    session_manager = get_session_manager()

    session = session_manager.get_session(session_id)
    if not session:
        raise LiveTradingError(f"Session {session_id} not found")

    return session.to_dict()
