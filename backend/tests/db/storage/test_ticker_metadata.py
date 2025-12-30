"""
Unit tests for ticker metadata module.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestTickerMetadataImports:
    """Tests for ticker metadata module imports."""

    def test_module_import(self):
        """Test that ticker metadata module can be imported."""
        from src.db.storage import ticker_metadata
        assert ticker_metadata is not None

    def test_validate_ticker_info_import(self):
        """Test that _validate_ticker_info function can be imported."""
        from src.db.storage.ticker_metadata import _validate_ticker_info
        assert _validate_ticker_info is not None

    def test_parse_ticker_info_import(self):
        """Test that _parse_ticker_info function can be imported."""
        from src.db.storage.ticker_metadata import _parse_ticker_info
        assert _parse_ticker_info is not None

    def test_get_ticker_metadata_import(self):
        """Test that get_ticker_metadata function can be imported."""
        from src.db.storage.ticker_metadata import get_ticker_metadata
        assert get_ticker_metadata is not None


class TestValidateTickerInfo:
    """Tests for _validate_ticker_info function."""

    def test_validate_empty_info(self):
        """Test validation of empty info dict."""
        from src.db.storage.ticker_metadata import _validate_ticker_info
        is_valid, error = _validate_ticker_info({})
        assert is_valid is False
        assert error is not None

    def test_validate_valid_info(self):
        """Test validation of valid ticker info."""
        from src.db.storage.ticker_metadata import _validate_ticker_info
        info = {
            "longName": "Apple Inc.",
            "symbol": "AAPL",
            "currentPrice": 150.0,
        }
        is_valid, error = _validate_ticker_info(info)
        assert is_valid is True
        assert error is None

    def test_validate_info_with_short_name(self):
        """Test validation with shortName instead of longName."""
        from src.db.storage.ticker_metadata import _validate_ticker_info
        info = {
            "shortName": "Apple",
            "regularMarketPrice": 150.0,
        }
        is_valid, error = _validate_ticker_info(info)
        assert is_valid is True

    def test_validate_info_with_previous_close(self):
        """Test validation with previousClose price."""
        from src.db.storage.ticker_metadata import _validate_ticker_info
        info = {
            "symbol": "AAPL",
            "previousClose": 149.0,
        }
        is_valid, error = _validate_ticker_info(info)
        assert is_valid is True

    def test_validate_info_missing_price(self):
        """Test validation when price fields are missing."""
        from src.db.storage.ticker_metadata import _validate_ticker_info
        info = {
            "longName": "Apple Inc.",
            "symbol": "AAPL",
        }
        is_valid, error = _validate_ticker_info(info)
        assert is_valid is False


class TestParseTickerInfo:
    """Tests for _parse_ticker_info function."""

    def test_parse_valid_info(self):
        """Test parsing valid ticker info."""
        from src.db.storage.ticker_metadata import _parse_ticker_info
        info = {
            "longName": "Apple Inc.",
            "symbol": "AAPL",
            "currentPrice": 150.0,
            "currency": "USD",
            "marketCap": 2500000000000,
            "sector": "Technology",
            "industry": "Consumer Electronics",
        }
        result = _parse_ticker_info("AAPL", info, True, None)
        
        assert result["ticker"] == "AAPL"
        assert result["is_valid"] is True
        # Check the actual field names returned by the function
        assert "long_name" in result or "name" in result

    def test_parse_invalid_info(self):
        """Test parsing invalid ticker info."""
        from src.db.storage.ticker_metadata import _parse_ticker_info
        info = {}
        result = _parse_ticker_info("INVALID", info, False, "Ticker not found")
        
        assert result["ticker"] == "INVALID"
        assert result["is_valid"] is False
