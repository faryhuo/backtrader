"""
Unit tests for task manager service.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.service.task_manager import TaskManager, get_task_manager


class TestTaskManager:
    """Tests for TaskManager class."""

    @pytest.fixture
    def task_manager(self):
        """Create TaskManager instance."""
        with patch("src.service.task_manager.get_task_storage") as mock_storage:
            manager = TaskManager()
            yield manager

    def test_task_manager_initialization(self, task_manager):
        """Test TaskManager can be initialized."""
        assert task_manager is not None
        assert task_manager.max_concurrent > 0

    def test_task_manager_has_storage(self, task_manager):
        """Test TaskManager has storage attribute."""
        assert hasattr(task_manager, 'storage')


class TestTaskExecution:
    """Tests for task execution logic."""

    @pytest.mark.asyncio
    async def test_execute_task_success(self):
        """Test successful task execution."""
        async def success_executor(config, progress_callback):
            await progress_callback(25, "Started")
            await progress_callback(50, "Halfway")
            await progress_callback(75, "Almost done")
            await progress_callback(100, "Complete")
            return {"result": "success", "data": config["input"]}

        config = {"input": "test_data"}

        # Track progress updates
        progress_updates = []

        async def track_progress(progress, message):
            progress_updates.append((progress, message))

        result = await success_executor(config, track_progress)

        assert result["result"] == "success"
        assert result["data"] == "test_data"
        assert len(progress_updates) == 4
        assert progress_updates[-1][0] == 100

    @pytest.mark.asyncio
    async def test_execute_task_failure(self):
        """Test task execution failure."""
        async def failing_executor(config, progress_callback):
            await progress_callback(10, "Starting")
            raise ValueError("Task failed due to invalid input")

        with pytest.raises(ValueError) as exc_info:
            await failing_executor({}, AsyncMock())

        assert "invalid input" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_progress_callback(self):
        """Test progress callback functionality."""
        progress_values = []
        messages = []

        async def progress_callback(progress, message):
            progress_values.append(progress)
            messages.append(message)

        async def executor_with_progress(config, callback):
            await callback(0, "Initializing")
            await callback(33, "Processing data")
            await callback(66, "Analyzing results")
            await callback(100, "Complete")
            return {"status": "done"}

        result = await executor_with_progress({}, progress_callback)

        assert result["status"] == "done"
        assert progress_values == [0, 33, 66, 100]
        assert len(messages) == 4
        assert messages[0] == "Initializing"
        assert messages[-1] == "Complete"


class TestTaskManagerSingleton:
    """Tests for TaskManager singleton pattern."""

    def test_get_task_manager_singleton(self):
        """Test that get_task_manager returns singleton."""
        with patch("src.service.task_manager.get_task_storage"):
            manager1 = get_task_manager()
            manager2 = get_task_manager()

            assert manager1 is manager2


class TestConcurrencyControl:
    """Tests for concurrency control."""

    def test_max_concurrent_default(self):
        """Test default max_concurrent setting."""
        with patch("src.service.task_manager.get_task_storage"):
            manager = TaskManager()
            assert manager.max_concurrent >= 1

    def test_max_concurrent_custom(self):
        """Test custom max_concurrent setting."""
        with patch("src.service.task_manager.get_task_storage"):
            manager = TaskManager(max_concurrent=5)
            assert manager.max_concurrent == 5
