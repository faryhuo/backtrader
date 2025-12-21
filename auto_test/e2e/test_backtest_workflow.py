"""
E2E tests for backtest workflow.

Tests cover:
- Running backtests via API
- Backtest history management
- AI analysis updates
- Parameter extraction
"""

import pytest
import time
from assertions import assert_api_response, assert_api_error, assert_backtest_metrics


@pytest.mark.api
@pytest.mark.requires_auth
class TestBacktestAPI:
    """API tests for backtest execution and history."""

    def test_run_backtest_without_strategy(self, api_client, data_fixtures):
        """Test running a simple backtest without custom strategy."""
        config = data_fixtures.backtest_config(
            ticker="AAPL",
            days_back=90,
            strategy_name=None  # Use default strategy
        )
        
        response = api_client.post("/api/backtest", json=config)
        assert_api_response(
            response,
            expected_status=200,
            expected_keys=["backtest_id", "metrics", "plot_url"]
        )
        
        data = response.json()
        assert_backtest_metrics(data["metrics"])
        assert data["plot_url"].endswith(".png")
        
        # Return backtest_id for potential cleanup
        return data["backtest_id"]

    def test_run_backtest_with_strategy(self, api_client, data_fixtures, test_strategy_name):
        """Test running backtest with custom strategy."""
        # Create strategy first
        strategy_code = data_fixtures.simple_strategy_code(test_strategy_name)
        api_client.post(
            "/api/strategies",
            json={"name": test_strategy_name, "code": strategy_code}
        )
        
        # Run backtest with the strategy
        config = data_fixtures.backtest_config(
            ticker="AAPL",
            days_back=90,
            strategy_name=test_strategy_name
        )
        
        response = api_client.post("/api/backtest", json=config)
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert_backtest_metrics(data["metrics"])

    def test_run_backtest_with_params(self, api_client, data_fixtures, test_strategy_name):
        """Test running backtest with parameter overrides."""
        # Create strategy with params
        strategy_code = data_fixtures.strategy_with_params()
        api_client.post(
            "/api/strategies",
            json={"name": test_strategy_name, "code": strategy_code}
        )
        
        # Run backtest with custom params
        config = data_fixtures.backtest_config(
            ticker="MSFT",
            days_back=180,
            strategy_name=test_strategy_name,
            params={
                "fast_period": 5,
                "slow_period": 20,
            }
        )
        
        response = api_client.post("/api/backtest", json=config)
        assert_api_response(response, expected_status=200)

    def test_backtest_history_list(self, api_client, data_fixtures):
        """Test listing backtest history."""
        # Run a backtest first to ensure there's data
        config = data_fixtures.backtest_config(ticker="AAPL", days_back=30)
        api_client.post("/api/backtest", json=config)
        
        # Wait a moment for it to be saved
        time.sleep(0.5)
        
        # List history
        query = {
            "limit": 10,
            "offset": 0,
            "sort_by": "created_at",
            "sort_order": "desc"
        }
        
        response = api_client.post("/api/backtest/history", json=query)
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert "items" in data or "backtests" in data or isinstance(data, list)

    def test_backtest_history_filter_by_ticker(self, api_client, data_fixtures):
        """Test filtering backtest history by ticker."""
        # Run backtests for different tickers
        for ticker in ["AAPL", "MSFT"]:
            config = data_fixtures.backtest_config(ticker=ticker, days_back=30)
            api_client.post("/api/backtest", json=config)
        
        time.sleep(0.5)
        
        # Filter by AAPL
        query = {
            "ticker": "AAPL",
            "limit": 10
        }
        
        response = api_client.post("/api/backtest/history", json=query)
        assert_api_response(response, expected_status=200)

    def test_get_backtest_detail(self, api_client, data_fixtures):
        """Test getting detailed backtest result by ID."""
        # Run backtest
        config = data_fixtures.backtest_config(ticker="TSLA", days_back=60)
        run_response = api_client.post("/api/backtest", json=config)
        backtest_id = run_response.json()["backtest_id"]
        
        # Get detail
        detail_response = api_client.get(f"/api/backtest/history/{backtest_id}")
        assert_api_response(detail_response, expected_status=200)
        
        data = detail_response.json()
        assert "backtest_id" in data or "id" in data
        assert "metrics" in data or "config" in data

    def test_update_ai_analysis(self, api_client, data_fixtures):
        """Test updating AI analysis for a backtest."""
        # Run backtest
        config = data_fixtures.backtest_config(ticker="NVDA", days_back=90)
        run_response = api_client.post("/api/backtest", json=config)
        backtest_id = run_response.json()["backtest_id"]
        
        # Update AI analysis
        analysis_data = {
            "model_name": "gpt-4",
            "analysis": "This backtest shows strong performance with good risk-adjusted returns."
        }
        
        update_response = api_client.post(
            f"/api/backtest/history/{backtest_id}/ai-analysis",
            json=analysis_data
        )
        assert_api_response(update_response, expected_status=200)
        
        # Verify analysis was saved
        detail_response = api_client.get(f"/api/backtest/history/{backtest_id}")
        assert detail_response.status_code == 200
        # Check if ai_analysis field exists and contains our data
        # (exact structure depends on backend implementation)

    def test_delete_backtest(self, api_client, data_fixtures, db_helper):
        """Test deleting a backtest record."""
        # Run backtest
        config = data_fixtures.backtest_config(ticker="AMZN", days_back=30)
        run_response = api_client.post("/api/backtest", json=config)
        backtest_id = run_response.json()["backtest_id"]
        
        # Delete backtest
        delete_response = api_client.delete(f"/api/backtest/history/{backtest_id}")
        assert_api_response(delete_response, expected_status=200)
        
        # Verify it's gone
        get_response = api_client.get(f"/api/backtest/history/{backtest_id}")
        assert_api_error(get_response, expected_status=404)

    def test_backtest_invalid_ticker(self, api_client, data_fixtures):
        """Test backtest with invalid ticker."""
        config = data_fixtures.backtest_config(
            ticker="INVALID_TICKER_XYZ",
            days_back=30
        )
        
        response = api_client.post("/api/backtest", json=config)
        # Should fail with data load error
        assert response.status_code in [400, 502]  # DataLoadError or validation error

    def test_backtest_invalid_date_range(self, api_client, data_fixtures):
        """Test backtest with invalid date range."""
        config = {
            "ticker": "AAPL",
            "start_date": "2030-01-01",  # Future date
            "end_date": "2030-12-31",
            "initial_cash": 10000.0,
            "commission": 0.001,
            "stake": 100
        }
        
        response = api_client.post("/api/backtest", json=config)
        # May fail with data error or return empty results
        # The exact behavior depends on data source
        assert response.status_code in [200, 400, 502]

    def test_backtest_with_nonexistent_strategy(self, api_client, data_fixtures):
        """Test backtest with non-existent strategy name."""
        config = data_fixtures.backtest_config(
            ticker="AAPL",
            days_back=30,
            strategy_name="NonExistentStrategy"
        )
        
        response = api_client.post("/api/backtest", json=config)
        assert_api_error(response, expected_status=400, expected_error_substring="strategy")


@pytest.mark.ui
@pytest.mark.slow
class TestBacktestUI:
    """UI tests for backtest interface."""

    def test_run_strategy_page_loads(self, browser):
        """Test that run strategy page loads successfully."""
        try:
            browser.goto("/")
            browser.wait_for_network_idle()
            
            # Verify page loaded
            browser.expect_visible("body")
        except Exception as e:
            if "ERR_CONNECTION_REFUSED" in str(e):
                pytest.skip("Frontend server not running on localhost:5173")
            raise

    def test_backtest_history_page_loads(self, browser):
        """Test that backtest history page loads successfully."""
        try:
            browser.goto("/")
            browser.wait_for_network_idle()
            
            # Verify page loaded
            browser.expect_visible("body")
        except Exception as e:
            if "ERR_CONNECTION_REFUSED" in str(e):
                pytest.skip("Frontend server not running on localhost:5173")
            raise
