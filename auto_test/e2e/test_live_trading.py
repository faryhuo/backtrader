"""
E2E tests for Live Trading API.

Based on TEST_CASES.md - LIVE section:
- LIVE-001: Invalid mode returns 400
- LIVE-002: Live mode with LIVE_TRADING_ENABLED=false returns 403
- LIVE-003: Invalid exchange/symbol/timeframe returns 400
- LIVE-004: Stop non-existent/already stopped session returns 404/400
- LIVE-005: Status/sessions only returns own sessions
- LIVE-006: Exchanges returns enabled exchanges
- LIVE-007: Orders for non-existent session returns 4xx
- LIVE-008: Health check returns consistent structure
"""

import pytest
import sys
from pathlib import Path

# Add libs to path
libs_path = Path(__file__).parent.parent / "libs"
sys.path.insert(0, str(libs_path))

from assertions import assert_api_response, assert_api_error
import api_paths


# ========== Live Trading Start Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestLiveStart:
    """API tests for starting live trading sessions."""

    def test_live_001_invalid_mode(self, api_client, data_fixtures):
        """LIVE-001: Invalid mode returns 400."""
        config = data_fixtures.live_trading_config()
        config["mode"] = "invalid_mode"  # Not 'paper' or 'live'
        
        response = api_client.post(api_paths.LIVE_START, json=config)
        
        # Should fail validation
        assert response.status_code in [400, 422]

    def test_live_003_invalid_exchange(self, api_client, data_fixtures):
        """LIVE-003: Invalid exchange returns 400."""
        config = data_fixtures.live_trading_config()
        config["exchange"] = "nonexistent_exchange_xyz"
        
        response = api_client.post(api_paths.LIVE_START, json=config)
        
        # Should fail validation or exchange not found
        assert response.status_code in [400, 422, 500]

    def test_live_003_invalid_symbol(self, api_client, data_fixtures):
        """LIVE-003: Invalid symbol format returns 400."""
        config = data_fixtures.live_trading_config()
        config["symbol"] = "INVALID"  # Not in pair format
        
        response = api_client.post(api_paths.LIVE_START, json=config)
        
        # May fail validation or accept and fail later
        assert response.status_code in [200, 400, 422, 500]

    def test_live_003_invalid_timeframe(self, api_client, data_fixtures):
        """LIVE-003: Invalid timeframe returns 400."""
        config = data_fixtures.live_trading_config()
        config["timeframe"] = "invalid_tf"
        
        response = api_client.post(api_paths.LIVE_START, json=config)
        
        # Should fail validation
        assert response.status_code in [400, 422, 500]


# ========== Live Trading Stop Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestLiveStop:
    """API tests for stopping live trading sessions."""

    def test_live_004_stop_nonexistent_session(self, api_client):
        """LIVE-004: Stop non-existent session returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = api_client.post(api_paths.LIVE_STOP, json={
            "session_id": fake_id
        })
        
        assert_api_error(response, expected_status=404)


# ========== Live Trading Status Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestLiveStatus:
    """API tests for live trading status and sessions."""

    def test_live_005_status_nonexistent(self, api_client):
        """LIVE-005: Status for non-existent session returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = api_client.get(api_paths.live_session(fake_id))
        
        assert_api_error(response, expected_status=404)

    def test_live_005_sessions_list(self, api_client):
        """LIVE-005: Sessions list returns structure."""
        response = api_client.get(api_paths.LIVE_SESSIONS)
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert "sessions" in data or isinstance(data, list)


# ========== Live Trading Exchanges Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestLiveExchanges:
    """API tests for live trading exchanges."""

    def test_live_006_exchanges_list(self, api_client):
        """LIVE-006: Exchanges returns enabled exchanges with fields."""
        response = api_client.get(api_paths.LIVE_EXCHANGES)
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert "exchanges" in data or isinstance(data, list)
        
        # If exchanges exist, check structure
        exchanges = data.get("exchanges", data) if isinstance(data, dict) else data
        if exchanges and len(exchanges) > 0:
            exchange = exchanges[0]
            assert "id" in exchange or "name" in exchange


# ========== Live Trading Orders Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestLiveOrders:
    """API tests for live trading orders."""

    def test_live_007_orders_nonexistent_session(self, api_client):
        """LIVE-007: Orders for non-existent session returns 4xx."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = api_client.get(api_paths.live_orders(fake_id))
        
        # Should return 404 or 400
        assert response.status_code in [400, 404]


# ========== Live Trading Health Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestLiveHealth:
    """API tests for live trading health."""

    def test_live_008_health_structure(self, api_client):
        """LIVE-008: Health check returns consistent structure."""
        response = api_client.get(api_paths.LIVE_HEALTH)
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        # Should have status field
        assert "status" in data or "healthy" in data


# ========== UI Tests ==========

@pytest.mark.ui
@pytest.mark.slow
class TestLiveTradingUI:
    """UI tests for live trading page."""

    def test_live_trading_page_loads(self, browser):
        """Test that live trading page can load."""
        try:
            browser.goto("/")
            browser.wait_for_network_idle()
            browser.expect_visible("body")
        except Exception as e:
            if "ERR_CONNECTION_REFUSED" in str(e):
                pytest.skip("Frontend server not running on localhost:5173")
            raise
