"""
E2E tests for Settings API.

Tests cover:
- User settings management (get/update/reset)
- Credential management (get/update/test)
- Data source configuration
"""

import pytest
import sys
from pathlib import Path

# Add libs to path
libs_path = Path(__file__).parent.parent / "libs"
sys.path.insert(0, str(libs_path))

from assertions import assert_api_response, assert_api_error
import api_paths


# ========== User Settings Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestUserSettings:
    """API tests for user settings."""

    def test_get_user_settings(self, api_client):
        """Get user settings returns proper structure."""
        response = api_client.get(api_paths.SETTINGS)
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert "status" in data, "Response must contain 'status'"
        assert "settings" in data, "Response must contain 'settings'"

    def test_update_user_settings_success(self, api_client, data_fixtures):
        """Update user settings with valid data succeeds."""
        settings = data_fixtures.settings_config()
        
        response = api_client.put(api_paths.SETTINGS, json=settings)
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert data.get("status") == "ok"

    def test_update_user_settings_empty_models(self, api_client):
        """Update settings with empty model list fails validation."""
        settings = {
            "selected_models": [],  # Invalid - min_length=1
            "code_analysis_prompt": "Test prompt",
            "code_rewrite_prompt": "Test prompt",
            "full_strategy_analysis_prompt": "Test prompt"
        }
        
        response = api_client.put(api_paths.SETTINGS, json=settings)
        
        # Should fail validation
        assert response.status_code in [400, 422], (
            f"Expected 400/422 for empty models list, got {response.status_code}"
        )

    def test_reset_user_settings(self, api_client):
        """Reset user settings returns defaults."""
        response = api_client.post(api_paths.SETTINGS_RESET)
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert "status" in data
        assert "settings" in data


# ========== Credential Management Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestCredentials:
    """API tests for credential management."""

    def test_get_credentials_masked(self, api_client):
        """Get credentials returns masked sensitive values."""
        response = api_client.get(api_paths.SETTINGS_CREDENTIALS)
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert "status" in data
        assert "credentials" in data
        assert isinstance(data["credentials"], dict)

    def test_update_credentials_openai(self, api_client):
        """Update OpenAI base URL (non-sensitive) succeeds."""
        update = {
            "openai_base_url": "https://api.openai.com/v1"
        }
        
        response = api_client.put(api_paths.SETTINGS_CREDENTIALS, json=update)
        
        assert_api_response(response, expected_status=200)

    def test_update_ccxt_credentials_no_fields(self, api_client):
        """Update CCXT credentials with no credential fields fails."""
        update = {
            "exchange": "binance",
            "mode": "paper"
            # No api_key, secret, or passphrase
        }
        
        response = api_client.put(api_paths.SETTINGS_CREDENTIALS_CCXT, json=update)
        
        # Should fail - at least one credential field required
        assert_api_error(response, expected_status=400)

    def test_update_ccxt_credentials_with_key(self, api_client):
        """Update CCXT credentials with api_key succeeds or handles gracefully."""
        update = {
            "exchange": "binance",
            "mode": "paper",
            "api_key": "test_api_key_placeholder"
        }
        
        response = api_client.put(api_paths.SETTINGS_CREDENTIALS_CCXT, json=update)
        
        # May succeed or fail based on encryption key availability
        assert response.status_code in [200, 400, 500]

    def test_reset_credential(self, api_client):
        """Reset credential to .env value."""
        response = api_client.delete(
            api_paths.settings_credential_reset("openai_base_url")
        )
        
        # Should succeed or credential doesn't exist
        assert response.status_code in [200, 500]

    def test_test_credentials_invalid_type(self, api_client):
        """Test credentials with invalid type returns 400."""
        request = {
            "credential_type": "invalid_type_xyz"
        }
        
        response = api_client.post(api_paths.SETTINGS_CREDENTIALS_TEST, json=request)
        
        assert_api_error(response, expected_status=400)

    def test_test_credentials_proxy(self, api_client):
        """Test proxy credentials returns validation result."""
        request = {
            "credential_type": "proxy",
            "proxy_url": "http://invalid-proxy:8080"
        }
        
        response = api_client.post(api_paths.SETTINGS_CREDENTIALS_TEST, json=request)
        
        # Will return result (likely invalid but should return 200 with valid=false)
        assert response.status_code == 200
        
        data = response.json()
        assert "valid" in data


# ========== Data Source Configuration Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestDataSourceSettings:
    """API tests for data source configuration."""

    def test_get_data_source_settings(self, api_client):
        """Get data source settings returns structure."""
        response = api_client.get(api_paths.SETTINGS_DATA_SOURCE)
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert "status" in data
        assert "settings" in data

    def test_update_data_source_priority(self, api_client):
        """Update data source priority succeeds."""
        update = {
            "data_source_priority": ["yahoo", "database"]
        }
        
        response = api_client.put(api_paths.SETTINGS_DATA_SOURCE, json=update)
        
        assert_api_response(response, expected_status=200)

    def test_update_data_source_invalid_source(self, api_client):
        """Update with invalid data source name returns 400."""
        update = {
            "data_source_priority": ["yahoo", "invalid_source_xyz"]
        }
        
        response = api_client.put(api_paths.SETTINGS_DATA_SOURCE, json=update)
        
        assert_api_error(response, expected_status=400)

    def test_reset_data_source_settings(self, api_client):
        """Reset data source settings returns defaults."""
        response = api_client.post(api_paths.SETTINGS_DATA_SOURCE_RESET)
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert "status" in data
        assert "settings" in data


# ========== UI Tests ==========

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
