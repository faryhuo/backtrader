from sqlalchemy import create_engine, text

from src.db.migrate_cleanup_json import cleanup_corrupted_json


def test_cleanup_corrupted_json_deletes_bad_records(tmp_path):
    db_path = (tmp_path / "db.sqlite").as_posix()
    url = f"sqlite:///{db_path}"
    engine = create_engine(url)

    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE backtest_history (id INTEGER PRIMARY KEY, metrics TEXT, ai_analysis TEXT)"))
        conn.execute(text("INSERT INTO backtest_history (metrics, ai_analysis) VALUES ('', NULL)"))
        conn.execute(text("INSERT INTO backtest_history (metrics, ai_analysis) VALUES ('{}', '')"))
        conn.execute(text("INSERT INTO backtest_history (metrics, ai_analysis) VALUES ('{}', NULL)"))

    deleted = cleanup_corrupted_json(url)
    assert deleted >= 1

    with engine.connect() as conn:
        remaining = conn.execute(text("SELECT COUNT(*) FROM backtest_history")).scalar()
    assert remaining == 1

