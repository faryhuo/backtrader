import os
from datetime import datetime, timedelta

from src.db.storage.backtest import BacktestStorage


def test_save_and_list_backtests_with_cleanup(tmp_path, monkeypatch):
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    monkeypatch.setattr("src.db.storage.backtest.IMAGES_DIR", images_dir, raising=False)

    db_path = (tmp_path / "backtests.sqlite").as_posix()
    storage = BacktestStorage(f"sqlite:///{db_path}")
    storage.MAX_RECORDS = 1

    old_plot = images_dir / "old.png"
    old_plot.write_text("x", encoding="utf-8")

    metrics = {"final_value": 1.0, "returns": 2.0, "trade_details": {}}
    config = {"ticker": "AAPL", "start_date": "2024-01-01", "end_date": "2024-02-01"}

    first = storage.save_backtest(
        backtest_id="b1",
        config=config,
        metrics=metrics,
        plot_filename="old.png",
        user_id="u1",
    )
    first.created_at = datetime.utcnow() - timedelta(days=10)

    db = storage.get_db_session()
    try:
        db.add(first)
        db.commit()
    finally:
        db.close()

    storage.save_backtest(
        backtest_id="b2",
        config=config,
        metrics=metrics,
        plot_filename=None,
        user_id="u1",
    )

    listing = storage.list_backtests(user_id="u1", limit=10, offset=0)
    assert listing["total"] == 1
    assert listing["backtests"][0]["backtest_id"] == "b2"
    assert os.path.exists(old_plot) is False

