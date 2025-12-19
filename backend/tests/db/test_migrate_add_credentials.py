import sqlite3

from src.db import migrate_add_credentials


def test_migrate_add_credentials_adds_columns(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("CREATE TABLE user_settings (id INTEGER PRIMARY KEY, user_id TEXT)")
        conn.commit()
    finally:
        conn.close()

    monkeypatch.setattr(migrate_add_credentials, "DB_PATH", db_path)
    migrate_add_credentials.migrate()

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(user_settings)")
        cols = {row[1] for row in cur.fetchall()}
    finally:
        conn.close()

    assert "openai_api_key" in cols
    assert "ccxt_credentials" in cols

