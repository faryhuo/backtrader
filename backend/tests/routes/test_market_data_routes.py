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
