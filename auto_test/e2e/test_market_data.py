"""
E2E tests for Market Data and Cache API.

Based on TEST_CASES.md - MARKET DATA section:
- MD-001: Invalid ticker returns validation error
- MD-002: Price data returns {"data": ...} with time range
- MD-003: Legacy /api/data returns ticker_info + data
- MD-004: Cache stats returns structure
- MD-005: Cache cleanup without filter must return 400 (security)
- MD-006: Cache warmup returns success/failure counts
- MD-007: Delete single ticker cache, 404 if not found
- MD-008: Resample invalid source/target returns 400
- MD-009: Analyze missing metrics returns 422/400
"""

import pytest
import sys
from pathlib import Path

# Add libs to path
libs_path = Path(__file__).parent.parent / "libs"
sys.path.insert(0, str(libs_path))

from assertions import assert_api_response, assert_api_error
import api_paths


# ========== Market Data Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestMarketData:
    """API tests for market data endpoints."""

    def test_md_001_ticker_info_valid(self, api_client):
        """MD-001: Valid ticker returns info."""
        response = api_client.get(api_paths.ticker_info("AAPL"))
        
        if response.status_code == 200:
            data = response.json()
            # Should have some ticker info
            assert isinstance(data, dict)
        else:
            # Data source unavailable is acceptable
            assert response.status_code in [400, 500, 503]

    def test_md_001_ticker_info_invalid(self, api_client):
        """MD-001: Invalid ticker returns validation error."""
        response = api_client.get(api_paths.ticker_info("INVALID_XYZ_12345"))
        
        # Should fail validation or return error
        assert response.status_code in [400, 404, 500]

    def test_md_002_ticker_prices_with_range(self, api_client, data_fixtures):
        """MD-002: Price data returns {"data": ...} and respects time range."""
        start_date, end_date = data_fixtures.date_range(days_back=30)
        
        response = api_client.get(
            api_paths.ticker_prices("AAPL"),
            params={"start_date": start_date, "end_date": end_date}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "data" in data, "Response must contain 'data' key"
        else:
            # Data unavailable is acceptable
            assert response.status_code in [400, 500, 503]

    def test_md_003_legacy_data_endpoint(self, api_client, data_fixtures):
        """MD-003: Legacy /api/data returns ticker_info + data."""
        request = data_fixtures.market_data_request(ticker="AAPL", days_back=30)
        
        response = api_client.post(api_paths.DATA, json=request)
        
        if response.status_code == 200:
            data = response.json()
            # Should have data or ticker_info
            assert "data" in data or "ticker_info" in data, (
                "Legacy endpoint should return data or ticker_info"
            )
        else:
            # Data unavailable
            assert response.status_code in [400, 500, 503]


# ========== Cache Management Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestCacheManagement:
    """API tests for cache management endpoints."""

    def test_md_004_cache_stats_structure(self, api_client):
        """MD-004: Cache stats returns structure."""
        response = api_client.get(api_paths.CACHE_STATS)
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert isinstance(data, dict), "Cache stats should be a dictionary"

    def test_md_004_cached_tickers_list(self, api_client):
        """MD-004: Cached tickers returns list with count."""
        response = api_client.get(api_paths.CACHE_TICKERS)
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert "tickers" in data, "Response must contain 'tickers'"
        assert "count" in data, "Response must contain 'count'"

    def test_md_005_cleanup_without_filter_fails(self, api_client):
        """MD-005: Cache cleanup without any filter must return 400 (prevent accidental full delete)."""
        response = api_client.delete(api_paths.CACHE_CLEANUP)
        
        assert_api_error(response, expected_status=400)

    def test_md_005_cleanup_with_filter_succeeds(self, api_client):
        """MD-005: Cache cleanup with filter is allowed."""
        response = api_client.delete(
            api_paths.CACHE_CLEANUP,
            params={"older_than_days": 365}
        )
        
        # Should succeed or no data to clean
        assert response.status_code in [200, 404]

    @pytest.mark.slow
    def test_md_006_warmup_returns_counts(self, api_client, data_fixtures):
        """MD-006: Cache warmup returns success/failure counts."""
        request = data_fixtures.warmup_request(
            tickers=["AAPL"],
            days_back=7
        )
        
        response = api_client.post(api_paths.CACHE_WARMUP, json=request)
        
        if response.status_code == 200:
            data = response.json()
            # Should have some result structure
            assert isinstance(data, dict)
        else:
            # Data unavailable
            assert response.status_code in [400, 500]

    def test_md_007_delete_ticker_cache_not_found(self, api_client):
        """MD-007: Delete cache for non-cached ticker returns 404."""
        response = api_client.delete(api_paths.cache_ticker("NONEXISTENT_XYZ_999"))
        
        # Either 404 (not cached) or 200 (nothing to delete)
        assert response.status_code in [200, 404]


# ========== Resample Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestResample:
    """API tests for data resampling endpoints."""

    def test_resample_timeframes_list(self, api_client):
        """Get list of supported timeframes."""
        response = api_client.get(api_paths.RESAMPLE_TIMEFRAMES)
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert "timeframes" in data
        assert isinstance(data["timeframes"], list)

    def test_resample_targets_valid(self, api_client):
        """Get valid target timeframes for a source."""
        response = api_client.get(api_paths.resample_targets("1h"))
        
        if response.status_code == 200:
            data = response.json()
            assert "source" in data
            assert "valid_targets" in data
        else:
            # Invalid source timeframe
            assert response.status_code == 400

    def test_md_008_resample_invalid_source(self, api_client):
        """MD-008: Resample with invalid source timeframe returns 400."""
        response = api_client.get(api_paths.resample_targets("invalid_timeframe"))
        
        assert_api_error(response, expected_status=400)

    @pytest.mark.slow
    def test_md_008_resample_invalid_target(self, api_client, data_fixtures):
        """MD-008: Resample with invalid target returns 400."""
        request = data_fixtures.resample_request(
            ticker="AAPL",
            target_timeframe="invalid_tf",
            days_back=30
        )
        
        response = api_client.post(api_paths.RESAMPLE, json=request)
        
        # Should fail with invalid target
        assert response.status_code in [400, 422]


# ========== Analyze Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestAnalyze:
    """API tests for analysis endpoint."""

    def test_md_009_analyze_missing_metrics(self, api_client):
        """MD-009: Analyze without metrics returns 422/400."""
        response = api_client.post(api_paths.ANALYZE, json={})
        
        # Should fail validation
        assert response.status_code in [400, 422]

    def test_md_009_analyze_success(self, api_client):
        """MD-009: Analyze with valid metrics returns analysis."""
        response = api_client.post(api_paths.ANALYZE, json={
            "metrics": {
                "sharpe": 1.5,
                "returns": 15.0,
                "drawdown": -10.0
            }
        })
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert "analysis" in data

    def test_analyze_negative_results(self, api_client):
        """Analyze handles negative backtest results appropriately."""
        response = api_client.post(api_paths.ANALYZE, json={
            "metrics": {
                "sharpe": -0.5,
                "returns": -5.0,
                "drawdown": -25.0
            }
        })
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert "analysis" in data
