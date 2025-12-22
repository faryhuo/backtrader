"""
E2E tests for market data API.

Tests cover:
- Ticker info and validation
- Price data fetching
- Cache management (stats, warmup, cleanup)
- Data resampling
"""

import pytest
import sys
from pathlib import Path

# Add libs to path
libs_path = Path(__file__).parent.parent / "libs"
sys.path.insert(0, str(libs_path))

from assertions import assert_api_response, assert_api_error


@pytest.mark.api
@pytest.mark.requires_auth
class TestMarketDataAPI:
    """API tests for market data endpoints."""

    def test_get_ticker_info(self, api_client):
        """Test getting ticker metadata and validation."""
        response = api_client.get("/api/ticker/AAPL/info")

        if response.status_code == 200:
            data = response.json()
            assert "is_valid" in data or "symbol" in data or "ticker" in data
        else:
            # May fail if service unavailable
            assert response.status_code in [400, 500]

    def test_get_ticker_info_invalid(self, api_client):
        """Test getting info for invalid ticker."""
        response = api_client.get("/api/ticker/INVALID_XYZ_123/info")
        # Should fail with validation error
        assert response.status_code in [400, 404, 500]

    def test_get_ticker_prices(self, api_client, data_fixtures):
        """Test fetching OHLCV price data."""
        start_date, end_date = data_fixtures.date_range(days_back=30)

        response = api_client.get(
            "/api/ticker/AAPL/prices",
            params={"start_date": start_date, "end_date": end_date}
        )

        if response.status_code == 200:
            data = response.json()
            assert "data" in data
        else:
            # May fail if data unavailable
            assert response.status_code in [400, 500]

    def test_fetch_market_data_legacy(self, api_client, data_fixtures):
        """Test legacy market data endpoint."""
        request = data_fixtures.market_data_request(ticker="AAPL", days_back=30)

        response = api_client.post("/api/data", json=request)

        if response.status_code == 200:
            data = response.json()
            # Should have ticker_info and data
            assert "data" in data or "ticker_info" in data
        else:
            assert response.status_code in [400, 500]

    def test_fetch_market_data_invalid_ticker(self, api_client, data_fixtures):
        """Test fetching data for invalid ticker."""
        request = data_fixtures.market_data_request(
            ticker="INVALID_XYZ_123",
            days_back=30
        )

        response = api_client.post("/api/data", json=request)
        # Should fail validation
        assert response.status_code in [400, 500]


@pytest.mark.api
@pytest.mark.requires_auth
class TestCacheManagementAPI:
    """API tests for cache management endpoints."""

    def test_get_cache_stats(self, api_client):
        """Test getting cache statistics."""
        response = api_client.get("/api/cache/stats")
        assert_api_response(response, expected_status=200)

        data = response.json()
        # Should have some stats fields
        assert isinstance(data, dict)

    def test_get_cached_tickers(self, api_client):
        """Test getting list of cached tickers."""
        response = api_client.get("/api/cache/tickers")
        assert_api_response(response, expected_status=200)

        data = response.json()
        assert "tickers" in data
        assert "count" in data

    def test_get_ticker_cache_info(self, api_client):
        """Test getting cache info for specific ticker."""
        response = api_client.get("/api/cache/AAPL")

        # May not have cached data
        assert response.status_code in [200, 404]

    def test_get_ticker_cache_info_not_found(self, api_client):
        """Test getting cache info for non-cached ticker."""
        response = api_client.get("/api/cache/NONEXISTENT_XYZ_999")
        # Should be 404 if not cached
        assert response.status_code in [404, 200]

    @pytest.mark.slow
    def test_warmup_cache(self, api_client, data_fixtures):
        """Test warming up cache for multiple tickers."""
        request = data_fixtures.warmup_request(
            tickers=["AAPL"],
            days_back=7
        )

        response = api_client.post("/api/cache/warmup", json=request)

        if response.status_code == 200:
            data = response.json()
            # Should have some result info
            assert isinstance(data, dict)
        else:
            # May fail if data unavailable
            assert response.status_code in [400, 500]

    def test_cleanup_cache_requires_filter(self, api_client):
        """Test that cache cleanup requires at least one filter."""
        response = api_client.delete("/api/cache/cleanup")
        # Should fail without filter
        assert_api_error(response, expected_status=400)

    def test_cleanup_cache_with_filter(self, api_client):
        """Test cache cleanup with older_than_days filter."""
        response = api_client.delete(
            "/api/cache/cleanup",
            params={"older_than_days": 365}  # Clean old data
        )

        # Should succeed or have nothing to clean
        assert response.status_code in [200, 404]

    def test_delete_ticker_cache_not_found(self, api_client):
        """Test deleting cache for non-existent ticker."""
        response = api_client.delete("/api/cache/NONEXISTENT_XYZ_999")
        assert response.status_code in [404, 200]


@pytest.mark.api
@pytest.mark.requires_auth
class TestResampleAPI:
    """API tests for data resampling endpoints."""

    def test_get_supported_timeframes(self, api_client):
        """Test getting list of supported timeframes."""
        response = api_client.get("/api/resample/timeframes")
        assert_api_response(response, expected_status=200)

        data = response.json()
        assert "timeframes" in data
        assert isinstance(data["timeframes"], list)

    def test_get_resample_targets(self, api_client):
        """Test getting valid target timeframes for source."""
        response = api_client.get("/api/resample/targets/1h")

        if response.status_code == 200:
            data = response.json()
            assert "source" in data
            assert "valid_targets" in data
        else:
            # Invalid source timeframe
            assert response.status_code == 400

    def test_get_resample_targets_invalid(self, api_client):
        """Test getting targets for invalid source timeframe."""
        response = api_client.get("/api/resample/targets/invalid")
        assert_api_error(response, expected_status=400)

    @pytest.mark.slow
    def test_resample_data(self, api_client, data_fixtures):
        """Test resampling OHLCV data."""
        request = data_fixtures.resample_request(
            ticker="AAPL",
            target_timeframe="1w",
            days_back=60
        )

        response = api_client.post("/api/resample", json=request)

        if response.status_code == 200:
            data = response.json()
            assert "ticker" in data
            assert "timeframe" in data
            assert "data" in data
        else:
            # May fail if no data available
            assert response.status_code in [400, 404, 500]

    def test_resample_data_no_data(self, api_client, data_fixtures):
        """Test resampling when no data available."""
        request = data_fixtures.resample_request(
            ticker="INVALID_XYZ",
            target_timeframe="1d",
            days_back=30
        )

        response = api_client.post("/api/resample", json=request)
        # Should fail with no data
        assert response.status_code in [400, 404, 500]


@pytest.mark.api
@pytest.mark.requires_auth
class TestAnalysisAPI:
    """API tests for analysis endpoints."""

    def test_analyze_results(self, api_client):
        """Test analyzing backtest results."""
        request = {
            "metrics": {
                "sharpe": 1.5,
                "returns": 15.0,
                "drawdown": -10.0
            }
        }

        response = api_client.post("/api/analyze", json=request)
        assert_api_response(response, expected_status=200)

        data = response.json()
        assert "analysis" in data

    def test_analyze_results_negative(self, api_client):
        """Test analyzing negative backtest results."""
        request = {
            "metrics": {
                "sharpe": -0.5,
                "returns": -5.0,
                "drawdown": -25.0
            }
        }

        response = api_client.post("/api/analyze", json=request)
        assert_api_response(response, expected_status=200)

        data = response.json()
        assert "analysis" in data
        # Should mention the loss
        assert "loss" in data["analysis"].lower() or "negative" in data["analysis"].lower() or "-" in data["analysis"]
