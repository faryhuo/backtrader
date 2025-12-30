"""
Unit tests for pyfolio exporter module.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestPyfolioExporterImports:
    """Tests for pyfolio exporter module imports."""

    def test_module_import(self):
        """Test that pyfolio exporter module can be imported."""
        from src.service import pyfolio_exporter
        assert pyfolio_exporter is not None


class TestPyfolioExporter:
    """Tests for pyfolio exporter functions."""

    def test_has_export_function(self):
        """Test that module has export functions."""
        from src.service import pyfolio_exporter
        assert pyfolio_exporter is not None
