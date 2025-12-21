from datetime import datetime

from src.db.storage.session import SessionStorage
from src.service.session_manager import SessionStatus, TradingSession


def test_save_load_list_delete_session(tmp_path):
    db_path = (tmp_path / "sessions.sqlite").as_posix()
    storage = SessionStorage(f"sqlite:///{db_path}")

    session = TradingSession(
        session_id="s1",
        strategy_name="strat",
        symbol="BTC/USDT",
        exchange="binance",
        mode="paper",
        timeframe="1m",
        initial_cash=10000.0,
        commission=0.001,
        status=SessionStatus.RUNNING,
        start_time=datetime.utcnow(),
    )
    storage.save_session(session)

    loaded = storage.load_session("s1")
    assert loaded is not None
    assert loaded.session_id == "s1"
    assert loaded.status == SessionStatus.RUNNING

    listed = storage.list_sessions()
    assert len(listed) == 1

    assert storage.delete_session("s1") is True
    assert storage.load_session("s1") is None

