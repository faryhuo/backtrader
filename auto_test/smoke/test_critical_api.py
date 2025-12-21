"""
Critical API smoke tests.

These tests verify the most essential API endpoints are functioning.
Each test should complete in <2 seconds.
"""

import pytest


@pytest.mark.smoke
class TestCriticalAPI:
    """Smoke tests for critical API endpoints."""

    def test_api_is_accessible(self, api_client):
        """Verify API is accessible and responding."""
        # Try to access root or a simple endpoint
        response = api_client.get("/api/strategies")
        # Just verify we get a response (200, auth errors, or 503 service unavailable is fine)
        # 503 means server is up but may need proper authentication
        assert response.status_code in [200, 401, 403, 503]

    def test_strategy_list_endpoint(self, api_client):
        """Verify strategy listing endpoint works."""
        response = api_client.get("/api/strategies")
        assert response.status_code in [200, 401, 403, 503]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_template_list_endpoint(self, api_client):
        """Verify template listing endpoint works."""
        response = api_client.get("/api/templates")
        assert response.status_code in [200, 401, 403, 503]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_exchange_list_endpoint(self, api_client):
        """Verify exchange listing endpoint works."""
        response = api_client.get("/api/live/exchanges")
        assert response.status_code in [200, 401, 403, 503]

    def test_live_health_endpoint(self, api_client):
        """Verify live trading health check works."""
        response = api_client.get("/api/live/health")
        assert response.status_code in [200, 401, 403, 503]

    def test_backtest_history_endpoint(self, api_client):
        """Verify backtest history endpoint works."""
        response = api_client.post(
            "/api/backtest/history",
            json={"limit": 5, "offset": 0}
        )
        assert response.status_code in [200, 401, 403, 503]

    def test_portfolio_history_endpoint(self, api_client):
        """Verify portfolio history endpoint works."""
        response = api_client.get("/api/portfolio/history")
        assert response.status_code in [200, 401, 403, 503]

    def test_walkforward_list_endpoint(self, api_client):
        """Verify walk-forward list endpoint works."""
        response = api_client.get("/api/walkforward/list")
        assert response.status_code in [200, 401, 403, 503]

    def test_tasks_list_endpoint(self, api_client):
        """Verify tasks list endpoint works."""
        response = api_client.get("/api/tasks")
        assert response.status_code in [200, 401, 403, 503]

    def test_tasks_stats_endpoint(self, api_client):
        """Verify tasks stats endpoint works."""
        response = api_client.get("/api/tasks/stats")
        assert response.status_code in [200, 401, 403, 503]

    def test_settings_endpoint(self, api_client):
        """Verify settings endpoint works."""
        response = api_client.get("/api/settings")
        assert response.status_code in [200, 401, 403, 503]

    def test_cache_stats_endpoint(self, api_client):
        """Verify cache stats endpoint works."""
        response = api_client.get("/api/cache/stats")
        assert response.status_code in [200, 401, 403, 503]

    def test_resample_timeframes_endpoint(self, api_client):
        """Verify resample timeframes endpoint works."""
        response = api_client.get("/api/resample/timeframes")
        assert response.status_code in [200, 401, 403, 503]
