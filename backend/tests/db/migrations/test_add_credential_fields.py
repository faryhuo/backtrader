import sqlite3

from sqlalchemy import create_engine, text

from src.db.migrations.add_credential_fields import run_migration


def test_add_credential_fields_migration(tmp_path):
    db_path = (tmp_path / "db.sqlite").as_posix()
    url = f"sqlite:///{db_path}"

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("CREATE TABLE user_settings (id INTEGER PRIMARY KEY)")
        conn.commit()
    finally:
        conn.close()

    run_migration(url)

    engine = create_engine(url)
    with engine.connect() as conn:
        cols = conn.execute(text("SELECT name FROM pragma_table_info('user_settings')")).fetchall()
    col_names = {row[0] for row in cols}
    assert "openai_api_key" in col_names
    assert "ccxt_credentials" in col_names

