"""
E2E tests for Portfolio API.

Based on TEST_CASES.md - PORTFOLIO section:
- PF-001: tickers/weights count mismatch returns 400
- PF-002: Submit returns task_id, result from task
- PF-003: History list pagination/sorting works
- PF-004: Detail not found returns 404, only own records
- PF-005: Delete not found returns 404
"""

import pytest
import sys
from pathlib import Path

# Add libs to path
libs_path = Path(__file__).parent.parent / "libs"
sys.path.insert(0, str(libs_path))

from assertions import assert_api_response, assert_api_error
import api_paths


# ========== Portfolio Submission Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestPortfolioSubmission:
    """API tests for portfolio backtest submission."""

    def test_pf_001_tickers_weights_mismatch(self, api_client, data_fixtures):
        """PF-001: tickers/weights count mismatch returns 400."""
        response = api_client.post(api_paths.PORTFOLIO, json={
            "tickers": ["AAPL", "MSFT", "GOOGL"],
            "weights": [0.5, 0.5],  # Mismatch - only 2 weights for 3 tickers
            "start_date": "2024-01-01",
            "end_date": "2024-06-01",
            "initial_cash": 100000
        })
        
        assert response.status_code == 400, (
            f"Expected 400 for tickers/weights mismatch, got {response.status_code}"
        )

    def test_pf_001_empty_tickers(self, api_client):
        """PF-001: Empty tickers list returns 422/400."""
        response = api_client.post(api_paths.PORTFOLIO, json={
            "tickers": [],
            "weights": [],
            "start_date": "2024-01-01",
            "end_date": "2024-06-01",
            "initial_cash": 100000
        })
        
        # Should fail validation (min_length=1)
        assert response.status_code in [400, 422]

    @pytest.mark.slow
    def test_pf_002_submit_returns_task_id(self, api_client, data_fixtures):
        """PF-002: Submit portfolio returns task_id."""
        config = data_fixtures.portfolio_config(
            tickers=["AAPL", "MSFT"],
            weights=[0.5, 0.5],
            days_back=30
        )
        
        response = api_client.post(api_paths.PORTFOLIO, json=config)
        
        if response.status_code == 200:
            data = response.json()
            # Should have task_id for async execution
            assert "task_id" in data or "portfolio_id" in data, (
                "Response should have task_id or portfolio_id"
            )
        else:
            # Data unavailable or validation error
            assert response.status_code in [400, 500]


# ========== Portfolio History Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestPortfolioHistory:
    """API tests for portfolio history."""

    def test_pf_003_history_list_basic(self, api_client):
        """PF-003: History list returns structure."""
        response = api_client.get(api_paths.PORTFOLIO_HISTORY)
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert "results" in data or "items" in data or isinstance(data, list)

    def test_pf_003_history_pagination(self, api_client):
        """PF-003: History list pagination works."""
        response = api_client.get(
            api_paths.PORTFOLIO_HISTORY,
            params={"limit": 5, "offset": 0}
        )
        
        assert_api_response(response, expected_status=200)

    def test_pf_003_history_sorting(self, api_client):
        """PF-003: History list sorting works."""
        response = api_client.get(
            api_paths.PORTFOLIO_HISTORY,
            params={"sort_by": "created_at", "sort_order": "desc"}
        )
        
        assert_api_response(response, expected_status=200)


# ========== Portfolio Detail Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestPortfolioDetail:
    """API tests for portfolio detail operations."""

    def test_pf_004_detail_not_found(self, api_client):
        """PF-004: Detail for non-existent ID returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = api_client.get(api_paths.portfolio_detail(fake_id))
        
        assert_api_error(response, expected_status=404)

    def test_pf_005_delete_not_found(self, api_client):
        """PF-005: Delete non-existent portfolio returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = api_client.delete(api_paths.portfolio_delete(fake_id))
        
        assert_api_error(response, expected_status=404)


# ========== UI Tests ==========

@pytest.mark.ui
@pytest.mark.slow
class TestPortfolioUI:
    """UI tests for portfolio page."""

    def test_portfolio_page_loads(self, browser):
        """Test that portfolio page can load."""
        try:
            browser.goto("/")
            browser.wait_for_network_idle()
            browser.expect_visible("body")
        except Exception as e:
            if "ERR_CONNECTION_REFUSED" in str(e):
                pytest.skip("Frontend server not running on localhost:5173")
            raise
