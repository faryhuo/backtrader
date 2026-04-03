"""Tests for setup wizard auth-provider validation."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.service.setup_wizard_service import SetupWizardService
from src.service.auth_service import AuthService, AuthTokens, bootstrap_system_admin_from_env
from src.db.storage.user_auth import UserAuthStorage
from src.utils.encryption import mask_credential


def _base_payload() -> dict:
    return {
        "deployment_mode": "local",
        "security": {"encryption_key": "test-secret", "enable_login": False},
        "database": {"mode": "sqlite", "sqlite_path": "trading_sessions.db"},
        "auth": {
            "auth_provider": "none",
            "system_auth_allow_registration": False,
            "logto_issuer": "",
            "logto_jwks_uri": "",
            "logto_audience": "",
            "logto_required_scopes": "",
            "logto_endpoint": "",
            "logto_app_id": "",
            "logto_redirect_uri": "",
            "logto_post_logout_redirect_uri": "",
        },
        "data_source": {"priority": ["yahoo", "database"], "eodhd_api_key": ""},
        "ai": {"enabled": False, "provider_priority": ["openai"], "providers": {}},
        "trading": {
            "live_trading_enabled": False,
            "default_trade_mode": "paper",
            "binance": {},
            "risk": {},
            "credentials": {"paper": {"api_key": "", "secret": ""}, "live": {"api_key": "", "secret": ""}},
            "live_risk_acknowledged": False,
        },
        "strategy": {},
        "site": {},
        "report": {"enable_public_share": False, "report_share_secret": "", "report_max_age_days": 30, "output_directory": "data/reports"},
        "network": {},
    }


def test_public_system_auth_is_valid():
    payload = _base_payload()
    payload["deployment_mode"] = "public"
    payload["auth"]["auth_provider"] = "system"
    payload["auth"]["system_auth_allow_registration"] = True

    validated = SetupWizardService().validate_payload(payload)

    assert validated.security.enable_login is True
    assert validated.auth.auth_provider == "system"


def test_public_logto_requires_fields():
    payload = _base_payload()
    payload["deployment_mode"] = "public"
    payload["auth"]["auth_provider"] = "logto"

    try:
        SetupWizardService().validate_payload(payload)
    except ValueError as exc:
        assert "Logto fields required when login is enabled" in str(exc)
    else:
        raise AssertionError("Expected ValueError for incomplete Logto config")


def test_auth_service_create_user_returns_serializable_user_after_commit(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'auth.sqlite'}"
    monkeypatch.setenv("SYSTEM_AUTH_SECRET", "test-secret-key")
    monkeypatch.setenv("ENCRYPTION_KEY", "test-secret-key")

    auth_service = AuthService(user_storage=UserAuthStorage(database_url=database_url))
    user = auth_service.create_user(
        email="admin@example.com",
        password="password123",
        display_name="Admin",
        is_superuser=True,
    )

    assert user["email"] == "admin@example.com"
    assert user["name"] == "Admin"
    assert user["is_superuser"] is True
    assert user["sub"].startswith("system:")


def test_bootstrap_system_admin_from_env_creates_first_user(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'bootstrap.sqlite'}"
    monkeypatch.setenv("ENABLE_LOGIN", "true")
    monkeypatch.setenv("AUTH_PROVIDER", "system")
    monkeypatch.setenv("SYSTEM_AUTH_SECRET", "test-secret-key")
    monkeypatch.setenv("ENCRYPTION_KEY", "test-secret-key")
    monkeypatch.setenv("SYSTEM_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("SYSTEM_ADMIN_PASSWORD", "password123")
    monkeypatch.setenv("SYSTEM_ADMIN_DISPLAY_NAME", "Admin")

    auth_service = AuthService(user_storage=UserAuthStorage(database_url=database_url))

    user = bootstrap_system_admin_from_env(auth_service)

    assert user is not None
    assert user["email"] == "admin@example.com"
    assert user["name"] == "Admin"
    assert user["is_superuser"] is True
    assert auth_service.user_storage.count_users() == 1


def test_bootstrap_system_admin_from_env_is_noop_when_users_exist(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'bootstrap-existing.sqlite'}"
    monkeypatch.setenv("ENABLE_LOGIN", "true")
    monkeypatch.setenv("AUTH_PROVIDER", "system")
    monkeypatch.setenv("SYSTEM_AUTH_SECRET", "test-secret-key")
    monkeypatch.setenv("ENCRYPTION_KEY", "test-secret-key")
    monkeypatch.setenv("SYSTEM_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("SYSTEM_ADMIN_PASSWORD", "password123")

    auth_service = AuthService(user_storage=UserAuthStorage(database_url=database_url))
    auth_service.create_user(
        email="existing@example.com",
        password="password123",
        display_name="Existing",
        is_superuser=True,
    )

    user = bootstrap_system_admin_from_env(auth_service)

    assert user is None
    assert auth_service.user_storage.count_users() == 1


def test_bootstrap_system_admin_from_env_is_noop_when_auth_provider_is_not_system(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'bootstrap-none.sqlite'}"
    monkeypatch.setenv("ENABLE_LOGIN", "false")
    monkeypatch.setenv("AUTH_PROVIDER", "none")
    monkeypatch.setenv("SYSTEM_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("SYSTEM_ADMIN_PASSWORD", "password123")

    auth_service = AuthService(user_storage=UserAuthStorage(database_url=database_url))

    user = bootstrap_system_admin_from_env(auth_service)

    assert user is None
    assert auth_service.user_storage.count_users() == 0


def test_save_returns_bootstrap_auth_for_first_system_admin(tmp_path, monkeypatch):
    payload = _base_payload()
    payload["deployment_mode"] = "public"
    payload["security"]["encryption_key"] = "test-secret-key"
    payload["auth"]["auth_provider"] = "system"
    payload["auth"]["system_auth_allow_registration"] = False
    payload["auth"]["first_admin_email"] = "admin@example.com"
    payload["auth"]["first_admin_password"] = "password123"
    payload["auth"]["first_admin_display_name"] = "Admin"

    class StubUserAuthStorage:
        def count_users(self):
            return 0

    class StubAuthService:
        def __init__(self):
            self.user_storage = SimpleNamespace(count_users=lambda: 0)

        def create_user(self, **kwargs):
            return {"id": 1, "email": kwargs["email"]}

        def login_user(self, email, password):
            return AuthTokens(
                access_token="bootstrap-token",
                token_type="bearer",
                expires_in=28800,
                user={
                    "id": 1,
                    "sub": "system:1",
                    "email": email,
                    "name": "Admin",
                    "auth_provider": "system",
                    "is_superuser": True,
                    "is_active": True,
                },
            )

    service = SetupWizardService()
    service.backend_env_path = tmp_path / ".env"
    service.backend_env_template_path = tmp_path / ".env.template"
    service.database_config_path = tmp_path / "database_config.json"
    service.strategy_config_path = tmp_path / "strategy_config.json"
    service.broker_config_path = tmp_path / "broker_config.json"
    service.report_config_path = tmp_path / "report_config.json"
    service.logger_config_path = tmp_path / "logger_config.json"
    service.settings_storage = MagicMock()
    service.settings_storage.save_credential.return_value = True

    monkeypatch.setattr("src.db.storage.user_auth.UserAuthStorage", StubUserAuthStorage)
    monkeypatch.setattr("src.service.auth_service.AuthService", StubAuthService)

    result = service.save(payload)

    assert result["status"] == "ok"
    assert result["bootstrap_auth"]["access_token"] == "bootstrap-token"
    assert result["bootstrap_auth"]["user"]["email"] == "admin@example.com"


def test_save_keeps_real_system_auth_secret_when_encryption_key_input_is_masked(tmp_path):
    payload = _base_payload()
    payload["deployment_mode"] = "public"
    payload["auth"]["auth_provider"] = "system"
    payload["auth"]["system_auth_allow_registration"] = True

    real_encryption_key = "AbCdEfGhIjKlMnOpQrStUvWxYz0123456789+/=="
    payload["security"]["encryption_key"] = mask_credential(real_encryption_key)

    service = SetupWizardService()
    service.backend_env_path = tmp_path / ".env"
    service.backend_env_template_path = tmp_path / ".env.template"
    service.database_config_path = tmp_path / "database_config.json"
    service.strategy_config_path = tmp_path / "strategy_config.json"
    service.broker_config_path = tmp_path / "broker_config.json"
    service.report_config_path = tmp_path / "report_config.json"
    service.logger_config_path = tmp_path / "logger_config.json"
    service.settings_storage = MagicMock()
    service.settings_storage.save_credential.return_value = True

    service.backend_env_path.write_text(
        f"ENCRYPTION_KEY={real_encryption_key}\nSYSTEM_AUTH_SECRET={real_encryption_key}\n",
        encoding="utf-8",
    )

    result = service.save(payload)

    saved_env = service.backend_env_path.read_text(encoding="utf-8")
    assert result["status"] == "ok"
    assert f"ENCRYPTION_KEY={real_encryption_key}" in saved_env
    assert f"SYSTEM_AUTH_SECRET={real_encryption_key}" in saved_env
    assert f"ENCRYPTION_KEY={mask_credential(real_encryption_key)}" not in saved_env
    assert f"SYSTEM_AUTH_SECRET={mask_credential(real_encryption_key)}" not in saved_env


@patch("src.service.setup_wizard_service.SettingsStorage")
@patch("src.db.storage.user_auth.UserAuthStorage")
def test_get_wizard_state_uses_database_setup_completed_flag(mock_user_storage_cls, mock_settings_storage_cls):
    mock_settings_storage = MagicMock()
    mock_settings_storage.get_credential_with_fallback.return_value = (False, "database")
    mock_settings_storage_cls.return_value = mock_settings_storage
    mock_user_storage_cls.return_value.count_users.return_value = 0

    service = SetupWizardService()
    state = service.get_wizard_state()

    assert state["status"]["is_ready"] is False
    assert state["status"]["is_first_open"] is True


@patch("src.utils.credential_validator.validate_credential")
def test_test_endpoint_resolves_masked_ccxt_values_from_env(mock_validate_credential, tmp_path):
    service = SetupWizardService()
    service.backend_env_path = tmp_path / ".env"
    service.backend_env_template_path = tmp_path / ".env.template"
    service.backend_env_path.write_text(
        "CCXT_BINANCE_PAPER_API_KEY=paper-key-123\nCCXT_BINANCE_PAPER_SECRET=paper-secret-456\n",
        encoding="utf-8",
    )
    mock_validate_credential.return_value = (True, "ok")

    result = service.test_endpoint(
        "ccxt",
        {
            "exchange": "binance",
            "mode": "paper",
            "api_key": mask_credential("paper-key-123"),
            "secret": mask_credential("paper-secret-456"),
            "use_testnet": True,
        },
    )

    assert result["valid"] is True
    mock_validate_credential.assert_called_once_with(
        "ccxt",
        exchange="binance",
        mode="paper",
        api_key="paper-key-123",
        secret="paper-secret-456",
        use_testnet=True,
    )
