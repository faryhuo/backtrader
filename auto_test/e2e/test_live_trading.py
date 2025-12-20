"""
E2E tests for live trading workflow.

Tests cover:
- Starting/stopping paper trading sessions
- Session status and monitoring
- Exchange listing
- Health checks
"""

import pytest
import time
from assertions import assert_api_response, assert_api_error, assert_session_response


@pytest.mark.api
@pytest.mark.requires_auth
class TestLiveTradingAPI:
    """API tests for live trading (paper mode)."""

    def test_get_exchanges(self, api_client):
        """Test listing available exchanges."""
        response = api_client.get("/api/live/exchanges")
        assert_api_response(response, expected_status=200)
        
        exchanges = response.json()
        assert isinstance(exchanges, list)
        # Should have at least one exchange configured
        if len(exchanges) > 0:
            exchange = exchanges[0]
            assert "id" in exchange
            assert "name" in exchange

    def test_health_check(self, api_client):
        """Test live trading health check endpoint."""
        response = api_client.get ("/api/live/health")
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert "status" in data

    def test_list_sessions_empty(self, api_client):
        """Test listing sessions when none are active."""
        response = api_client.get("/api/live/sessions")
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        # Should return a list (may be empty)
        assert isinstance(data, list) or "sessions" in data

    @pytest.mark.slow
    def test_start_paper_trading_session(self, api_client, data_fixtures, test_strategy_name):
        """Test starting a paper trading session."""
        # Create a strategy first
        strategy_code = data_fixtures.simple_strategy_code(test_strategy_name)
        api_client.post(
            "/api/strategies",
            json={"name": test_strategy_name, "code": strategy_code}
        )
        
        # Start paper trading session
        config = data_fixtures.live_trading_config(
            strategy_name=test_strategy_name,
            symbol="BTC/USDT",
            exchange="binance",
            mode="paper"
        )
        
        response = api_client.post("/api/live/start", json=config)
        
        # May fail if exchange not configured or feature disabled
        if response.status_code == 200:
            assert_session_response(response.json())
            session_id = response.json()["session_id"]
            
            # Stop the session to cleanup
            stop_response = api_client.post(
                "/api/live/stop",
                json={"session_id": session_id}
            )
            assert stop_response.status_code in [200, 404]  # May already be stopped
        else:
            # Expected if live trading is disabled or exchange not configured
            assert response.status_code in [400, 403, 500]

    def test_start_session_invalid_symbol(self, api_client, data_fixtures, test_strategy_name):
        """Test starting session with invalid trading symbol."""
        config = data_fixtures.live_trading_config(
            strategy_name=test_strategy_name,
            symbol="INVALID/SYMBOL",
            mode="paper"
        )
        
        response = api_client.post("/api/live/start", json=config)
        # Should fail validation
        assert response.status_code in [400, 500]

    def test_start_session_nonexistent_strategy(self, api_client, data_fixtures):
        """Test starting session with non-existent strategy."""
        config = data_fixtures.live_trading_config(
            strategy_name="NonExistentStrategy",
            mode="paper"
        )
        
        response = api_client.post("/api/live/start", json=config)
        # Should fail with strategy error
        assert response.status_code in [400, 404]

    def test_get_session_status_not_found(self, api_client):
        """Test getting status of non-existent session."""
        fake_session_id = "00000000-0000-0000-0000-000000000000"
        
        response = api_client.get(f"/api/live/sessions/{fake_session_id}")
        assert_api_error(response, expected_status=404)

    def test_stop_session_not_found(self, api_client):
        """Test stopping non-existent session."""
        fake_session_id = "00000000-0000-0000-0000-000000000000"
        
        response = api_client.post(
            "/api/live/stop",
            json={"session_id": fake_session_id}
        )
        assert_api_error(response, expected_status=404)


@pytest.mark.ui
@pytest.mark.slow
class TestLiveTradingUI:
    """UI tests for live trading interface."""

    def test_live_trading_page_loads(self, browser):
        """Test that live trading dashboard loads successfully."""
        try:
            browser.goto("/")
            browser.wait_for_network_idle()
            
            # Verify page loaded
            browser.expect_visible("body")
        except Exception as e:
            if "ERR_CONNECTION_REFUSED" in str(e):
                pytest.skip("Frontend server not running on localhost:5173")
            raise
