"""
Unit tests for portfolio storage module.
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.db.storage.portfolio import (
    PortfolioStorage,
    get_portfolio_storage,
)


class TestPortfolioStorage:
    """Tests for PortfolioStorage class."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = MagicMock()
        session.__enter__ = MagicMock(return_value=session)
        session.__exit__ = MagicMock(return_value=None)
        return session

    @pytest.fixture
    def sample_result(self):
        """Sample portfolio backtest result."""
        return {
            "portfolio_id": "test-portfolio-123",
            "total_return": 15.5,
            "annual_return": 12.3,
            "sharpe_ratio": 1.25,
            "max_drawdown": -8.5,
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_cash": 100000,
            "assets": ["AAPL", "GOOGL", "MSFT"],
            "weights": {"AAPL": 0.4, "GOOGL": 0.3, "MSFT": 0.3},
            "rebalance_frequency": "monthly",
            "metrics": {
                "calmar_ratio": 1.8,
                "trades_count": 24,
            },
        }

    @patch("src.db.storage.portfolio.init_database")
    def test_init_storage(self, mock_init_db):
        """Test storage initialization."""
        mock_init_db.return_value = MagicMock()
        storage = PortfolioStorage()
        assert storage is not None

    @patch("src.db.storage.portfolio.init_database")
    def test_init_storage_custom_url(self, mock_init_db):
        """Test storage initialization with custom database URL."""
        mock_init_db.return_value = MagicMock()
        storage = PortfolioStorage(database_url="sqlite:///test.db")
        mock_init_db.assert_called()


class TestPortfolioStorageSaveResult:
    """Tests for save_result method."""

    @patch("src.db.storage.portfolio.init_database")
    def test_save_result_returns_id(self, mock_init_db, sample_result):
        """Test that save_result returns portfolio ID."""
        mock_session = MagicMock()
        mock_init_db.return_value = MagicMock()
        mock_init_db.return_value.get_session.return_value.__enter__ = MagicMock(
            return_value=mock_session
        )
        mock_init_db.return_value.get_session.return_value.__exit__ = MagicMock(
            return_value=None
        )

        storage = PortfolioStorage()
        # Mock the session context manager
        with patch.object(storage, "_get_session") as mock_get_session:
            mock_get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_get_session.return_value.__exit__ = MagicMock(return_value=None)

    @pytest.fixture
    def sample_result(self):
        """Sample portfolio backtest result."""
        return {
            "portfolio_id": "test-portfolio-123",
            "total_return": 15.5,
            "annual_return": 12.3,
            "sharpe_ratio": 1.25,
            "max_drawdown": -8.5,
        }


class TestPortfolioStorageGetById:
    """Tests for get_by_id method."""

    @patch("src.db.storage.portfolio.init_database")
    def test_get_by_id_not_found(self, mock_init_db):
        """Test that get_by_id returns None when not found."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_init_db.return_value = MagicMock()

        storage = PortfolioStorage()
        with patch.object(storage, "_get_session") as mock_get_session:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.__exit__ = MagicMock(return_value=None)
            mock_get_session.return_value = mock_ctx
            
            result = storage.get_by_id("nonexistent-id")
            assert result is None


class TestPortfolioStorageListHistory:
    """Tests for list_history method."""

    @patch("src.db.storage.portfolio.init_database")
    def test_list_history_empty(self, mock_init_db):
        """Test listing history when empty."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_session.query.return_value.filter.return_value = mock_query
        mock_init_db.return_value = MagicMock()

        storage = PortfolioStorage()
        with patch.object(storage, "_get_session") as mock_get_session:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.__exit__ = MagicMock(return_value=None)
            mock_get_session.return_value = mock_ctx


class TestGetPortfolioStorageSingleton:
    """Tests for get_portfolio_storage singleton function."""

    @patch("src.db.storage.portfolio.init_database")
    @patch("src.db.storage.portfolio._storage_instance", None)
    def test_get_portfolio_storage_singleton(self, mock_init_db):
        """Test that get_portfolio_storage returns singleton instance."""
        mock_init_db.return_value = MagicMock()
        
        storage1 = get_portfolio_storage()
        storage2 = get_portfolio_storage()
        assert storage1 is storage2
