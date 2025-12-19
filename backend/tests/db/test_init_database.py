from cryptography.fernet import Fernet

from src.db.models import UserSettingsModel, init_database
from src.utils.encryption import encrypt_value


def test_init_database_creates_tables(tmp_path, monkeypatch):
    monkeypatch.setenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    db_path = (tmp_path / "db.sqlite").as_posix()
    engine, session_local = init_database(f"sqlite:///{db_path}")

    session = session_local()
    try:
        row = UserSettingsModel(user_id="u1", selected_models="a,b")
        row.openai_api_key = encrypt_value("sk-test")
        session.add(row)
        session.commit()

        loaded = session.query(UserSettingsModel).filter(UserSettingsModel.user_id == "u1").first()
        assert loaded is not None
        assert loaded.selected_models == "a,b"
    finally:
        session.close()
        engine.dispose()

