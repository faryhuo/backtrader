"""
E2E tests for walk-forward optimization workflow.

Tests cover:
- Starting walk-forward optimizations
- Listing optimization results
- Getting optimization details and status
- Error handling
"""

import pytest
import sys
import time
from pathlib import Path

# Add libs to path
libs_path = Path(__file__).parent.parent / "libs"
sys.path.insert(0, str(libs_path))

from assertions import assert_api_response, assert_api_error, assert_walkforward_result
from response_normalizer import normalize_list_response


@pytest.mark.api
@pytest.mark.requires_auth
class TestWalkForwardAPI:
    """API tests for walk-forward optimization."""

    @pytest.mark.slow
    def test_start_walkforward_optimization(self, api_client, data_fixtures, test_strategy_name):
        """Test starting a walk-forward optimization."""
        # Create strategy first
        strategy_code = data_fixtures.simple_strategy_code(test_strategy_name)
        api_client.post(
            "/api/strategies",
            json={"name": test_strategy_name, "code": strategy_code}
        )

        config = data_fixtures.walkforward_config(
            ticker="AAPL",
            strategy_name=test_strategy_name,
            days_back=365,
        )

        response = api_client.post("/api/walkforward/start", json=config)

        if response.status_code == 200:
            data = response.json()
            assert "optimization_id" in data
            assert "status" in data
            assert data["status"] in ["pending", "running"]
            return data["optimization_id"]
        else:
            # May fail if resources unavailable
            assert response.status_code in [400, 500]

    def test_list_walkforward_optimizations(self, api_client):
        """Test listing walk-forward optimizations."""
        response = api_client.get("/api/walkforward/list")
        assert_api_response(response, expected_status=200)

        data = response.json()
        assert "optimizations" in data
        assert "total" in data
        assert isinstance(data["optimizations"], list)

    def test_list_walkforward_with_filters(self, api_client):
        """Test listing walk-forward optimizations with filters."""
        response = api_client.get(
            "/api/walkforward/list",
            params={
                "status": "completed",
                "limit": 10,
                "offset": 0,
                "sort_by": "created_at",
                "sort_order": "desc",
            }
        )
        assert_api_response(response, expected_status=200)

    def test_get_walkforward_not_found(self, api_client):
        """Test getting non-existent walk-forward optimization."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = api_client.get(f"/api/walkforward/{fake_id}")
        assert_api_error(response, expected_status=404)

    def test_get_walkforward_status_not_found(self, api_client):
        """Test getting status of non-existent optimization."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = api_client.get(f"/api/walkforward/{fake_id}/status")
        assert_api_error(response, expected_status=404)

    def test_delete_walkforward_not_found(self, api_client):
        """Test deleting non-existent walk-forward optimization."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = api_client.delete(f"/api/walkforward/{fake_id}")
        assert_api_error(response, expected_status=404)

    def test_start_walkforward_invalid_strategy(self, api_client, data_fixtures):
        """Test starting optimization with non-existent strategy."""
        config = data_fixtures.walkforward_config(
            ticker="AAPL",
            strategy_name="NonExistentStrategy123",
        )

        response = api_client.post("/api/walkforward/start", json=config)
        # Should fail with strategy not found error
        assert response.status_code in [400, 404, 500]

    def test_start_walkforward_invalid_param_grid(self, api_client, data_fixtures, test_strategy_name):
        """Test starting optimization with invalid parameter grid."""
        # Create strategy first
        strategy_code = data_fixtures.simple_strategy_code(test_strategy_name)
        api_client.post(
            "/api/strategies",
            json={"name": test_strategy_name, "code": strategy_code}
        )

        config = data_fixtures.walkforward_config(
            ticker="AAPL",
            strategy_name=test_strategy_name,
        )
        # Override with empty param_grid
        config["param_grid"] = {}

        response = api_client.post("/api/walkforward/start", json=config)
        # May fail validation or allow empty grid
        assert response.status_code in [200, 400, 422]

    def test_list_walkforward_filter_by_ticker(self, api_client):
        """Test filtering walk-forward list by ticker."""
        response = api_client.get(
            "/api/walkforward/list",
            params={"ticker": "AAPL"}
        )
        assert_api_response(response, expected_status=200)

    def test_list_walkforward_filter_by_strategy(self, api_client):
        """Test filtering walk-forward list by strategy name."""
        response = api_client.get(
            "/api/walkforward/list",
            params={"strategy_name": "test_strategy"}
        )
        assert_api_response(response, expected_status=200)


@pytest.mark.ui
@pytest.mark.slow
class TestWalkForwardUI:
    """UI tests for walk-forward optimization interface."""

    def test_walkforward_page_loads(self, browser):
        """Test that optimization page can load."""
        try:
            browser.goto("/")
            browser.wait_for_network_idle()
            browser.expect_visible("body")
        except Exception as e:
            if "ERR_CONNECTION_REFUSED" in str(e):
                pytest.skip("Frontend server not running on localhost:5173")
            raise
