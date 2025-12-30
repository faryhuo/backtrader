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
)


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
