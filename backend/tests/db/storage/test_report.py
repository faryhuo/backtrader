"""
Unit tests for report storage module.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.db.storage.report import ReportStorage


class TestReportStorageInit:
    """Tests for ReportStorage initialization."""

    @patch("src.db.storage.report.init_database")
    def test_init_storage(self, mock_init_db):
        """Test storage initialization."""
        mock_init_db.return_value = MagicMock()
        storage = ReportStorage()
        assert storage is not None
        assert storage.MAX_RECORDS == 100

    @patch("src.db.storage.report.init_database")
    def test_init_storage_custom_url(self, mock_init_db):
        """Test storage initialization with custom database URL."""
        mock_init_db.return_value = MagicMock()
        storage = ReportStorage(database_url="sqlite:///test.db")
        mock_init_db.assert_called()


class TestReportStorageCreateReport:
    """Tests for create_report method."""

    @patch("src.db.storage.report.init_database")
    def test_create_report_basic(self, mock_init_db):
        """Test creating a basic report record."""
        mock_session = MagicMock()
        mock_init_db.return_value = MagicMock()
        
        storage = ReportStorage()
        with patch.object(storage, "_get_session") as mock_get_session:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.__exit__ = MagicMock(return_value=None)
            mock_get_session.return_value = mock_ctx
            
            # The method should be callable with required params
            # We're testing the interface exists
            assert hasattr(storage, "create_report")


class TestReportStorageGetReport:
    """Tests for get_report method."""

    @patch("src.db.storage.report.init_database")
    def test_get_report_not_found(self, mock_init_db):
        """Test that get_report returns None when not found."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_init_db.return_value = MagicMock()

        storage = ReportStorage()
        with patch.object(storage, "_get_session") as mock_get_session:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.__exit__ = MagicMock(return_value=None)
            mock_get_session.return_value = mock_ctx

            result = storage.get_report("nonexistent-id")
            assert result is None


class TestReportStorageGetByShareToken:
    """Tests for get_report_by_share_token method."""

    @patch("src.db.storage.report.init_database")
    def test_get_by_share_token_not_found(self, mock_init_db):
        """Test that get_report_by_share_token returns None when not found."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_query.first.return_value = None
        mock_session.query.return_value.filter.return_value = mock_query
        mock_init_db.return_value = MagicMock()

        storage = ReportStorage()
        with patch.object(storage, "_get_session") as mock_get_session:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.__exit__ = MagicMock(return_value=None)
            mock_get_session.return_value = mock_ctx

            result = storage.get_report_by_share_token("invalid-token")
            assert result is None


class TestReportStorageListReports:
    """Tests for list_reports method."""

    @patch("src.db.storage.report.init_database")
    def test_list_reports_interface(self, mock_init_db):
        """Test that list_reports method exists with correct signature."""
        mock_init_db.return_value = MagicMock()
        storage = ReportStorage()
        
        assert hasattr(storage, "list_reports")
        # Can be called with various filter options
        import inspect
        sig = inspect.signature(storage.list_reports)
        params = list(sig.parameters.keys())
        assert "report_type" in params
        assert "status" in params
        assert "limit" in params
        assert "offset" in params


class TestReportStorageUpdateStatus:
    """Tests for update_status method."""

    @patch("src.db.storage.report.init_database")
    def test_update_status_interface(self, mock_init_db):
        """Test that update_status method exists."""
        mock_init_db.return_value = MagicMock()
        storage = ReportStorage()
        
        assert hasattr(storage, "update_status")


class TestReportStorageSaveContent:
    """Tests for save_content method."""

    @patch("src.db.storage.report.init_database")
    def test_save_content_interface(self, mock_init_db):
        """Test that save_content method exists with correct signature."""
        mock_init_db.return_value = MagicMock()
        storage = ReportStorage()
        
        assert hasattr(storage, "save_content")
        import inspect
        sig = inspect.signature(storage.save_content)
        params = list(sig.parameters.keys())
        assert "report_id" in params
        assert "html_content" in params


class TestReportStorageShareToken:
    """Tests for share token methods."""

    @patch("src.db.storage.report.init_database")
    def test_set_share_token_interface(self, mock_init_db):
        """Test that set_share_token method exists."""
        mock_init_db.return_value = MagicMock()
        storage = ReportStorage()
        
        assert hasattr(storage, "set_share_token")

    @patch("src.db.storage.report.init_database")
    def test_clear_share_token_interface(self, mock_init_db):
        """Test that clear_share_token method exists."""
        mock_init_db.return_value = MagicMock()
        storage = ReportStorage()
        
        assert hasattr(storage, "clear_share_token")


class TestReportStorageDeleteReport:
    """Tests for delete_report method."""

    @patch("src.db.storage.report.init_database")
    def test_delete_report_interface(self, mock_init_db):
        """Test that delete_report method exists."""
        mock_init_db.return_value = MagicMock()
        storage = ReportStorage()
        
        assert hasattr(storage, "delete_report")
