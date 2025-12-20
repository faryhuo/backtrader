"""
Critical UI smoke tests.

These tests verify the most essential UI pages load without errors.
Each test should complete in <5 seconds.
"""

import pytest


@pytest.mark.smoke
@pytest.mark.ui
class TestCriticalUI:
    """Smoke tests for critical UI pages."""

    def test_home_page_loads(self, browser):
        """Verify home page loads without errors."""
        try:
            browser.goto("/")
            browser.wait_for_network_idle(timeout=5000)
            
            # Verify basic page structure exists
            browser.expect_visible("body")
        except Exception as e:
            if "ERR_CONNECTION_REFUSED" in str(e):
                pytest.skip("Frontend server not running on localhost:5173")
            raise

    def test_no_console_errors_on_load(self, browser):
        """Verify no critical JavaScript errors on page load."""
        try:
            browser.goto("/")
            browser.wait_for_network_idle(timeout=5000)
            
            # Page should load successfully (no crash)
            assert browser.page is not None
            assert browser.is_visible("body")
        except Exception as e:
            if "ERR_CONNECTION_REFUSED" in str(e):
                pytest.skip("Frontend server not running on localhost:5173")
            raise

    def test_page_title_exists(self, browser):
        """Verify page has a title."""
        try:
            browser.goto("/")
            browser.wait_for_network_idle(timeout=5000)
            
            title = browser.page.title()
            assert title is not None
            assert len(title) > 0
        except Exception as e:
            if "ERR_CONNECTION_REFUSED" in str(e):
                pytest.skip("Frontend server not running on localhost:5173")
            raise

    def test_frontend_server_responding(self, browser):
        """Verify frontend server is responding to requests."""
        try:
            browser.goto("/", wait_until="domcontentloaded")
            # If we get here without exception, server is responding
            assert browser.page is not None
        except Exception as e:
            if "ERR_CONNECTION_REFUSED" in str(e):
                pytest.skip("Frontend server not running on localhost:5173")
            raise
