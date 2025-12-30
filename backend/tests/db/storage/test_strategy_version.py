"""
Unit tests for strategy version storage module.
"""
import pytest
from unittest.mock import MagicMock, patch

from src.db.storage.strategy_version import (
    StrategyVersionStorage,
    compute_code_hash,
    count_line_changes,
)


class TestComputeCodeHash:
    """Tests for compute_code_hash function."""

    def test_compute_hash_same_code(self):
        """Test that same code produces same hash."""
        code = "def strategy():\n    pass"
        hash1 = compute_code_hash(code)
        hash2 = compute_code_hash(code)
        assert hash1 == hash2

    def test_compute_hash_different_code(self):
        """Test that different code produces different hash."""
        code1 = "def strategy():\n    pass"
        code2 = "def strategy():\n    return True"
        hash1 = compute_code_hash(code1)
        hash2 = compute_code_hash(code2)
        assert hash1 != hash2

    def test_compute_hash_empty_code(self):
        """Test hash of empty code."""
        hash1 = compute_code_hash("")
        assert hash1 is not None
        assert len(hash1) == 64  # SHA-256 produces 64 hex characters


class TestCountLineChanges:
    """Tests for count_line_changes function."""

    def test_count_changes_no_diff(self):
        """Test counting changes when code is identical."""
        code = "line1\nline2\nline3"
        added, removed = count_line_changes(code, code)
        assert added == 0
        assert removed == 0

    def test_count_changes_additions(self):
        """Test counting added lines."""
        old_code = "line1\nline2"
        new_code = "line1\nline2\nline3"
        added, removed = count_line_changes(old_code, new_code)
        assert added == 1
        assert removed == 0

    def test_count_changes_removals(self):
        """Test counting removed lines."""
        old_code = "line1\nline2\nline3"
        new_code = "line1\nline2"
        added, removed = count_line_changes(old_code, new_code)
        assert added == 0
        assert removed == 1

    def test_count_changes_mixed(self):
        """Test counting mixed changes."""
        old_code = "line1\nold_line\nline3"
        new_code = "line1\nnew_line\nline3"
        added, removed = count_line_changes(old_code, new_code)
        assert added == 1
        assert removed == 1


class TestStrategyVersionStorageInit:
    """Tests for StrategyVersionStorage initialization."""

    @patch("src.db.storage.strategy_version.init_database")
    def test_init_storage(self, mock_init_db):
        """Test storage initialization."""
        mock_init_db.return_value = MagicMock()
        storage = StrategyVersionStorage()
        assert storage is not None

    @patch("src.db.storage.strategy_version.init_database")
    def test_init_storage_custom_url(self, mock_init_db):
        """Test storage initialization with custom database URL."""
        mock_init_db.return_value = MagicMock()
        storage = StrategyVersionStorage(database_url="sqlite:///test.db")
        mock_init_db.assert_called()


class TestStrategyVersionStorageCreateVersion:
    """Tests for create_version method."""

    @patch("src.db.storage.strategy_version.init_database")
    def test_create_version_interface(self, mock_init_db):
        """Test that create_version method exists with correct signature."""
        mock_init_db.return_value = MagicMock()
        storage = StrategyVersionStorage()
        
        assert hasattr(storage, "create_version")
        import inspect
        sig = inspect.signature(storage.create_version)
        params = list(sig.parameters.keys())
        assert "strategy_name" in params
        assert "code" in params


class TestStrategyVersionStorageListVersions:
    """Tests for list_versions method."""

    @patch("src.db.storage.strategy_version.init_database")
    def test_list_versions_interface(self, mock_init_db):
        """Test that list_versions method exists with correct signature."""
        mock_init_db.return_value = MagicMock()
        storage = StrategyVersionStorage()
        
        assert hasattr(storage, "list_versions")
        import inspect
        sig = inspect.signature(storage.list_versions)
        params = list(sig.parameters.keys())
        assert "strategy_name" in params
        assert "limit" in params
        assert "offset" in params


class TestStrategyVersionStorageGetVersion:
    """Tests for get_version method."""

    @patch("src.db.storage.strategy_version.init_database")
    def test_get_version_interface(self, mock_init_db):
        """Test that get_version method exists with correct signature."""
        mock_init_db.return_value = MagicMock()
        storage = StrategyVersionStorage()
        
        assert hasattr(storage, "get_version")
        import inspect
        sig = inspect.signature(storage.get_version)
        params = list(sig.parameters.keys())
        assert "strategy_name" in params
        assert "version_number" in params


class TestStrategyVersionStorageGetLatestVersion:
    """Tests for get_latest_version method."""

    @patch("src.db.storage.strategy_version.init_database")
    def test_get_latest_version_interface(self, mock_init_db):
        """Test that get_latest_version method exists."""
        mock_init_db.return_value = MagicMock()
        storage = StrategyVersionStorage()
        
        assert hasattr(storage, "get_latest_version")
