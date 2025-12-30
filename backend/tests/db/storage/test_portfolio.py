"""
Unit tests for portfolio storage module.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestPortfolioStorageImports:
    """Tests for portfolio storage module imports."""

    def test_module_import(self):
        """Test that portfolio storage module can be imported."""
        from src.db.storage import portfolio
        assert portfolio is not None

    def test_portfolio_storage_import(self):
        """Test that PortfolioStorage class can be imported."""
        from src.db.storage.portfolio import PortfolioStorage
        assert PortfolioStorage is not None

    def test_get_portfolio_storage_import(self):
        """Test that get_portfolio_storage function can be imported."""
        from src.db.storage.portfolio import get_portfolio_storage
        assert get_portfolio_storage is not None


class TestPortfolioStorageClass:
    """Tests for PortfolioStorage class structure."""

    def test_portfolio_storage_has_required_methods(self):
        """Test that PortfolioStorage class has all required methods."""
        from src.db.storage.portfolio import PortfolioStorage
        
        # Check all expected methods exist
        assert hasattr(PortfolioStorage, "save_result")
        assert hasattr(PortfolioStorage, "get_by_id")
        assert hasattr(PortfolioStorage, "list_history")
        assert hasattr(PortfolioStorage, "delete_by_id")

    def test_portfolio_storage_inherits_base_storage(self):
        """Test that PortfolioStorage inherits from BaseStorage."""
        from src.db.storage.portfolio import PortfolioStorage
        from src.db.storage.base import BaseStorage
        assert issubclass(PortfolioStorage, BaseStorage)
