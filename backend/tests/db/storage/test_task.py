"""
Unit tests for task storage module.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestTaskStorageImports:
    """Tests for task storage module imports."""

    def test_module_import(self):
        """Test that task storage module can be imported."""
        from src.db.storage import task
        assert task is not None

    def test_task_storage_import(self):
        """Test that TaskStorage class can be imported."""
        from src.db.storage.task import TaskStorage
        assert TaskStorage is not None

    def test_get_task_storage_import(self):
        """Test that get_task_storage function can be imported."""
        from src.db.storage.task import get_task_storage
        assert get_task_storage is not None


class TestTaskStorageClass:
    """Tests for TaskStorage class structure."""

    def test_task_storage_has_required_methods(self):
        """Test that TaskStorage class has all required methods."""
        from src.db.storage.task import TaskStorage
        
        # Check all expected methods exist
        assert hasattr(TaskStorage, "create_task")
        assert hasattr(TaskStorage, "get_by_id")
        assert hasattr(TaskStorage, "list_tasks")
        assert hasattr(TaskStorage, "update_status")
        assert hasattr(TaskStorage, "add_log")
        assert hasattr(TaskStorage, "cancel_task")
        assert hasattr(TaskStorage, "retry_task")
        assert hasattr(TaskStorage, "delete_by_id")
        assert hasattr(TaskStorage, "get_running_count")
        assert hasattr(TaskStorage, "get_pending_tasks")

    def test_task_storage_inherits_base_storage(self):
        """Test that TaskStorage inherits from BaseStorage."""
        from src.db.storage.task import TaskStorage
        from src.db.storage.base import BaseStorage
        assert issubclass(TaskStorage, BaseStorage)
