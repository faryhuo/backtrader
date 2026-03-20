"""
Unit tests for settings routes module.
"""
import pytest
from unittest.mock import MagicMock, patch

from src.routes.settings_routes import (
    router,
    UserSettingsRequest,
    CredentialUpdate,
    CCXTCredentialUpdate,
    CredentialTestRequest,
    DataSourceSettingsRequest,
    test_credentials as route_test_credentials,
    update_ccxt_credentials as route_update_ccxt_credentials,
    update_data_source_settings as route_update_data_source_settings,
)
from src.utils.encryption import mask_credential


class TestUserSettingsRequest:
    """Tests for UserSettingsRequest Pydantic model."""

    def test_valid_request(self):
        """Test creating valid UserSettingsRequest."""
        request = UserSettingsRequest(
            selected_models=["gpt-4", "gpt-3.5-turbo"],
            code_analysis_prompt="Analyze this code",
            code_rewrite_prompt="Rewrite this code",
            full_strategy_analysis_prompt="Analyze strategy",
        )
        assert len(request.selected_models) == 2
        assert "gpt-4" in request.selected_models


class TestCredentialUpdate:
    """Tests for CredentialUpdate Pydantic model."""

    def test_empty_update(self):
        """Test creating CredentialUpdate with no values."""
        update = CredentialUpdate()
        assert update.openai_api_key is None
        assert update.openai_base_url is None

    def test_partial_update(self):
        """Test creating CredentialUpdate with partial values."""
        update = CredentialUpdate(
            openai_api_key="sk-test",
            http_proxy="http://proxy:8080",
        )
        assert update.openai_api_key == "sk-test"
        assert update.http_proxy == "http://proxy:8080"
        assert update.https_proxy is None

    def test_logto_update(self):
        """Test creating CredentialUpdate with Logto values."""
        update = CredentialUpdate(
            logto_issuer="https://logto.example.com/oidc",
            logto_endpoint="https://logto.example.com",
            logto_app_id="app123",
        )
        assert update.logto_issuer is not None
        assert update.logto_endpoint is not None


class TestCCXTCredentialUpdate:
    """Tests for CCXTCredentialUpdate Pydantic model."""

    def test_valid_update(self):
        """Test creating valid CCXTCredentialUpdate."""
        update = CCXTCredentialUpdate(
            exchange="binance",
            mode="paper",
            api_key="test_key",
            secret="test_secret",
        )
        assert update.exchange == "binance"
        assert update.mode == "paper"
        assert update.api_key == "test_key"

    def test_with_passphrase(self):
        """Test creating CCXTCredentialUpdate with passphrase."""
        update = CCXTCredentialUpdate(
            exchange="okx",
            mode="live",
            api_key="test_key",
            secret="test_secret",
            passphrase="test_passphrase",
        )
        assert update.passphrase == "test_passphrase"


class TestCredentialTestRequest:
    """Tests for CredentialTestRequest Pydantic model."""

    def test_openai_test(self):
        """Test creating OpenAI credential test request."""
        request = CredentialTestRequest(
            credential_type="openai",
            api_key="sk-test",
            base_url="https://api.openai.com/v1",
        )
        assert request.credential_type == "openai"
        assert request.api_key == "sk-test"

    def test_ccxt_test(self):
        """Test creating CCXT credential test request."""
        request = CredentialTestRequest(
            credential_type="ccxt",
            exchange="binance",
            mode="paper",
            api_key="test_key",
            secret="test_secret",
        )
        assert request.credential_type == "ccxt"
        assert request.exchange == "binance"

    def test_proxy_test(self):
        """Test creating proxy credential test request."""
        request = CredentialTestRequest(
            credential_type="proxy",
            proxy_url="http://proxy:8080",
        )
        assert request.credential_type == "proxy"
        assert request.proxy_url == "http://proxy:8080"


class TestDataSourceSettingsRequest:
    """Tests for DataSourceSettingsRequest Pydantic model."""

    def test_priority_settings(self):
        """Test setting data source priority."""
        request = DataSourceSettingsRequest(
            data_source_priority=["eodhd", "yahoo", "database"],
        )
        assert request.data_source_priority[0] == "eodhd"

    def test_eodhd_api_key(self):
        """Test setting EODHD API key."""
        request = DataSourceSettingsRequest(
            eodhd_api_key="test_api_key",
        )
        assert request.eodhd_api_key == "test_api_key"

    def test_empty_request(self):
        """Test empty request."""
        request = DataSourceSettingsRequest()
        assert request.data_source_priority is None
        assert request.eodhd_api_key is None


class TestSettingsRouter:
    """Tests for settings router."""

    def test_router_exists(self):
        """Test that router is configured."""
        assert router is not None
        assert len(router.routes) > 0


class TestCredentialMaskResolution:
    """Tests for masked credential handling in settings routes."""

    @patch("src.routes.settings_routes.get_settings_storage")
    @patch("src.routes.settings_routes.validate_credential")
    def test_test_credentials_uses_stored_openai_key_for_masked_value(
        self,
        mock_validate_credential,
        mock_get_settings_storage,
    ):
        """Masked OpenAI keys should resolve to the stored plaintext before validation."""
        storage = MagicMock()
        storage.get_credential_with_fallback.return_value = ("sk-live-secret", "database")
        mock_get_settings_storage.return_value = storage
        mock_validate_credential.return_value = (True, "ok")

        request = CredentialTestRequest(
            credential_type="openai",
            api_key=mask_credential("sk-live-secret"),
            base_url="https://api.openai.com/v1",
        )

        response = route_test_credentials(request, user_id="u1")

        assert response["valid"] is True
        mock_validate_credential.assert_called_once_with(
            "openai",
            api_key="sk-live-secret",
            base_url="https://api.openai.com/v1",
        )

    @patch("src.routes.settings_routes.get_settings_storage")
    def test_update_ccxt_credentials_keeps_stored_secret_for_masked_value(
        self,
        mock_get_settings_storage,
    ):
        """Masked Binance credentials should not overwrite stored secrets with placeholder text."""
        storage = MagicMock()
        storage.get_ccxt_credentials_all.return_value = (
            {
                "binance": {
                    "paper": {
                        "api_key": "binance-key-123",
                        "secret": "binance-secret-456",
                    }
                }
            },
            "database",
        )
        storage.save_ccxt_credentials.return_value = True
        mock_get_settings_storage.return_value = storage

        request = CCXTCredentialUpdate(
            exchange="binance",
            mode="paper",
            api_key=mask_credential("binance-key-123"),
            secret=mask_credential("binance-secret-456"),
        )

        response = route_update_ccxt_credentials(request, user_id="u1")

        assert response["status"] == "ok"
        storage.save_ccxt_credentials.assert_called_once_with(
            exchange="binance",
            mode="paper",
            credentials={
                "api_key": "binance-key-123",
                "secret": "binance-secret-456",
            },
            user_id="u1",
        )

    @patch("src.routes.settings_routes.get_settings_storage")
    def test_update_data_source_settings_keeps_stored_eodhd_key_for_masked_value(
        self,
        mock_get_settings_storage,
    ):
        """Masked EODHD keys should not overwrite the stored plaintext value."""
        storage = MagicMock()
        storage.get_eodhd_api_key.return_value = "eodhd-live-key-123"
        storage.save_data_source_settings.return_value = True
        mock_get_settings_storage.return_value = storage

        request = DataSourceSettingsRequest(
            data_source_priority=["eodhd", "yahoo"],
            eodhd_api_key=mask_credential("eodhd-live-key-123"),
        )

        response = route_update_data_source_settings(request, user_id="u1")

        assert response["status"] == "ok"
        storage.save_data_source_settings.assert_called_once_with(
            data_source_priority=["eodhd", "yahoo"],
            eodhd_api_key="eodhd-live-key-123",
            user_id="u1",
        )
