"""
Tests for DataCacheStorage - data cache management.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.db.storage.data_cache import DataCacheStorage, get_data_cache_storage


class TestDataCacheStorage:
    """Test suite for DataCacheStorage."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = MagicMock()
        session.query.return_value.scalar.return_value = 0
        return session

    @pytest.fixture
    def storage(self, mock_session):
        """Create a DataCacheStorage with mocked database."""
        with patch("src.db.storage.data_cache.init_database") as mock_init:
            mock_init.return_value = (MagicMock(), MagicMock(return_value=mock_session))
            return DataCacheStorage()

    def test_get_cache_stats_empty(self, storage, mock_session):
        """Test cache stats with empty database."""
        mock_session.query.return_value.scalar.return_value = 0
        
        stats = storage.get_cache_stats(db=mock_session)
        
        assert stats["total_tickers"] == 0
        assert stats["total_records"] == 0
        assert stats["date_range"] is None
        assert stats["tickers"] == []

    def test_get_cache_stats_with_data(self, storage, mock_session):
        """Test cache stats with data."""
        # Mock total count
        mock_session.query.return_value.scalar.side_effect = [100, "2024-01-01", "2024-12-31"]
        
        # Mock per-ticker stats
        mock_row = MagicMock()
        mock_row.ticker = "AAPL"
        mock_row.record_count = 50
        mock_row.min_date = "2024-01-01"
        mock_row.max_date = "2024-12-31"
        mock_row.last_updated = datetime(2024, 12, 21, 10, 0, 0)
        
        mock_session.query.return_value.group_by.return_value.order_by.return_value.all.return_value = [mock_row]
        
        stats = storage.get_cache_stats(db=mock_session)
        
        assert stats["total_tickers"] == 1
        assert len(stats["tickers"]) == 1
        assert stats["tickers"][0]["ticker"] == "AAPL"

    def test_get_ticker_cache_info_not_found(self, storage, mock_session):
        """Test getting cache info for non-existent ticker."""
        mock_stats = MagicMock()
        mock_stats.record_count = 0
        mock_session.query.return_value.filter.return_value.first.return_value = mock_stats
        
        info = storage.get_ticker_cache_info("UNKNOWN", db=mock_session)
        
        assert info is None

    def test_get_ticker_cache_info_found(self, storage, mock_session):
        """Test getting cache info for existing ticker."""
        mock_stats = MagicMock()
        mock_stats.record_count = 100
        mock_stats.min_date = "2024-01-01"
        mock_stats.max_date = "2024-12-31"
        mock_stats.first_cached = datetime(2024, 1, 1, 10, 0, 0)
        mock_stats.last_updated = datetime(2024, 12, 21, 10, 0, 0)
        
        mock_session.query.return_value.filter.return_value.first.side_effect = [mock_stats, ("yfinance",)]
        
        info = storage.get_ticker_cache_info("AAPL", db=mock_session)
        
        assert info is not None
        assert info["ticker"] == "AAPL"
        assert info["record_count"] == 100
        assert info["source"] == "yfinance"

    def test_delete_ticker_cache_success(self, storage, mock_session):
        """Test deleting ticker cache successfully."""
        mock_session.query.return_value.filter.return_value.delete.return_value = 50
        
        result = storage.delete_ticker_cache("AAPL", db=mock_session)
        
        assert result is True
        mock_session.commit.assert_called_once()

    def test_delete_ticker_cache_not_found(self, storage, mock_session):
        """Test deleting non-existent ticker cache."""
        mock_session.query.return_value.filter.return_value.delete.return_value = 0
        
        result = storage.delete_ticker_cache("UNKNOWN", db=mock_session)
        
        assert result is False

    def test_get_all_cached_tickers(self, storage, mock_session):
        """Test getting all cached ticker symbols."""
        mock_session.query.return_value.distinct.return_value.order_by.return_value.all.return_value = [
            ("AAPL",), ("MSFT",), ("GOOGL",)
        ]
        
        tickers = storage.get_all_cached_tickers(db=mock_session)
        
        assert tickers == ["AAPL", "MSFT", "GOOGL"]

    def test_count_trading_days(self, storage):
        """Test trading day estimation."""
        # 1 year should be approximately 252 days
        days = storage._count_trading_days("2024-01-01", "2024-12-31")
        assert 240 <= days <= 265  # Reasonable range
        
        # 1 week should be approximately 5 days
        days = storage._count_trading_days("2024-01-01", "2024-01-07")
        assert 4 <= days <= 6


class TestWarmupData:
    """Test suite for warmup functionality."""

    @pytest.fixture
    def storage(self):
        """Create a DataCacheStorage with mocked database."""
        with patch("src.db.storage.data_cache.init_database") as mock_init:
            mock_init.return_value = (MagicMock(), MagicMock())
            return DataCacheStorage()

    @patch("src.db.storage.market_data.get_data_from_db")
    @patch("src.db.storage.market_data.get_data")
    def test_warmup_cache_hit(self, mock_get_data, mock_get_data_from_db, storage):
        """Test warmup when data is already cached."""
        import pandas as pd
        
        # Simulate cache hit - data exists with good coverage
        mock_df = pd.DataFrame({
            "Open": [100.0] * 252,
            "High": [105.0] * 252,
            "Low": [95.0] * 252,
            "Close": [102.0] * 252,
            "Volume": [1000000] * 252,
        })
        mock_get_data_from_db.return_value = mock_df
        
        result = storage.warmup_data(
            tickers=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-12-31",
        )
        
        assert len(result["success"]) == 1
        assert result["success"][0]["from_cache"] is True
        assert result["cache_hits"] == 1
        assert result["cache_hit_rate"] == 1.0
        mock_get_data.assert_not_called()  # Should not fetch from source

    @patch("src.db.storage.market_data.get_data_from_db")
    @patch("src.db.storage.market_data.get_data")
    def test_warmup_cache_miss(self, mock_get_data, mock_get_data_from_db, storage):
        """Test warmup when data needs to be fetched."""
        import pandas as pd
        
        # Simulate cache miss
        mock_get_data_from_db.return_value = None
        mock_get_data.return_value = pd.DataFrame({
            "Open": [100.0],
            "High": [105.0],
            "Low": [95.0],
            "Close": [102.0],
            "Volume": [1000000],
        })
        
        result = storage.warmup_data(
            tickers=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-01-02",
        )
        
        assert len(result["success"]) == 1
        assert result["success"][0]["from_cache"] is False
        assert result["cache_hits"] == 0
        assert result["total_fetched"] == 1

    @patch("src.db.storage.market_data.get_data_from_db")
    @patch("src.db.storage.market_data.get_data")
    def test_warmup_with_failure(self, mock_get_data, mock_get_data_from_db, storage):
        """Test warmup with fetch failure."""
        mock_get_data_from_db.return_value = None
        mock_get_data.side_effect = Exception("API Error")
        
        result = storage.warmup_data(
            tickers=["INVALID"],
            start_date="2024-01-01",
            end_date="2024-01-02",
        )
        
        assert len(result["failed"]) == 1
        assert result["failed"][0]["ticker"] == "INVALID"
        assert "API Error" in result["failed"][0]["error"]


class TestGetDataCacheStorageSingleton:
    """Test singleton pattern for DataCacheStorage."""

    def test_singleton_returns_same_instance(self):
        """Test that get_data_cache_storage returns the same instance."""
        with patch("src.db.storage.data_cache.init_database") as mock_init:
            mock_init.return_value = (MagicMock(), MagicMock())
            
            # Reset singleton
            import src.db.storage.data_cache as module
            module._data_cache_storage = None
            
            instance1 = get_data_cache_storage()
            instance2 = get_data_cache_storage()
            
            assert instance1 is instance2
