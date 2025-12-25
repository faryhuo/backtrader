import threading
import time

import pytest

from src.service.session_manager import SessionManager, SessionStatus


class StubStore:
    def __init__(self):
        self.stopped = False

    def stop(self):
        self.stopped = True


def test_create_session_duplicate_raises():
    manager = SessionManager()
    manager._sessions.clear()

    manager.create_session("s1", "strat", "BTC/USDT")
    with pytest.raises(ValueError):
        manager.create_session("s1", "strat", "BTC/USDT")


def test_update_session_updates_existing_and_ignores_unknown():
    manager = SessionManager()
    manager._sessions.clear()

    manager.create_session("s1", "strat", "BTC/USDT")
    manager.update_session("s1", current_pnl=12.5, unknown_field=1)

    s = manager.get_session("s1")
    assert s.current_pnl == 12.5
    assert not hasattr(s, "unknown_field")


def test_stop_session_returns_false_for_missing_session():
    manager = SessionManager()
    manager._sessions.clear()
    assert manager.stop_session("missing") is False


def test_stop_session_success_sets_status_and_calls_store_stop():
    manager = SessionManager()
    manager._sessions.clear()
    s = manager.create_session("s1", "strat", "BTC/USDT")

    s.status = SessionStatus.RUNNING
    s.store = StubStore()
    s.thread = threading.Thread(target=lambda: None)

    assert manager.stop_session("s1") is True
    assert s.status == SessionStatus.STOPPED
    assert s.end_time is not None
    assert s.store.stopped is True


def test_stop_session_timeout_returns_false():
    manager = SessionManager()
    manager._sessions.clear()
    s = manager.create_session("s1", "strat", "BTC/USDT")
    s.status = SessionStatus.RUNNING

    def sleeper():
        time.sleep(0.2)

    s.thread = threading.Thread(target=sleeper)
    s.thread.start()

    assert manager.stop_session("s1", timeout=0.01) is False


def test_remove_session():
    manager = SessionManager()
    manager._sessions.clear()
    manager.create_session("s1", "strat", "BTC/USDT")

    assert manager.remove_session("s1") is True
    assert manager.get_session("s1") is None
    assert manager.remove_session("s1") is False


def test_session_to_dict():
    """Test TradingSession serialization to dict."""
    manager = SessionManager()
    manager._sessions.clear()

    session = manager.create_session("s1", "my_strategy", "BTC/USDT",
                                     exchange="binance", mode="paper",
                                     timeframe="1h", initial_cash=10000.0,
                                     commission=0.001, user_id="user_123")

    session_dict = session.to_dict()

    assert session_dict['session_id'] == "s1"
    assert session_dict['strategy_name'] == "my_strategy"
    assert session_dict['symbol'] == "BTC/USDT"
    assert session_dict['exchange'] == "binance"
    assert session_dict['mode'] == "paper"
    assert session_dict['timeframe'] == "1h"
    assert session_dict['initial_cash'] == 10000.0
    assert session_dict['commission'] == 0.001
    assert session_dict['status'] == SessionStatus.STARTING.value
    assert session_dict['user_id'] == "user_123"
    assert 'ws_token' in session_dict
    assert 'start_time' in session_dict


def test_session_is_active():
    """Test TradingSession.is_active() method."""
    manager = SessionManager()
    manager._sessions.clear()

    session = manager.create_session("s1", "strat", "BTC/USDT")

    # Initially starting
    session.status = SessionStatus.STARTING
    assert session.is_active() is True

    # Running
    session.status = SessionStatus.RUNNING
    assert session.is_active() is True

    # Stopping
    session.status = SessionStatus.STOPPING
    assert session.is_active() is False

    # Stopped
    session.status = SessionStatus.STOPPED
    assert session.is_active() is False

    # Error
    session.status = SessionStatus.ERROR
    assert session.is_active() is False


def test_session_is_stopped():
    """Test TradingSession.is_stopped() method."""
    manager = SessionManager()
    manager._sessions.clear()

    session = manager.create_session("s1", "strat", "BTC/USDT")

    # Starting
    session.status = SessionStatus.STARTING
    assert session.is_stopped() is False

    # Running
    session.status = SessionStatus.RUNNING
    assert session.is_stopped() is False

    # Stopping
    session.status = SessionStatus.STOPPING
    assert session.is_stopped() is False

    # Stopped
    session.status = SessionStatus.STOPPED
    assert session.is_stopped() is True

    # Error
    session.status = SessionStatus.ERROR
    assert session.is_stopped() is True


def test_list_sessions():
    """Test listing all sessions."""
    manager = SessionManager()
    manager._sessions.clear()

    # Create multiple sessions
    manager.create_session("s1", "strat1", "BTC/USDT", user_id="user1")
    manager.create_session("s2", "strat2", "ETH/USDT", user_id="user1")
    manager.create_session("s3", "strat3", "SOL/USDT", user_id="user2")

    all_sessions = manager.list_sessions()

    assert len(all_sessions) == 3
    # list_sessions returns TradingSession objects, not dicts
    session_ids = [s.session_id for s in all_sessions]
    assert "s1" in session_ids
    assert "s2" in session_ids
    assert "s3" in session_ids


def test_list_sessions_with_status_filter():
    """Test listing sessions filtered by status."""
    manager = SessionManager()
    manager._sessions.clear()

    s1 = manager.create_session("s1", "strat1", "BTC/USDT")
    s2 = manager.create_session("s2", "strat2", "ETH/USDT")
    s3 = manager.create_session("s3", "strat3", "SOL/USDT")

    s1.status = SessionStatus.RUNNING
    s2.status = SessionStatus.STOPPED
    s3.status = SessionStatus.RUNNING

    running_sessions = manager.list_sessions(status_filter=SessionStatus.RUNNING)

    assert len(running_sessions) == 2
    session_ids = [s.session_id for s in running_sessions]
    assert "s1" in session_ids
    assert "s3" in session_ids
    assert "s2" not in session_ids


def test_list_sessions_active_only():
    """Test getting only active sessions using active_only filter."""
    manager = SessionManager()
    manager._sessions.clear()

    s1 = manager.create_session("s1", "strat", "BTC/USDT")
    s2 = manager.create_session("s2", "strat", "ETH/USDT")
    s3 = manager.create_session("s3", "strat", "SOL/USDT")

    s1.status = SessionStatus.RUNNING
    s2.status = SessionStatus.STOPPED
    s3.status = SessionStatus.STARTING  # Also active

    active = manager.list_sessions(active_only=True)

    assert len(active) == 2
    session_ids = [s.session_id for s in active]
    assert "s1" in session_ids
    assert "s3" in session_ids
    assert "s2" not in session_ids


def test_session_status_enum_values():
    """Test SessionStatus enum has expected values."""
    assert SessionStatus.STARTING.value == "starting"
    assert SessionStatus.RUNNING.value == "running"
    assert SessionStatus.STOPPING.value == "stopping"
    assert SessionStatus.STOPPED.value == "stopped"
    assert SessionStatus.ERROR.value == "error"


def test_create_session_with_all_params():
    """Test creating session with all parameters."""
    manager = SessionManager()
    manager._sessions.clear()

    session = manager.create_session(
        session_id="test_session",
        strategy_name="advanced_strategy",
        symbol="BTC/USDT",
        exchange="binance",
        mode="live",
        timeframe="5m",
        initial_cash=50000.0,
        commission=0.0015,
        user_id="power_user"
    )

    assert session.session_id == "test_session"
    assert session.strategy_name == "advanced_strategy"
    assert session.symbol == "BTC/USDT"
    assert session.exchange == "binance"
    assert session.mode == "live"
    assert session.timeframe == "5m"
    assert session.initial_cash == 50000.0
    assert session.commission == 0.0015
    assert session.user_id == "power_user"
    assert session.status == SessionStatus.STARTING


def test_update_session_with_positions_and_orders():
    """Test updating session with positions and orders data."""
    manager = SessionManager()
    manager._sessions.clear()

    session = manager.create_session("s1", "strat", "BTC/USDT")

    positions = [
        {"symbol": "BTC/USDT", "size": 0.5, "price": 50000.0}
    ]
    orders = [
        {"id": "order1", "status": "open", "side": "buy", "size": 0.1}
    ]

    manager.update_session("s1",
                          current_pnl=1250.50,
                          total_trades=5,
                          positions=positions,
                          orders=orders)

    updated = manager.get_session("s1")
    assert updated.current_pnl == 1250.50
    assert updated.total_trades == 5
    assert len(updated.positions) == 1
    assert len(updated.orders) == 1


def test_session_dict_includes_only_open_orders():
    """Test that to_dict() filters orders to only include open ones."""
    manager = SessionManager()
    manager._sessions.clear()

    session = manager.create_session("s1", "strat", "BTC/USDT")

    session.orders = [
        {"id": "o1", "status": "open"},
        {"id": "o2", "status": "filled"},
        {"id": "o3", "status": "pending"},
        {"id": "o4", "status": "canceled"},
    ]

    session_dict = session.to_dict()

    # Should only include orders that are not filled or canceled
    open_orders = session_dict['open_orders']
    assert len(open_orders) == 2
    order_ids = [o['id'] for o in open_orders]
    assert "o1" in order_ids
    assert "o3" in order_ids

