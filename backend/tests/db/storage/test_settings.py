import os

import pytest
from cryptography.fernet import Fernet

from src.db.storage.settings import SettingsStorage
from src.db.models import UserSettingsModel


@pytest.fixture
def storage(monkeypatch, tmp_path):
    monkeypatch.setenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    db_path = (tmp_path / "test_settings.db").as_posix()
    return SettingsStorage(f"sqlite:///{db_path}")


def test_normalize_user_id(storage):
    assert storage._normalize_user_id(None) is None
    assert storage._normalize_user_id("") is None
    assert storage._normalize_user_id("anonymous") is None
    assert storage._normalize_user_id("user-1") == "user-1"


def test_save_and_get_encrypted_openai_key(storage):
    assert storage.save_credential("openai_api_key", "sk-secret", user_id="u1") is True

    # Stored value is encrypted (not plaintext)
    db = storage.get_db_session()
    try:
        row = db.query(UserSettingsModel).filter(UserSettingsModel.user_id == "u1").first()
        assert row is not None
        assert row.openai_api_key != "sk-secret"
    finally:
        db.close()

    assert storage.get_credential("openai_api_key", user_id="u1") == "sk-secret"


def test_get_credential_with_fallback_env_bool(monkeypatch, storage):
    monkeypatch.setenv("ENABLE_LOGIN", "false")
    value, source = storage.get_credential_with_fallback("enable_login", user_id="missing-user")
    assert value is False
    assert source == "env"


def test_get_credential_with_fallback_none_when_missing(monkeypatch, storage):
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    value, source = storage.get_credential_with_fallback("openai_base_url", user_id="missing-user")
    assert value is None
    assert source == "none"


def test_save_and_get_ccxt_credentials(storage):
    ok = storage.save_ccxt_credentials(
        "binance",
        "paper",
        {"api_key": "k", "secret": "s", "passphrase": "p"},
        user_id="u1",
    )
    assert ok is True

    creds = storage.get_ccxt_credentials("binance", "paper", user_id="u1")
    assert creds == {"api_key": "k", "secret": "s", "passphrase": "p"}


def test_save_ccxt_credentials_allows_deletion(storage):
    assert storage.save_ccxt_credentials(
        "binance",
        "paper",
        {"api_key": "k", "secret": "s", "passphrase": "p"},
        user_id="u1",
    )
    assert storage.save_ccxt_credentials(
        "binance",
        "paper",
        {"passphrase": None},
        user_id="u1",
    )

    creds = storage.get_ccxt_credentials("binance", "paper", user_id="u1")
    assert creds == {"api_key": "k", "secret": "s"}


def test_get_ccxt_credentials_all_env_fallback(monkeypatch, storage):
    monkeypatch.setenv("CCXT_BINANCE_PAPER_API_KEY", "sk-abc123def456ghi789")
    monkeypatch.setenv("CCXT_BINANCE_PAPER_SECRET", "sk-xyz123def456ghi789")
    monkeypatch.delenv("CCXT_BINANCE_PAPER_PASSPHRASE", raising=False)

    all_creds, source = storage.get_ccxt_credentials_all(user_id="missing", mask_sensitive=True)

    assert source == "mixed"  # env + none for other exchanges/modes
    assert all_creds["binance"]["paper"]["source"] == "env"
    assert "x" in all_creds["binance"]["paper"]["api_key"]
    assert "x" in all_creds["binance"]["paper"]["secret"]


def test_get_all_credentials_includes_sources(monkeypatch, storage):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-abc123def456ghi789")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("ENABLE_LOGIN", "false")

    data = storage.get_all_credentials(user_id="missing", mask_sensitive=True)

    assert data["openai"]["api_key_source"] == "env"
    assert data["openai"]["base_url_source"] == "env"
    assert "x" in data["openai"]["api_key"]
    assert data["openai"]["base_url"] == "https://example.com/v1"
    assert data["logto"]["enable_login"] is False
    assert data["logto"]["enable_login_source"] == "env"
