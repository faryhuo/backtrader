"""
Unit tests for EODHD data module.
"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from src.db.storage.eodhd_data import (
    EODHDError,
    fetch_from_eodhd,
)


class TestEODHDError:
    """Tests for EODHDError exception."""

    def test_eodhd_error_message(self):
        """Test that EODHDError can be raised with a message."""
        with pytest.raises(EODHDError) as excinfo:
            raise EODHDError("API request failed")
        assert "API request failed" in str(excinfo.value)

    def test_eodhd_error_inheritance(self):
        """Test that EODHDError inherits from Exception."""
        assert issubclass(EODHDError, Exception)


class TestFetchFromEodhd:
    """Tests for fetch_from_eodhd function."""

    def test_fetch_without_api_key(self):
        """Test that fetch returns None when API key is empty."""
        result = fetch_from_eodhd(
            ticker="AAPL",
            start="2024-01-01",
            end="2024-12-31",
            api_key="",
        )
        assert result is None

    def test_fetch_without_api_key_none(self):
        """Test that fetch returns None when API key is None."""
        result = fetch_from_eodhd(
            ticker="AAPL",
            start="2024-01-01",
            end="2024-12-31",
            api_key=None,
        )
        assert result is None

    @patch("src.db.storage.eodhd_data.requests.get")
    def test_fetch_success(self, mock_get):
        """Test successful data fetch from EODHD."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "date": "2024-01-02",
                "open": 100.0,
                "high": 102.0,
                "low": 99.0,
                "close": 101.0,
                "adjusted_close": 101.0,
                "volume": 1000000,
            },
            {
                "date": "2024-01-03",
                "open": 101.0,
                "high": 103.0,
                "low": 100.0,
                "close": 102.0,
                "adjusted_close": 102.0,
                "volume": 1100000,
            },
        ]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_from_eodhd(
            ticker="AAPL",
            start="2024-01-01",
            end="2024-01-31",
            api_key="test_api_key",
        )

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "Open" in result.columns
        assert "Close" in result.columns
        assert "Volume" in result.columns

    @patch("src.db.storage.eodhd_data.requests.get")
    def test_fetch_adds_us_suffix(self, mock_get):
        """Test that US suffix is added to tickers without exchange."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        fetch_from_eodhd(
            ticker="AAPL",
            start="2024-01-01",
            end="2024-01-31",
            api_key="test_api_key",
        )

        # Verify the URL contains AAPL.US
        call_args = mock_get.call_args
        assert "AAPL.US" in call_args[0][0]

    @patch("src.db.storage.eodhd_data.requests.get")
    def test_fetch_preserves_exchange_suffix(self, mock_get):
        """Test that existing exchange suffix is preserved."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        fetch_from_eodhd(
            ticker="BP.LSE",
            start="2024-01-01",
            end="2024-01-31",
            api_key="test_api_key",
        )

        # Verify the URL contains BP.LSE (not BP.LSE.US)
        call_args = mock_get.call_args
        assert "BP.LSE" in call_args[0][0]
        assert "BP.LSE.US" not in call_args[0][0]

    @patch("src.db.storage.eodhd_data.requests.get")
    def test_fetch_empty_response(self, mock_get):
        """Test handling of empty response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_from_eodhd(
            ticker="AAPL",
            start="2024-01-01",
            end="2024-01-31",
            api_key="test_api_key",
        )

        assert result is None

    @patch("src.db.storage.eodhd_data.requests.get")
    def test_fetch_error_response(self, mock_get):
        """Test handling of error response from API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "Invalid ticker"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_from_eodhd(
            ticker="INVALID",
            start="2024-01-01",
            end="2024-01-31",
            api_key="test_api_key",
        )

        assert result is None

    @patch("src.db.storage.eodhd_data.requests.get")
    def test_fetch_timeout(self, mock_get):
        """Test handling of request timeout."""
        import requests.exceptions
        mock_get.side_effect = requests.exceptions.Timeout()

        result = fetch_from_eodhd(
            ticker="AAPL",
            start="2024-01-01",
            end="2024-01-31",
            api_key="test_api_key",
        )

        assert result is None

    @patch("src.db.storage.eodhd_data.requests.get")
    def test_fetch_request_exception(self, mock_get):
        """Test handling of request exception."""
        import requests.exceptions
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        result = fetch_from_eodhd(
            ticker="AAPL",
            start="2024-01-01",
            end="2024-01-31",
            api_key="test_api_key",
        )

        assert result is None
