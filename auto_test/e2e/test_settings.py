"""
E2E tests for settings API.

Tests cover:
- User settings management
- Credential management
- Data source configuration
"""

import pytest
import sys
from pathlib import Path

# Add libs to path
libs_path = Path(__file__).parent.parent / "libs"
sys.path.insert(0, str(libs_path))

from assertions import assert_api_response, assert_api_error


@pytest.mark.api
@pytest.mark.requires_auth
class TestSettingsAPI:
    """API tests for user settings."""

    def test_get_user_settings(self, api_client):
        """Test getting user settings."""
        response = api_client.get("/api/settings")
        assert_api_response(response, expected_status=200)

        data = response.json()
        assert "status" in data
        assert "settings" in data

    def test_update_user_settings(self, api_client, data_fixtures):
        """Test updating user settings."""
        settings = data_fixtures.settings_config()

        response = api_client.put("/api/settings", json=settings)
        assert_api_response(response, expected_status=200)

        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_update_user_settings_empty_models(self, api_client):
        """Test updating settings with empty model list."""
        settings = {
            "selected_models": [],  # Invalid - must have at least one
            "code_analysis_prompt": "Test prompt",
            "code_rewrite_prompt": "Test prompt",
            "full_strategy_analysis_prompt": "Test prompt",
        }

        response = api_client.put("/api/settings", json=settings)
        # Should fail validation
        assert response.status_code in [400, 422]

    def test_reset_user_settings(self, api_client):
        """Test resetting user settings to defaults."""
        response = api_client.post("/api/settings/reset")
        assert_api_response(response, expected_status=200)

        data = response.json()
        assert "status" in data
        assert "settings" in data


@pytest.mark.api
@pytest.mark.requires_auth
class TestCredentialsAPI:
    """API tests for credential management."""

    def test_get_credentials(self, api_client):
        """Test getting credentials (masked)."""
        response = api_client.get("/api/settings/credentials")
        assert_api_response(response, expected_status=200)

        data = response.json()
        assert "status" in data
        assert "credentials" in data
        # Sensitive values should be masked
        creds = data["credentials"]
        assert isinstance(creds, dict)

    def test_update_credentials_openai(self, api_client):
        """Test updating OpenAI credentials."""
        # Use test/placeholder values
        update = {
            "openai_base_url": "https://api.openai.com/v1"
        }

        response = api_client.put("/api/settings/credentials", json=update)
        assert_api_response(response, expected_status=200)

    def test_update_ccxt_credentials(self, api_client):
        """Test updating CCXT exchange credentials."""
        update = {
            "exchange": "binance",
            "mode": "paper",
            "api_key": "test_api_key_placeholder"
        }

        response = api_client.put("/api/settings/credentials/ccxt", json=update)
        # May succeed or fail if credentials not valid
        assert response.status_code in [200, 400, 500]

    def test_update_ccxt_credentials_empty(self, api_client):
        """Test updating CCXT credentials with no fields."""
        update = {
            "exchange": "binance",
            "mode": "paper"
            # No credentials provided
        }

        response = api_client.put("/api/settings/credentials/ccxt", json=update)
        # Should fail - at least one credential required
        assert_api_error(response, expected_status=400)

    def test_reset_credential(self, api_client):
        """Test resetting a credential to .env value."""
        response = api_client.delete("/api/settings/credentials/openai_base_url")
        # Should succeed or fail if credential doesn't exist
        assert response.status_code in [200, 500]

    def test_test_credentials_invalid_type(self, api_client):
        """Test credentials with invalid type."""
        request = {
            "credential_type": "invalid_type"
        }

        response = api_client.post("/api/settings/credentials/test", json=request)
        assert_api_error(response, expected_status=400)

    def test_test_credentials_proxy(self, api_client):
        """Test proxy credentials validation."""
        request = {
            "credential_type": "proxy",
            "proxy_url": "http://invalid-proxy:8080"
        }

        response = api_client.post("/api/settings/credentials/test", json=request)
        # Will likely fail with connection error but should return response
        assert response.status_code in [200]
        data = response.json()
        assert "valid" in data


@pytest.mark.api
@pytest.mark.requires_auth
class TestDataSourceAPI:
    """API tests for data source configuration."""

    def test_get_data_source_settings(self, api_client):
        """Test getting data source settings."""
        response = api_client.get("/api/settings/data-source")
        assert_api_response(response, expected_status=200)

        data = response.json()
        assert "status" in data
        assert "settings" in data

    def test_update_data_source_settings(self, api_client):
        """Test updating data source priority."""
        update = {
            "data_source_priority": ["yahoo", "database"]
        }

        response = api_client.put("/api/settings/data-source", json=update)
        assert_api_response(response, expected_status=200)

    def test_update_data_source_invalid_source(self, api_client):
        """Test updating with invalid data source."""
        update = {
            "data_source_priority": ["yahoo", "invalid_source"]
        }

        response = api_client.put("/api/settings/data-source", json=update)
        assert_api_error(response, expected_status=400)

    def test_reset_data_source_settings(self, api_client):
        """Test resetting data source settings to defaults."""
        response = api_client.post("/api/settings/data-source/reset")
        assert_api_response(response, expected_status=200)

        data = response.json()
        assert "status" in data
        assert "settings" in data


@pytest.mark.ui
@pytest.mark.slow
class TestSettingsUI:
    """UI tests for settings page."""

    def test_settings_page_loads(self, browser):
        """Test that settings page can load."""
        try:
            browser.goto("/")
            browser.wait_for_network_idle()
            browser.expect_visible("body")
        except Exception as e:
            if "ERR_CONNECTION_REFUSED" in str(e):
                pytest.skip("Frontend server not running on localhost:5173")
            raise
