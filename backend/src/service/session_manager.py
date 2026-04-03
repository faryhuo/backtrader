"""
Session Manager - Manage lifecycle of live trading sessions.

This module provides centralized management for multiple concurrent trading
sessions, including start, stop, status tracking, and persistence.
"""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import backtrader as bt

logger = logging.getLogger(__name__)


class SessionStatus(str, Enum):
    """Trading session status."""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class TradingSession:
    """
    Represents a single live trading session.

    A session encapsulates a running Backtrader Cerebro instance with
    CCXT broker and data feed, tracking its lifecycle and state.
    """
    session_id: str
    strategy_name: str
    symbol: str
    exchange: str
    mode: str  # 'paper' or 'live'
    timeframe: str
    initial_cash: float
    commission: float
    market: str = "spot"
    status: SessionStatus = SessionStatus.STARTING
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    # User and authentication
    user_id: Optional[str] = None  # Owner's user ID (from JWT 'sub' or None for anonymous)
    ws_token: str = field(default_factory=lambda: str(__import__('uuid').uuid4()))  # WebSocket auth token

    # Runtime objects (not serialized)
    cerebro: Optional[bt.Cerebro] = None
    store: Optional[Any] = None  # CCXTStore
    thread: Optional[threading.Thread] = None

    # Tracking
    current_pnl: float = 0.0
    total_trades: int = 0
    positions: List[Dict] = field(default_factory=list)
    orders: List[Dict] = field(default_factory=list)
    feed_status: str = "warming_up"
    error_message: Optional[str] = None
    baseline_quote_free: float = 0.0
    baseline_quote_locked: float = 0.0
    baseline_base_size: float = 0.0
    baseline_price: float = 0.0
    baseline_portfolio_value: float = 0.0

    def to_dict(self) -> Dict:
        """
        Convert session to dictionary for API responses.

        Returns:
            dict: Serializable session information
        """
        return {
            'session_id': self.session_id,
            'strategy_name': self.strategy_name,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'market': self.market,
            'mode': self.mode,
            'timeframe': self.timeframe,
            'initial_cash': self.initial_cash,
            'commission': self.commission,
            'status': self.status.value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'current_pnl': self.current_pnl,
            'total_trades': self.total_trades,
            'feed_status': self.feed_status,
            'positions': self.positions,
            'open_orders': [o for o in self.orders if o.get('status') not in ['filled', 'canceled']],
            'error_message': self.error_message,
            'ws_token': self.ws_token,  # Token for WebSocket authentication
            'user_id': self.user_id
        }

    def is_active(self) -> bool:
        """Check if session is currently active (running or starting)."""
        return self.status in (SessionStatus.STARTING, SessionStatus.RUNNING)

    def is_stopped(self) -> bool:
        """Check if session has stopped."""
        return self.status in (SessionStatus.STOPPED, SessionStatus.ERROR)


class SessionManager:
    """
    Manages multiple concurrent trading sessions.

    This class provides:
    - Session creation and registration
    - Session lifecycle management (start, stop, status)
    - Thread-safe access to session data
    - Session persistence coordination

    Usage:
        manager = SessionManager()
        session = manager.create_session(...)
        manager.start_session(session)
        status = manager.get_session_status(session_id)
        manager.stop_session(session_id)
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern - ensure only one SessionManager exists."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize session manager."""
        if not hasattr(self, '_initialized'):
            self._sessions: Dict[str, TradingSession] = {}
            self._sessions_lock = threading.RLock()
            self._initialized = True
            logger.info("SessionManager initialized")

    def create_session(
        self,
        session_id: str,
        strategy_name: str,
        symbol: str,
        exchange: str = 'binance',
        market: str = 'spot',
        mode: str = 'paper',
        timeframe: str = '1m',
        initial_cash: float = 10000.0,
        commission: float = 0.001,
        user_id: Optional[str] = None
    ) -> TradingSession:
        """
        Create a new trading session.

        Args:
            session_id: Unique session identifier
            strategy_name: Strategy to run
            symbol: Trading pair (e.g., 'BTC/USDT')
            exchange: Exchange ID
            mode: 'paper' or 'live'
            timeframe: Bar timeframe
            initial_cash: Starting capital
            commission: Commission rate
            user_id: Optional user identifier (from JWT 'sub' claim)

        Returns:
            TradingSession: Created session object

        Raises:
            ValueError: If session ID already exists
        """
        with self._sessions_lock:
            if session_id in self._sessions:
                raise ValueError(f"Session {session_id} already exists")

            session = TradingSession(
                session_id=session_id,
                strategy_name=strategy_name,
                symbol=symbol,
                exchange=exchange,
                market=market,
                mode=mode,
                timeframe=timeframe,
                initial_cash=initial_cash,
                commission=commission,
                status=SessionStatus.STARTING,
                start_time=datetime.now(),
                user_id=user_id
            )

            self._sessions[session_id] = session
            logger.info(
                f"Created session {session_id}: {strategy_name} on {symbol} "
                f"({exchange} {mode}) [user={user_id}]"
            )

            return session

    def register_session(self, session: TradingSession) -> None:
        """
        Register an existing session.

        Args:
            session: Session to register

        Raises:
            ValueError: If session ID already exists
        """
        with self._sessions_lock:
            if session.session_id in self._sessions:
                raise ValueError(f"Session {session.session_id} already exists")

            self._sessions[session.session_id] = session
            logger.info(f"Registered session {session.session_id}")

    def get_session(self, session_id: str) -> Optional[TradingSession]:
        """
        Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            TradingSession if found, None otherwise
        """
        with self._sessions_lock:
            return self._sessions.get(session_id)

    def update_session(self, session_id: str, **kwargs) -> None:
        """
        Update session attributes.

        Args:
            session_id: Session to update
            **kwargs: Attributes to update
        """
        with self._sessions_lock:
            session = self._sessions.get(session_id)
            if not session:
                logger.warning(f"Cannot update non-existent session {session_id}")
                return

            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)

            logger.debug(f"Updated session {session_id}: {kwargs}")

    def stop_session(self, session_id: str, timeout: float = 10.0) -> bool:
        """
        Stop a running session.

        Args:
            session_id: Session to stop
            timeout: Maximum time to wait for graceful shutdown (seconds)

        Returns:
            bool: True if stopped successfully, False otherwise
        """
        with self._sessions_lock:
            session = self._sessions.get(session_id)
            if not session:
                logger.warning(f"Cannot stop non-existent session {session_id}")
                return False

            if session.is_stopped():
                logger.info(f"Session {session_id} already stopped")
                return True

            logger.info(f"Stopping session {session_id}...")
            session.status = SessionStatus.STOPPING

        try:
            # Stop CCXT store
            if session.store:
                session.store.stop()
                logger.debug(f"CCXT store stopped for session {session_id}")

            # Wait for thread to finish
            if session.thread and session.thread.is_alive():
                session.thread.join(timeout=timeout)

                if session.thread.is_alive():
                    logger.warning(
                        f"Session {session_id} thread did not stop within {timeout}s"
                    )
                    return False

            # Update status
            with self._sessions_lock:
                session.status = SessionStatus.STOPPED
                session.end_time = datetime.now()

            logger.info(f"Session {session_id} stopped successfully")
            return True

        except Exception as e:
            logger.exception(f"Error stopping session {session_id}: {e}")
            with self._sessions_lock:
                session.status = SessionStatus.ERROR
                session.error_message = str(e)
            return False

    def list_sessions(
        self,
        status_filter: Optional[SessionStatus] = None,
        active_only: bool = False
    ) -> List[TradingSession]:
        """
        List all sessions, optionally filtered.

        Args:
            status_filter: Filter by status
            active_only: Only return active sessions

        Returns:
            List of sessions
        """
        with self._sessions_lock:
            sessions = list(self._sessions.values())

            if active_only:
                sessions = [s for s in sessions if s.is_active()]
            elif status_filter:
                sessions = [s for s in sessions if s.status == status_filter]

            return sessions

    def get_active_session_count(self) -> int:
        """Get count of active sessions."""
        with self._sessions_lock:
            return sum(1 for s in self._sessions.values() if s.is_active())

    def remove_session(self, session_id: str) -> bool:
        """
        Remove session from manager.

        Note: This does not stop the session, only removes it from tracking.
        Call stop_session() first if session is running.

        Args:
            session_id: Session to remove

        Returns:
            bool: True if removed, False if not found
        """
        with self._sessions_lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]

                if session.is_active():
                    logger.warning(
                        f"Removing active session {session_id}. "
                        "Call stop_session() first for clean shutdown."
                    )

                del self._sessions[session_id]
                logger.info(f"Removed session {session_id}")
                return True

            return False

    def stop_all_sessions(self, timeout: float = 10.0) -> Dict[str, bool]:
        """
        Stop all active sessions.

        Args:
            timeout: Timeout per session

        Returns:
            dict: {session_id: success} for each stopped session
        """
        with self._sessions_lock:
            active_sessions = [
                s.session_id for s in self._sessions.values() if s.is_active()
            ]

        results = {}
        for session_id in active_sessions:
            results[session_id] = self.stop_session(session_id, timeout)

        logger.info(
            f"Stopped {sum(results.values())}/{len(results)} sessions"
        )

        return results

    def get_session_count(self) -> Dict[str, int]:
        """
        Get count of sessions by status.

        Returns:
            dict: {status: count}
        """
        with self._sessions_lock:
            counts = {}
            for session in self._sessions.values():
                status = session.status.value
                counts[status] = counts.get(status, 0) + 1

            counts['total'] = len(self._sessions)
            counts['active'] = sum(
                1 for s in self._sessions.values() if s.is_active()
            )

            return counts


# Global session manager instance
_session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """
    Get the global SessionManager instance.

    Returns:
        SessionManager: Global session manager
    """
    return _session_manager
