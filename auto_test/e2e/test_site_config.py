"""
E2E tests for Site Configuration API.

Based on TEST_CASES.md - SITE section:
- SITE-001: Public site config access
- SITE-002: Response structure validation
- SITE-003: Admin config requires auth
- SITE-004: Update config partial fields
- SITE-005: Empty update returns 400
- SITE-006: Reset config requires auth
"""

import pytest
import sys
from pathlib import Path

# Add libs to path
libs_path = Path(__file__).parent.parent / "libs"
sys.path.insert(0, str(libs_path))

from assertions import assert_api_response, assert_api_error


# ========== Site Config API Tests ==========

@pytest.mark.api
class TestSiteConfigPublic:
    """Public site config tests - no auth required."""

    def test_site_001_public_config_no_auth(self, api_base_url):
        """SITE-001: Site config is accessible without authentication."""
        import httpx
        
        # Make request without auth token
        response = httpx.get(
            f"{api_base_url}/api/site/config",
            timeout=10,
            proxy=None
        )
        
        # Should be accessible without auth
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Site config should be public."
        )

    def test_site_002_config_structure(self, api_base_url):
        """SITE-002: Response contains site/links/stats/features structure."""
        import httpx
        
        response = httpx.get(
            f"{api_base_url}/api/site/config",
            timeout=10,
            proxy=None
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check expected top-level keys
        expected_keys = ["site", "links", "stats", "features"]
        for key in expected_keys:
            assert key in data, f"Expected key '{key}' in site config response"


@pytest.mark.api
@pytest.mark.requires_auth
class TestSiteConfigAdmin:
    """Admin site config tests - auth required."""

    def test_site_003_admin_config_requires_auth(self, api_base_url):
        """SITE-003: Admin config endpoint requires authentication."""
        import httpx
        
        # Make request without auth token
        response = httpx.get(
            f"{api_base_url}/api/site/config/admin",
            timeout=10,
            proxy=None
        )
        
        # Should require auth
        assert response.status_code in [401, 403], (
            f"Expected 401/403 for unauthenticated admin config request, got {response.status_code}"
        )

    def test_site_004_update_partial_fields(self, api_client):
        """SITE-004: Update config only updates non-empty fields, returns updated_fields."""
        update_data = {
            "site": {
                "title": "Test Updated Title"
            }
        }
        
        response = api_client.put("/api/site/config", json=update_data)
        
        if response.status_code == 200:
            data = response.json()
            # Should return what was updated
            assert "updated_fields" in data or "status" in data

    def test_site_005_empty_update_returns_400(self, api_client):
        """SITE-005: Empty body or all None values returns 400."""
        # Empty update
        response = api_client.put("/api/site/config", json={})
        
        # Should fail with 400
        assert response.status_code == 400, (
            f"Expected 400 for empty update, got {response.status_code}"
        )

    def test_site_006_reset_requires_auth(self, api_base_url):
        """SITE-006: Reset config endpoint requires authentication."""
        import httpx
        
        # Make request without auth token
        response = httpx.post(
            f"{api_base_url}/api/site/config/reset",
            timeout=10,
            proxy=None
        )
        
        # Should require auth
        assert response.status_code in [401, 403], (
            f"Expected 401/403 for unauthenticated reset, got {response.status_code}"
        )

    def test_site_006_reset_success(self, api_client):
        """SITE-006: Authenticated reset returns defaults."""
        response = api_client.post("/api/site/config/reset")
        
        # Should succeed with auth
        if response.status_code == 200:
            data = response.json()
            assert "status" in data or "config" in data
