"""Unit tests for multi-asset worker module."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.service.worker.task_models import (
    MultiAssetBacktestTask,
    MultiAssetBacktestResult,
    TaskStatus,
)


class TestMultiAssetBacktestTask:
    """Tests for MultiAssetBacktestTask dataclass."""

    def test_create_basic_task(self):
        """Test creating a basic multi-asset task."""
        task = MultiAssetBacktestTask(
            task_id="test-123",
            tickers=["AAPL", "GOOGL"],
            weights=[0.5, 0.5],
            start_date="2024-01-01",
            end_date="2024-12-31"
        )

        assert task.task_id == "test-123"
        assert task.tickers == ["AAPL", "GOOGL"]
        assert task.weights == [0.5, 0.5]
        assert task.initial_cash == 100000.0
        assert task.optimization_method == "equal_weight"

    def test_create_full_task(self):
        """Test creating a fully configured task."""
        task = MultiAssetBacktestTask(
            task_id="test-456",
            tickers=["AAPL", "GOOGL", "MSFT"],
            weights=[0.4, 0.35, 0.25],
            start_date="2024-01-01",
            end_date="2024-12-31",
            initial_cash=500000.0,
            commission=0.001,
            strategy_name="sma_cross",
            rebalance_config={
                "frequency": "monthly",
                "min_trade_threshold": 0.02
            },
            optimization_method="risk_parity",
            timeframe="1d",
            generate_chart=True,
            chart_save_path="/tmp/test.png"
        )

        assert task.initial_cash == 500000.0
        assert task.strategy_name == "sma_cross"
        assert task.optimization_method == "risk_parity"
        assert task.rebalance_config is not None

    def test_to_dict(self):
        """Test serialization to dictionary."""
        task = MultiAssetBacktestTask(
            task_id="test-789",
            tickers=["AAPL"],
            weights=[1.0],
            start_date="2024-01-01",
            end_date="2024-12-31"
        )

        data = task.to_dict()

        assert data["task_id"] == "test-789"
        assert data["tickers"] == ["AAPL"]
        assert data["weights"] == [1.0]
        assert data["optimization_method"] == "equal_weight"

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "task_id": "test-abc",
            "tickers": ["AAPL", "GOOGL"],
            "weights": [0.6, 0.4],
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "optimization_method": "markowitz"
        }

        task = MultiAssetBacktestTask.from_dict(data)

        assert task.task_id == "test-abc"
        assert task.optimization_method == "markowitz"

    def test_roundtrip_serialization(self):
        """Test to_dict -> from_dict roundtrip."""
        original = MultiAssetBacktestTask(
            task_id="roundtrip-test",
            tickers=["AAPL", "GOOGL", "MSFT"],
            weights=[0.33, 0.34, 0.33],
            start_date="2024-01-01",
            end_date="2024-12-31",
            optimization_method="risk_parity"
        )

        data = original.to_dict()
        restored = MultiAssetBacktestTask.from_dict(data)

        assert restored.task_id == original.task_id
        assert restored.tickers == original.tickers
        assert restored.optimization_method == original.optimization_method


class TestMultiAssetBacktestResult:
    """Tests for MultiAssetBacktestResult dataclass."""

    def test_create_success_result(self):
        """Test creating a successful result."""
        result = MultiAssetBacktestResult(
            task_id="test-123",
            status=TaskStatus.COMPLETED,
            final_value=125000.0,
            total_return=25.0,
            sharpe_ratio=1.5,
            max_drawdown=-8.5
        )

        assert result.task_id == "test-123"
        assert result.status == TaskStatus.COMPLETED
        assert result.final_value == 125000.0
        assert result.total_return == 25.0

    def test_create_error_result(self):
        """Test creating an error result."""
        result = MultiAssetBacktestResult.error_result(
            task_id="test-err",
            error="Data load failed",
            error_type="DataLoadError"
        )

        assert result.task_id == "test-err"
        assert result.status == TaskStatus.FAILED
        assert result.error == "Data load failed"
        assert result.error_type == "DataLoadError"

    def test_to_dict(self):
        """Test serialization to dictionary."""
        result = MultiAssetBacktestResult(
            task_id="test-456",
            status=TaskStatus.COMPLETED,
            final_value=110000.0,
            equity_curve={"2024-01-01": 100000, "2024-01-02": 101000}
        )

        data = result.to_dict()

        assert data["task_id"] == "test-456"
        assert data["status"] == "completed"
        assert data["equity_curve"] == {"2024-01-01": 100000, "2024-01-02": 101000}

    def test_from_dict_with_string_status(self):
        """Test deserialization with string status."""
        data = {
            "task_id": "test-789",
            "status": "completed",
            "final_value": 120000.0
        }

        result = MultiAssetBacktestResult.from_dict(data)

        assert result.status == TaskStatus.COMPLETED

    def test_from_dict_with_enum_status(self):
        """Test deserialization with enum status."""
        data = {
            "task_id": "test-abc",
            "status": TaskStatus.FAILED,
            "error": "Test error"
        }

        result = MultiAssetBacktestResult.from_dict(data)

        assert result.status == TaskStatus.FAILED
        assert result.error == "Test error"

    def test_result_with_memory_tracking(self):
        """Test result with memory tracking."""
        result = MultiAssetBacktestResult(
            task_id="test-mem",
            status=TaskStatus.COMPLETED,
            final_value=100000.0,
            peak_memory_mb=512.5,
            duration_seconds=45.3
        )

        assert result.peak_memory_mb == 512.5
        assert result.duration_seconds == 45.3


class TestMultiAssetWorkerExecution:
    """Tests for multi-asset worker execution."""

    @patch("src.service.multi_asset_backtest.run_multi_asset_backtest")
    def test_execute_task_success(self, mock_run):
        """Test successful task execution."""
        from src.service.worker.multi_asset_worker import execute_multi_asset_task

        mock_run.return_value = {
            "final_value": 125000.0,
            "total_return": 25.0,
            "sharpe_ratio": 1.5,
            "max_drawdown": -8.0,
            "equity_curve": {"2024-01-01": 100000},
            "rebalancing_events": [],
            "asset_contributions": {},
            "optimization_history": [],
            "per_asset_results": {}
        }

        task = MultiAssetBacktestTask(
            task_id="exec-test",
            tickers=["AAPL", "GOOGL"],
            weights=[0.5, 0.5],
            start_date="2024-01-01",
            end_date="2024-12-31"
        )

        result = execute_multi_asset_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert result.final_value == 125000.0
        assert result.total_return == 25.0

    @patch("src.service.multi_asset_backtest.run_multi_asset_backtest")
    def test_execute_task_failure(self, mock_run):
        """Test task execution with failure."""
        from src.service.worker.multi_asset_worker import execute_multi_asset_task

        mock_run.side_effect = Exception("Data load failed")

        task = MultiAssetBacktestTask(
            task_id="exec-fail",
            tickers=["INVALID"],
            weights=[1.0],
            start_date="2024-01-01",
            end_date="2024-12-31"
        )

        result = execute_multi_asset_task(task)

        assert result.status == TaskStatus.FAILED
        assert "Data load failed" in result.error


class TestMemoryMonitoring:
    """Tests for memory monitoring utilities."""

    def test_get_memory_usage(self):
        """Test memory usage retrieval."""
        from src.service.worker.multi_asset_worker import get_memory_usage_mb

        memory = get_memory_usage_mb()

        # Should return a non-negative number
        assert memory >= 0.0

    def test_get_memory_usage_with_psutil(self):
        """Test memory usage with mocked psutil."""
        import psutil
        with patch.object(psutil, 'Process') as mock_process_class:
            mock_process = MagicMock()
            mock_process.memory_info.return_value = MagicMock(rss=512 * 1024 * 1024)
            mock_process_class.return_value = mock_process

            from src.service.worker.multi_asset_worker import get_memory_usage_mb
            memory = get_memory_usage_mb()

            # psutil.Process() was called
            mock_process_class.assert_called_once()
            assert abs(memory - 512.0) < 0.01

    def test_get_memory_usage_handles_errors(self):
        """Test memory usage gracefully handles errors."""
        import psutil
        with patch.object(psutil, 'Process') as mock_process_class:
            mock_process_class.side_effect = Exception("Process error")

            from src.service.worker.multi_asset_worker import get_memory_usage_mb
            memory = get_memory_usage_mb()

            # Should return 0.0 on error
            assert memory == 0.0


class TestWorkerPoolIntegration:
    """Tests for worker pool integration."""

    def test_task_models_exported(self):
        """Test that task models are properly exported."""
        from src.service.worker.task_models import (
            MultiAssetBacktestTask,
            MultiAssetBacktestResult,
        )

        assert MultiAssetBacktestTask is not None
        assert MultiAssetBacktestResult is not None

    def test_worker_pool_has_multi_asset_methods(self):
        """Test that worker pool has multi-asset methods."""
        from src.service.worker.worker_pool import WorkerPool

        pool = WorkerPool()

        assert hasattr(pool, "submit_multi_asset_backtest")
        assert hasattr(pool, "get_multi_asset_result")
        assert hasattr(pool, "submit_multi_asset_backtest_sync")
        assert hasattr(pool, "_execute_multi_asset_in_process")
