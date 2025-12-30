"""
Unit tests for report storage module.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestReportStorageImports:
    """Tests for report storage module imports."""

    def test_module_import(self):
        """Test that report storage module can be imported."""
        from src.db.storage import report
        assert report is not None

    def test_report_storage_import(self):
        """Test that ReportStorage class can be imported."""
        from src.db.storage.report import ReportStorage
        assert ReportStorage is not None


class TestReportStorageClass:
    """Tests for ReportStorage class structure."""

    def test_report_storage_has_required_methods(self):
        """Test that ReportStorage class has all required methods."""
        from src.db.storage.report import ReportStorage
        
        # Check all expected methods exist
        assert hasattr(ReportStorage, "create_report")
        assert hasattr(ReportStorage, "get_report")
        assert hasattr(ReportStorage, "get_report_by_share_token")
        assert hasattr(ReportStorage, "list_reports")
        assert hasattr(ReportStorage, "update_status")
        assert hasattr(ReportStorage, "save_content")
        assert hasattr(ReportStorage, "set_share_token")
        assert hasattr(ReportStorage, "clear_share_token")
        assert hasattr(ReportStorage, "delete_report")

    def test_report_storage_inherits_base_storage(self):
        """Test that ReportStorage inherits from BaseStorage."""
        from src.db.storage.report import ReportStorage
        from src.db.storage.base import BaseStorage
        assert issubclass(ReportStorage, BaseStorage)
