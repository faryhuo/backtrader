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

