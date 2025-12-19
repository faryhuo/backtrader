import os

import pytest

from src.config import config_manager as cm


@pytest.fixture
def stub_storage(monkeypatch):
    class StubSettingsStorage:
        def __init__(self, database_url):
            self.database_url = database_url
            self.values = {}
            self.ccxt_values = {}

        def get_credential_with_fallback(self, key, user_id=None):
            if key in self.values and self.values[key] is not None:
                return self.values[key], "database"
            env_val = os.getenv(key.upper())
            if env_val is not None and env_val != "":
                if key == "enable_login":
                    return env_val.lower() in {"true", "1", "yes", "on"}, "env"
                return env_val, "env"
            return None, "none"

        def get_ccxt_credentials(self, exchange, mode, user_id=None, db=None):
            return self.ccxt_values.get((exchange, mode, user_id))

    monkeypatch.setattr(cm, "SettingsStorage", StubSettingsStorage)
    return StubSettingsStorage


def test_config_manager_get_priority_db_over_env(stub_storage, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    manager = cm.ConfigManager(user_id="u1", database_url="sqlite:///:memory:")
    manager.settings_storage.values["openai_api_key"] = "db-key"

    assert manager.get("OPENAI_API_KEY") == "db-key"


def test_config_manager_get_falls_back_to_env(stub_storage, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    manager = cm.ConfigManager(user_id="u1", database_url="sqlite:///:memory:")

    assert manager.get("OPENAI_API_KEY") == "env-key"


def test_config_manager_get_default_when_missing(stub_storage):
    manager = cm.ConfigManager(user_id="u1", database_url="sqlite:///:memory:")
    assert manager.get("MISSING_KEY", default="x") == "x"


def test_get_openai_config_base_url_default(stub_storage, monkeypatch):
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    manager = cm.ConfigManager(user_id="u1", database_url="sqlite:///:memory:")
    manager.settings_storage.values["openai_api_key"] = "k"

    config = manager.get_openai_config()
    assert config["api_key"] == "k"
    assert config["base_url"] == "https://api.openai.com/v1"


@pytest.mark.parametrize(
    "raw,expected",
    [("true", True), ("1", True), ("yes", True), ("on", True), ("false", False), ("0", False), ("off", False)],
)
def test_enable_login_conversion(stub_storage, monkeypatch, raw, expected):
    monkeypatch.setenv("ENABLE_LOGIN", raw)
    manager = cm.ConfigManager(user_id="u1", database_url="sqlite:///:memory:")
    assert manager.get_logto_config()["enable_login"] is expected


def test_ccxt_credentials_fallback_to_env(stub_storage, monkeypatch):
    monkeypatch.setenv("CCXT_BINANCE_PAPER_API_KEY", "k")
    monkeypatch.setenv("CCXT_BINANCE_PAPER_SECRET", "s")
    monkeypatch.delenv("CCXT_BINANCE_PAPER_PASSPHRASE", raising=False)

    manager = cm.ConfigManager(user_id="u1", database_url="sqlite:///:memory:")
    creds = manager.get_ccxt_credentials("binance", "paper")
    assert creds["api_key"] == "k"
    assert creds["secret"] == "s"
    assert creds["passphrase"] is None
    assert manager.has_ccxt_credentials("binance", "paper") is True


def test_ccxt_credentials_from_db(stub_storage):
    manager = cm.ConfigManager(user_id="u1", database_url="sqlite:///:memory:")
    manager.settings_storage.ccxt_values[("binance", "paper", "u1")] = {
        "api_key": "dbk",
        "secret": "dbs",
        "passphrase": None,
    }
    creds = manager.get_ccxt_credentials("binance", "paper")
    assert creds["api_key"] == "dbk"
    assert creds["secret"] == "dbs"

