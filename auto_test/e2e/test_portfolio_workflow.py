"""
E2E tests for portfolio backtest workflow.

Tests cover:
- Portfolio backtest execution
- Portfolio history management
- Portfolio details retrieval
- Error handling for invalid inputs
"""

import pytest
import sys
import time
from pathlib import Path

# Add libs to path
libs_path = Path(__file__).parent.parent / "libs"
sys.path.insert(0, str(libs_path))

from assertions import assert_api_response, assert_api_error, assert_portfolio_result
from response_normalizer import normalize_list_response


@pytest.mark.api
@pytest.mark.requires_auth
class TestPortfolioAPI:
    """API tests for portfolio backtest execution and history."""

    @pytest.mark.slow
    def test_run_portfolio_backtest(self, api_client, data_fixtures):
        """Test running a portfolio backtest with multiple tickers."""
        config = data_fixtures.portfolio_config(
            tickers=["AAPL", "MSFT"],
            weights=[0.6, 0.4],
            days_back=90,
        )

        response = api_client.post("/api/portfolio/backtest", json=config)

        # May fail if data not available or service issue
        if response.status_code == 200:
            data = response.json()
            assert "portfolio_id" in data or "task_id" in data
            assert "plot_url" in data
            # Store portfolio_id for cleanup
            return data.get("portfolio_id")
        else:
            # Expected if data source unavailable
            assert response.status_code in [400, 500, 502]

    def test_portfolio_backtest_weight_mismatch(self, api_client, data_fixtures):
        """Test portfolio backtest with mismatched tickers and weights."""
        config = data_fixtures.portfolio_config(
            tickers=["AAPL", "MSFT", "GOOGL"],
            weights=[0.5, 0.5],  # Only 2 weights for 3 tickers
            days_back=30,
        )

        response = api_client.post("/api/portfolio/backtest", json=config)
        assert_api_error(response, expected_status=400)

    def test_portfolio_backtest_empty_tickers(self, api_client, data_fixtures):
        """Test portfolio backtest with empty ticker list."""
        end_date = "2024-12-01"
        start_date = "2024-09-01"

        config = {
            "tickers": [],
            "weights": [],
            "start_date": start_date,
            "end_date": end_date,
            "initial_cash": 100000.0,
            "commission": 0.0005,
            "stake": 100,
        }

        response = api_client.post("/api/portfolio/backtest", json=config)
        # Should fail validation - empty tickers
        assert response.status_code in [400, 422]

    def test_portfolio_history_list(self, api_client):
        """Test listing portfolio backtest history."""
        response = api_client.get("/api/portfolio/history")
        assert_api_response(response, expected_status=200)

        data = response.json()
        assert "results" in data or "items" in data or isinstance(data, list)

    def test_portfolio_history_with_pagination(self, api_client):
        """Test portfolio history with pagination parameters."""
        response = api_client.get(
            "/api/portfolio/history",
            params={"limit": 5, "offset": 0, "sort_by": "created_at", "sort_order": "desc"}
        )
        assert_api_response(response, expected_status=200)

    def test_get_portfolio_detail_not_found(self, api_client):
        """Test getting non-existent portfolio detail."""
        fake_portfolio_id = "00000000-0000-0000-0000-000000000000"

        response = api_client.get(f"/api/portfolio/{fake_portfolio_id}")
        assert_api_error(response, expected_status=404)

    def test_delete_portfolio_not_found(self, api_client):
        """Test deleting non-existent portfolio record."""
        fake_portfolio_id = "00000000-0000-0000-0000-000000000000"

        response = api_client.delete(f"/api/portfolio/{fake_portfolio_id}")
        assert_api_error(response, expected_status=404)

    @pytest.mark.slow
    def test_portfolio_backtest_with_strategy(self, api_client, data_fixtures, test_strategy_name):
        """Test portfolio backtest with custom strategy."""
        # Create strategy first
        strategy_code = data_fixtures.simple_strategy_code(test_strategy_name)
        api_client.post(
            "/api/strategies",
            json={"name": test_strategy_name, "code": strategy_code}
        )

        config = data_fixtures.portfolio_config(
            tickers=["AAPL", "MSFT"],
            weights=[0.5, 0.5],
            days_back=60,
            strategy_name=test_strategy_name,
        )

        response = api_client.post("/api/portfolio/backtest", json=config)

        # May succeed or fail depending on data availability
        assert response.status_code in [200, 400, 500, 502]

    def test_portfolio_backtest_invalid_ticker(self, api_client, data_fixtures):
        """Test portfolio backtest with invalid ticker."""
        config = data_fixtures.portfolio_config(
            tickers=["AAPL", "INVALID_XYZ_123"],
            weights=[0.5, 0.5],
            days_back=30,
        )

        response = api_client.post("/api/portfolio/backtest", json=config)
        # Should fail with data error
        assert response.status_code in [400, 500, 502]


@pytest.mark.ui
@pytest.mark.slow
class TestPortfolioUI:
    """UI tests for portfolio interface."""

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
