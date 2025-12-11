"""
Live Trading Engine - Orchestrates live/paper trading with CCXT.

This module provides the main entry point for live trading, similar to
backtest_engine.py but using real-time data feeds and CCXT broker.
"""

import logging
import threading
import uuid
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import backtrader as bt

from src.brokers.ccxt_adapter import CCXTBroker, CCXTData, CCXTStore
from src.db.session_storage import SessionStorage
from src.service.backtest_engine import TradeRecorder, load_user_strategy
from src.service.session_manager import SessionStatus, get_session_manager
from src.utils.config_loader import load_broker_config

logger = logging.getLogger(__name__)

# Suppress noisy protobuf warnings
warnings.filterwarnings(
    "once",
    message=r"Protobuf gencode version .*runtime version .*",
    category=UserWarning,
    module=r"google\.protobuf\.runtime_version"
)

# Initialize session storage
_session_storage = SessionStorage()


class LiveTradingError(Exception):
    """Raised when live trading encounters an error."""


class SafeReturns(bt.analyzers.Returns):
    """Returns analyzer that tolerates zero bars (avoids ZeroDivisionError)."""

    def stop(self):
        try:
            super().stop()
        except ZeroDivisionError:
            # No periods processed; provide neutral values instead of crashing
            logger.warning("Returns analyzer saw no bars; emitting neutral return metrics")
            self.rets['rtot'] = 0.0
            self.rets['ravg'] = 0.0
            self.rets['rnorm'] = 0.0
            self.rets['rnorm100'] = 0.0


def run_live(
    strategy_name: str,
    symbol: str,
    exchange: str = 'binance',
    mode: str = 'paper',
    timeframe: str = '1m',
    initial_cash: float = 10000.0,
    commission: float = 0.001,
    session_id: Optional[str] = None,
    config: Optional[Dict] = None
) -> Dict:
    """
    Start live trading session with SessionManager integration.

    This function orchestrates a live trading session similar to run_backtest(),
    but uses real-time data feeds and CCXT broker for order execution.

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

    # Get session manager
    session_manager = get_session_manager()

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
            commission=commission
        )

        # 2. Load strategy class
        strategy_cls = load_user_strategy(strategy_name)
        logger.info(f"Loaded strategy: {strategy_name}")

        # 3. Load broker config if not provided
        if config is None:
            config = load_broker_config()

        # 4. Initialize CCXT components
        store = CCXTStore(exchange_id=exchange, mode=mode)
        store.start()
        logger.info(f"CCXT store started for {exchange}")

        broker = CCXTBroker(
            store=store,
            cash=initial_cash,
            commission=commission,
            session_id=session_id  # Pass session_id for WebSocket broadcasting
        )
        logger.info(f"CCXT broker initialized with ${initial_cash}")

        data_feed = CCXTData(
            store=store,
            symbol=symbol,
            timeframe=timeframe
        )
        logger.info(f"CCXT data feed initialized for {symbol} ({timeframe})")

        # 5. Initialize Cerebro
        cerebro = bt.Cerebro()
        cerebro.addstrategy(strategy_cls)
        cerebro.adddata(data_feed)
        cerebro.setbroker(broker)

        # 6. Add analyzers
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(SafeReturns, _name='returns')
        cerebro.addanalyzer(TradeRecorder, _name='trade_recorder')
        logger.info("Added analyzers to Cerebro")

        # 7. Store runtime objects in session
        session.cerebro = cerebro
        session.store = store

        # 8. Save session to database
        _session_storage.save_session(session)

        # 9. Run Cerebro in background thread
        def run_cerebro():
            """Background thread function that runs Cerebro."""
            try:
                # Update status
                session.status = SessionStatus.RUNNING
                session_manager.update_session(session_id, status=SessionStatus.RUNNING)
                _session_storage.save_session(session)

                logger.info(f"Cerebro started for session {session_id}")

                # Run cerebro (this will loop until stopped)
                results = cerebro.run()

                # Update status on successful completion
                session.status = SessionStatus.STOPPED
                session.end_time = datetime.now()
                session_manager.update_session(
                    session_id,
                    status=SessionStatus.STOPPED,
                    end_time=session.end_time
                )
                _session_storage.save_session(session)

                logger.info(f"Cerebro stopped normally for session {session_id}")

            except Exception as e:
                # Update status on error
                session.status = SessionStatus.ERROR
                session.error_message = str(e)
                session.end_time = datetime.now()

                session_manager.update_session(
                    session_id,
                    status=SessionStatus.ERROR,
                    error_message=str(e),
                    end_time=session.end_time
                )
                _session_storage.save_session(session)

                logger.exception(f"Error in session {session_id}: {e}")

            finally:
                # Clean up store
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

        # Return session info
        return session.to_dict()

    except Exception as e:
        # Clean up on error
        session_manager.remove_session(session_id)
        logger.exception(f"Failed to start live trading session: {e}")
        raise LiveTradingError(f"Failed to start session: {e}") from e


def stop_live(session_id: str) -> Dict:
    """
    Stop live trading session gracefully.

    Args:
        session_id: Session ID to stop

    Returns:
        dict: Session stop information

    Raises:
        LiveTradingError: If session not found or cannot be stopped
    """
    logger.info(f"Stopping session {session_id}")

    session_manager = get_session_manager()

    # Get session
    session = session_manager.get_session(session_id)
    if not session:
        raise LiveTradingError(f"Session {session_id} not found")

    # Stop session
    success = session_manager.stop_session(session_id, timeout=10.0)

    if not success:
        raise LiveTradingError(f"Failed to stop session {session_id}")

    # Save final state
    _session_storage.save_session(session)

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
