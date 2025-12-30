"""
Unit tests for task contracts module.
"""
import pytest

from src.contracts.task import (
    TaskType,
    TaskStatus,
)


class TestTaskType:
    """Tests for TaskType enum."""

    def test_task_type_values(self):
        """Test that all task types have correct values."""
        assert TaskType.BACKTEST.value == "backtest"
        assert TaskType.PORTFOLIO.value == "portfolio"
        assert TaskType.WALKFORWARD.value == "walkforward"
        assert TaskType.DEEP_ANALYSIS.value == "deep_analysis"

    def test_task_type_from_string(self):
        """Test creating TaskType from string value."""
        assert TaskType("backtest") == TaskType.BACKTEST
        assert TaskType("portfolio") == TaskType.PORTFOLIO
        assert TaskType("walkforward") == TaskType.WALKFORWARD
        assert TaskType("deep_analysis") == TaskType.DEEP_ANALYSIS

    def test_task_type_invalid_value(self):
        """Test that invalid task type raises ValueError."""
        with pytest.raises(ValueError):
            TaskType("invalid_type")

    def test_task_type_is_string_enum(self):
        """Test that TaskType values can be used as strings."""
        assert TaskType.BACKTEST == "backtest"
        assert TaskType.BACKTEST.value == "backtest"


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_task_status_values(self):
        """Test that all task statuses have correct values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"

    def test_task_status_from_string(self):
        """Test creating TaskStatus from string value."""
        assert TaskStatus("pending") == TaskStatus.PENDING
        assert TaskStatus("running") == TaskStatus.RUNNING
        assert TaskStatus("completed") == TaskStatus.COMPLETED
        assert TaskStatus("failed") == TaskStatus.FAILED
        assert TaskStatus("cancelled") == TaskStatus.CANCELLED

    def test_task_status_invalid_value(self):
        """Test that invalid task status raises ValueError."""
        with pytest.raises(ValueError):
            TaskStatus("invalid_status")

    def test_task_status_is_string_enum(self):
        """Test that TaskStatus values can be used as strings."""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.COMPLETED.value == "completed"


class TestEnumIteration:
    """Tests for enum iteration."""

    def test_task_type_iteration(self):
        """Test iterating over TaskType values."""
        types = list(TaskType)
        assert len(types) == 4
        assert TaskType.BACKTEST in types
        assert TaskType.PORTFOLIO in types

    def test_task_status_iteration(self):
        """Test iterating over TaskStatus values."""
        statuses = list(TaskStatus)
        assert len(statuses) == 5
        assert TaskStatus.PENDING in statuses
        assert TaskStatus.COMPLETED in statuses
