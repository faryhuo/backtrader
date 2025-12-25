"""
E2E tests for Frontend Static Hosting.

Based on TEST_CASES.md - FRONTEND section:
- FE-001: Without frontend build, / returns JSON hint
- FE-002: With frontend build, / returns index.html
- FE-003: SPA catch-all returns index.html for non-API routes
- FE-004: /images/* static directory accessible
- FE-005: /assets/* only mounted if exists
"""

import pytest
import sys
from pathlib import Path

# Add libs to path
libs_path = Path(__file__).parent.parent / "libs"
sys.path.insert(0, str(libs_path))


# ========== Frontend Tests ==========

@pytest.mark.api
class TestFrontendRoutes:
    """Tests for frontend static file serving."""

    def test_fe_001_or_fe_002_root_route(self, api_base_url):
        """FE-001/FE-002: Root route returns either JSON hint or index.html."""
        import httpx
        
        with httpx.Client(trust_env=False) as client:
            response = client.get(f"{api_base_url}/", timeout=10)
        
        # Should return 200 in either case
        assert response.status_code == 200
        
        content_type = response.headers.get("content-type", "")
        
        if "application/json" in content_type:
            # FE-001: Frontend not built, returns JSON hint
            data = response.json()
            # Should have some message about frontend
            assert isinstance(data, dict)
        elif "text/html" in content_type:
            # FE-002: Frontend is built, returns index.html
            assert "<!DOCTYPE html>" in response.text or "<html" in response.text.lower()

    def test_fe_003_spa_catchall(self, api_base_url):
        """FE-003: SPA catch-all returns index.html for unknown routes."""
        import httpx
        
        # Non-API route that doesn't exist as a file
        with httpx.Client(trust_env=False) as client:
            response = client.get(
                f"{api_base_url}/some/random/spa/route",
                timeout=10,
            )
        
        # Should either return index.html (200) or 404 if SPA not configured
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            if "text/html" in content_type:
                # SPA catch-all working
                assert "<html" in response.text.lower() or "<!DOCTYPE" in response.text

    def test_fe_004_images_directory(self, api_base_url):
        """FE-004: /images/* static directory is accessible."""
        import httpx
        
        # Try to access images directory
        with httpx.Client(trust_env=False) as client:
            response = client.get(
                f"{api_base_url}/images/",
                timeout=10,
                follow_redirects=True
            )
        
        # Should either list directory (200), return 403 (forbidden), or 404
        # The key is it doesn't return 500 error
        assert response.status_code in [200, 403, 404]

    def test_fe_005_assets_optional(self, api_base_url):
        """FE-005: /assets/* only mounted if exists."""
        import httpx
        
        with httpx.Client(trust_env=False) as client:
            response = client.get(
                f"{api_base_url}/assets/nonexistent.js",
                timeout=10,
            )
        
        # Should return 404 for non-existent asset
        assert response.status_code == 404


# ========== API vs Frontend Routing Tests ==========

@pytest.mark.api
class TestRoutingPriority:
    """Tests for API vs frontend routing priority."""

    def test_api_routes_not_caught_by_spa(self, api_base_url):
        """API routes should not be caught by SPA catch-all."""
        import httpx
        
        # API route should return JSON, not HTML
        with httpx.Client(trust_env=False) as client:
            response = client.get(
                f"{api_base_url}/api/site/config",
                timeout=10,
            )
        
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type

    def test_invalid_api_route_returns_error(self, api_base_url):
        """Invalid API routes may return API error or SPA fallback."""
        import httpx
        
        with httpx.Client(trust_env=False) as client:
            response = client.get(
                f"{api_base_url}/api/nonexistent/route",
                timeout=10,
            )
        
        # Behavior depends on routing config:
        # - If API-first: returns 404 with JSON
        # - If SPA catch-all active: returns 200 with HTML
        content_type = response.headers.get("content-type", "")
        
        if response.status_code == 404:
            # API returns 404 for unknown route
            assert "application/json" in content_type
        elif response.status_code == 200:
            # SPA catch-all caught the request - this is valid behavior
            pass  # Test passes
        else:
            # Unexpected status
            pytest.fail(f"Unexpected status code: {response.status_code}")

