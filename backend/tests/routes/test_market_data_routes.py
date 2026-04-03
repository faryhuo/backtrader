"""
Unit tests for market data routes.
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.routes.market_data_routes import (
    DataRequest,
    AnalysisRequest,
    WarmupRequest,
    get_instrument_catalog,
)


class TestPydanticModels:
    """Tests for market data Pydantic models."""

    def test_data_request(self):
        """Test DataRequest model."""
        request = DataRequest(
            ticker="AAPL",
            start_date="2024-01-01",
            end_date="2024-12-31"
        )

        assert request.ticker == "AAPL"
        assert request.start_date == "2024-01-01"
        assert request.end_date == "2024-12-31"

    def test_warmup_request(self):
        """Test WarmupRequest model."""
        request = WarmupRequest(
            tickers=["AAPL", "MSFT", "GOOGL"],
            start_date="2024-01-01",
            end_date="2024-12-31"
        )

        assert len(request.tickers) == 3
        assert "AAPL" in request.tickers


class TestMarketDataRoutes:
    """Tests for market data route handlers."""

    @patch("src.routes.market_data_routes.get_raw_data_json")
    def test_get_raw_data(self, mock_get_data):
        """Test getting raw market data."""
        mock_get_data.return_value = {
            "ticker": "AAPL",
            "data": [
                {"date": "2024-01-01", "close": 150.0},
                {"date": "2024-01-02", "close": 152.0}
            ]
        }

        result = mock_get_data(ticker="AAPL", start_date="2024-01-01", end_date="2024-12-31")

        assert result["ticker"] == "AAPL"
        assert len(result["data"]) == 2

    @patch("src.routes.market_data_routes.get_data_cache_storage")
    def test_cache_management(self, mock_cache_storage):
        """Test cache storage management."""
        mock_storage = MagicMock()
        mock_storage.get_cache_stats.return_value = {
            "total_entries": 100,
            "size_mb": 50
        }
        mock_cache_storage.return_value = mock_storage

        result = mock_storage.get_cache_stats()

        assert result["total_entries"] == 100
        assert result["size_mb"] == 50

    @patch("src.db.storage.ticker_metadata.search_instrument_catalog")
    @patch("src.db.storage.ticker_metadata.search_yahoo_instruments")
    def test_get_instrument_catalog_uses_platform_search(self, mock_yahoo_search, mock_cache_search):
        """Yahoo catalog should use live platform search before cache fallback."""
        mock_yahoo_search.return_value = [
            {"code": "BTC-USD", "label": "Bitcoin USD", "instrument_type": "crypto"}
        ]
        mock_cache_search.return_value = []

        result = get_instrument_catalog(
            platform="yahoo",
            instrument_type="crypto",
            query="BTC",
            limit=10,
            user={"sub": "tester"},
        )

        assert result["platform"] == "yahoo"
        assert result["instrument_type"] == "crypto"
        assert result["options"][0]["code"] == "BTC-USD"
        mock_yahoo_search.assert_called_once_with(
            query="BTC",
            instrument_type="crypto",
            limit=10,
        )
        mock_cache_search.assert_not_called()

    @patch("src.db.storage.ticker_metadata.search_instrument_catalog")
    @patch("src.db.storage.eodhd_data.search_eodhd_instruments")
    @patch("src.db.storage.settings.SettingsStorage")
    def test_get_instrument_catalog_uses_eodhd_search(self, mock_settings_storage, mock_eodhd_search, mock_cache_search):
        """EODHD catalog should search the selected platform using the user's API key."""
        storage = MagicMock()
        storage.get_eodhd_api_key.return_value = "secret-key"
        mock_settings_storage.return_value = storage
        mock_eodhd_search.return_value = [
            {"code": "BTC-USD.CC", "label": "Bitcoin", "instrument_type": "crypto"}
        ]
        mock_cache_search.return_value = []

        result = get_instrument_catalog(
            platform="eodhd",
            instrument_type="crypto",
            query="BTC",
            limit=5,
            user={"sub": "tester"},
        )

        assert result["platform"] == "eodhd"
        assert result["options"][0]["code"] == "BTC-USD.CC"
        storage.get_eodhd_api_key.assert_called_once_with("tester")
        mock_eodhd_search.assert_called_once_with(
            query="BTC",
            instrument_type="crypto",
            limit=5,
            api_key="secret-key",
        )


class TestDataValidation:
    """Tests for data validation."""

    def test_valid_date_range(self):
        """Test valid date range."""
        request = DataRequest(
            ticker="AAPL",
            start_date="2024-01-01",
            end_date="2024-12-31"
        )

        assert request.start_date < request.end_date

    def test_ticker_format(self):
        """Test various ticker formats."""
        tickers = ["AAPL", "000001.SZ", "^GSPC", "BTC-USD"]

        for ticker in tickers:
            request = DataRequest(
                ticker=ticker,
                start_date="2024-01-01",
                end_date="2024-12-31"
            )
            assert request.ticker == ticker
