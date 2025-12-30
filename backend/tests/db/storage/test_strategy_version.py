"""
Unit tests for strategy version storage module.
"""
import pytest
from unittest.mock import MagicMock, patch

from src.db.storage.strategy_version import (
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


class TestStrategyVersionStorageImports:
    """Tests for strategy version storage module imports."""

    def test_module_import(self):
        """Test that strategy version storage module can be imported."""
        from src.db.storage import strategy_version
        assert strategy_version is not None

    def test_storage_class_import(self):
        """Test that StrategyVersionStorage class can be imported."""
        from src.db.storage.strategy_version import StrategyVersionStorage
        assert StrategyVersionStorage is not None


class TestStrategyVersionStorageClass:
    """Tests for StrategyVersionStorage class structure."""

    def test_storage_has_required_methods(self):
        """Test that StrategyVersionStorage class has all required methods."""
        from src.db.storage.strategy_version import StrategyVersionStorage
        
        # Check all expected methods exist
        assert hasattr(StrategyVersionStorage, "create_version")
        assert hasattr(StrategyVersionStorage, "list_versions")
        assert hasattr(StrategyVersionStorage, "get_version")
        assert hasattr(StrategyVersionStorage, "get_latest_version")

    def test_storage_inherits_base_storage(self):
        """Test that StrategyVersionStorage inherits from BaseStorage."""
        from src.db.storage.strategy_version import StrategyVersionStorage
        from src.db.storage.base import BaseStorage
        assert issubclass(StrategyVersionStorage, BaseStorage)
