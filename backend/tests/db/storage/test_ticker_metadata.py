"""
Unit tests for ticker metadata module.
"""
import pytest
from unittest.mock import MagicMock, patch

from src.db.storage.ticker_metadata import (
    _validate_ticker_info,
    _parse_ticker_info,
    get_ticker_metadata,
)


class TestValidateTickerInfo:
    """Tests for _validate_ticker_info function."""

    def test_validate_empty_info(self):
        """Test validation of empty info dict."""
        is_valid, error = _validate_ticker_info({})
        assert is_valid is False
        assert error is not None

    def test_validate_valid_info(self):
        """Test validation of valid ticker info."""
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
        info = {
            "shortName": "Apple",
            "regularMarketPrice": 150.0,
        }
        is_valid, error = _validate_ticker_info(info)
        assert is_valid is True

    def test_validate_info_with_previous_close(self):
        """Test validation with previousClose price."""
        info = {
            "symbol": "AAPL",
            "previousClose": 149.0,
        }
        is_valid, error = _validate_ticker_info(info)
        assert is_valid is True

    def test_validate_info_missing_price(self):
        """Test validation when price fields are missing."""
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
        assert result["name"] == "Apple Inc."
        assert result["currency"] == "USD"

    def test_parse_invalid_info(self):
        """Test parsing invalid ticker info."""
        info = {}
        result = _parse_ticker_info("INVALID", info, False, "Ticker not found")
        
        assert result["ticker"] == "INVALID"
        assert result["is_valid"] is False
        assert result["error_message"] == "Ticker not found"


class TestGetTickerMetadata:
    """Tests for get_ticker_metadata function."""

    @patch("src.db.storage.ticker_metadata.init_database")
    @patch("src.db.storage.ticker_metadata.yf")
    def test_get_metadata_from_cache(self, mock_yf, mock_init_db):
        """Test getting metadata from cache."""
        # Setup mock session with cached data
        mock_session = MagicMock()
        mock_model = MagicMock()
        mock_model.ticker = "AAPL"
        mock_model.is_valid = True
        mock_model.name = "Apple Inc."
        mock_model.exchange = "NASDAQ"
        mock_model.currency = "USD"
        mock_model.market_cap = 2500000000000
        mock_model.sector = "Technology"
        mock_model.industry = "Consumer Electronics"
        mock_model.country = "United States"
        mock_model.website = "https://apple.com"
        mock_model.logo_url = None
        mock_model.last_updated = MagicMock()
        mock_model.error_message = None
        
        mock_session.query.return_value.filter.return_value.first.return_value = mock_model
        
        mock_engine = MagicMock()
        mock_init_db.return_value = mock_engine
        mock_engine.get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_engine.get_session.return_value.__exit__ = MagicMock(return_value=None)

    @patch("src.db.storage.ticker_metadata.init_database")
    @patch("src.db.storage.ticker_metadata.yf")
    def test_get_metadata_force_refresh(self, mock_yf, mock_init_db):
        """Test getting metadata with force refresh."""
        mock_ticker = MagicMock()
        mock_ticker.info = {
            "longName": "Apple Inc.",
            "symbol": "AAPL",
            "currentPrice": 150.0,
        }
        mock_yf.Ticker.return_value = mock_ticker
        
        mock_engine = MagicMock()
        mock_init_db.return_value = mock_engine
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_engine.get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_engine.get_session.return_value.__exit__ = MagicMock(return_value=None)

    @patch("src.db.storage.ticker_metadata.init_database")
    @patch("src.db.storage.ticker_metadata.yf")
    def test_get_metadata_yfinance_error(self, mock_yf, mock_init_db):
        """Test handling yfinance errors."""
        mock_yf.Ticker.side_effect = Exception("Network error")
        
        mock_engine = MagicMock()
        mock_init_db.return_value = mock_engine
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_engine.get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_engine.get_session.return_value.__exit__ = MagicMock(return_value=None)
