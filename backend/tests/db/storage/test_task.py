"""
Unit tests for task storage module.
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.db.storage.task import (
    TaskStorage,
    get_task_storage,
)


class TestTaskStorageInit:
    """Tests for TaskStorage initialization."""

    @patch("src.db.storage.task.init_database")
    def test_init_storage(self, mock_init_db):
        """Test storage initialization."""
        mock_init_db.return_value = MagicMock()
        storage = TaskStorage()
        assert storage is not None


class TestTaskStorageCreateTask:
    """Tests for create_task method."""

    @patch("src.db.storage.task.init_database")
    def test_create_task_interface(self, mock_init_db):
        """Test that create_task method exists with correct signature."""
        mock_init_db.return_value = MagicMock()
        storage = TaskStorage()
        
        assert hasattr(storage, "create_task")
        import inspect
        sig = inspect.signature(storage.create_task)
        params = list(sig.parameters.keys())
        assert "task_type" in params
        assert "config" in params
        assert "user_id" in params


class TestTaskStorageGetById:
    """Tests for get_by_id method."""

    @patch("src.db.storage.task.init_database")
    def test_get_by_id_not_found(self, mock_init_db):
        """Test that get_by_id returns None when not found."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_init_db.return_value = MagicMock()

        storage = TaskStorage()
        with patch.object(storage, "_get_session") as mock_get_session:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.__exit__ = MagicMock(return_value=None)
            mock_get_session.return_value = mock_ctx

            result = storage.get_by_id("nonexistent-id")
            assert result is None


class TestTaskStorageListTasks:
    """Tests for list_tasks method."""

    @patch("src.db.storage.task.init_database")
    def test_list_tasks_interface(self, mock_init_db):
        """Test that list_tasks method exists with correct signature."""
        mock_init_db.return_value = MagicMock()
        storage = TaskStorage()
        
        assert hasattr(storage, "list_tasks")
        import inspect
        sig = inspect.signature(storage.list_tasks)
        params = list(sig.parameters.keys())
        assert "user_id" in params
        assert "task_type" in params
        assert "status" in params
        assert "limit" in params
        assert "offset" in params


class TestTaskStorageUpdateStatus:
    """Tests for update_status method."""

    @patch("src.db.storage.task.init_database")
    def test_update_status_interface(self, mock_init_db):
        """Test that update_status method exists with correct signature."""
        mock_init_db.return_value = MagicMock()
        storage = TaskStorage()
        
        assert hasattr(storage, "update_status")
        import inspect
        sig = inspect.signature(storage.update_status)
        params = list(sig.parameters.keys())
        assert "task_id" in params
        assert "status" in params
        assert "progress" in params


class TestTaskStorageAddLog:
    """Tests for add_log method."""

    @patch("src.db.storage.task.init_database")
    def test_add_log_interface(self, mock_init_db):
        """Test that add_log method exists with correct signature."""
        mock_init_db.return_value = MagicMock()
        storage = TaskStorage()
        
        assert hasattr(storage, "add_log")
        import inspect
        sig = inspect.signature(storage.add_log)
        params = list(sig.parameters.keys())
        assert "task_id" in params
        assert "level" in params
        assert "message" in params


class TestTaskStorageCancelTask:
    """Tests for cancel_task method."""

    @patch("src.db.storage.task.init_database")
    def test_cancel_task_interface(self, mock_init_db):
        """Test that cancel_task method exists."""
        mock_init_db.return_value = MagicMock()
        storage = TaskStorage()
        
        assert hasattr(storage, "cancel_task")


class TestTaskStorageRetryTask:
    """Tests for retry_task method."""

    @patch("src.db.storage.task.init_database")
    def test_retry_task_interface(self, mock_init_db):
        """Test that retry_task method exists."""
        mock_init_db.return_value = MagicMock()
        storage = TaskStorage()
        
        assert hasattr(storage, "retry_task")


class TestTaskStorageDeleteById:
    """Tests for delete_by_id method."""

    @patch("src.db.storage.task.init_database")
    def test_delete_by_id_interface(self, mock_init_db):
        """Test that delete_by_id method exists with correct signature."""
        mock_init_db.return_value = MagicMock()
        storage = TaskStorage()
        
        assert hasattr(storage, "delete_by_id")
        import inspect
        sig = inspect.signature(storage.delete_by_id)
        params = list(sig.parameters.keys())
        assert "task_id" in params
        assert "force" in params


class TestTaskStorageRunningAndPending:
    """Tests for running and pending task methods."""

    @patch("src.db.storage.task.init_database")
    def test_get_running_count_interface(self, mock_init_db):
        """Test that get_running_count method exists."""
        mock_init_db.return_value = MagicMock()
        storage = TaskStorage()
        
        assert hasattr(storage, "get_running_count")

    @patch("src.db.storage.task.init_database")
    def test_get_pending_tasks_interface(self, mock_init_db):
        """Test that get_pending_tasks method exists."""
        mock_init_db.return_value = MagicMock()
        storage = TaskStorage()
        
        assert hasattr(storage, "get_pending_tasks")


class TestGetTaskStorageSingleton:
    """Tests for get_task_storage singleton function."""

    @patch("src.db.storage.task.init_database")
    @patch("src.db.storage.task._task_storage", None)
    def test_get_task_storage_singleton(self, mock_init_db):
        """Test that get_task_storage returns singleton instance."""
        mock_init_db.return_value = MagicMock()
        
        storage1 = get_task_storage()
        storage2 = get_task_storage()
        assert storage1 is storage2
