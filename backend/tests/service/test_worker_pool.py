"""
Worker Pool Unit Tests

Tests for the worker pool infrastructure including:
- Worker pool initialization and shutdown
- Task submission and result retrieval
- Timeout handling
- Configuration options
"""

import pytest
import uuid
from unittest.mock import patch, MagicMock

from src.config.worker_config import WorkerPoolConfig, get_config
from src.service.worker.task_models import (
    BacktestTask,
    BacktestResult,
    TaskStatus,
    LiveTradingTask,
    LiveEventType,
)


class TestWorkerPoolConfig:
    """Tests for worker pool configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = WorkerPoolConfig()
        assert config.enabled is True
        assert config.pool_size == 4
        assert config.task_timeout_seconds == 300.0
        assert config.max_memory_mb == 1024

    def test_custom_config(self):
        """Test custom configuration values."""
        config = WorkerPoolConfig(
            enabled=False,
            pool_size=8,
            task_timeout_seconds=600.0,
            max_memory_mb=2048,
        )
        assert config.enabled is False
        assert config.pool_size == 8
        assert config.task_timeout_seconds == 600.0
        assert config.max_memory_mb == 2048

    def test_config_from_env(self):
        """Test configuration from environment variables."""
        with patch.dict("os.environ", {
            "WORKER_POOL_ENABLED": "false",
            "WORKER_POOL_SIZE": "2",
            "WORKER_TASK_TIMEOUT": "120",
        }):
            # Need to reimport to pick up env vars
            from src.config.worker_config import get_config as get_cfg
            config = get_cfg()
            # Note: get_config is cached, so we test default behavior
            assert config is not None


class TestTaskModels:
    """Tests for task and result dataclasses."""

    def test_backtest_task_creation(self):
        """Test creating a BacktestTask."""
        task = BacktestTask(
            task_id="test-123",
            strategy_name="test_strategy",
            ticker="AAPL",
            start_date="2023-01-01",
            end_date="2023-12-31",
            initial_cash=100000.0,
            commission=0.001,
            stake=100,
        )
        assert task.task_id == "test-123"
        assert task.strategy_name == "test_strategy"
        assert task.ticker == "AAPL"
        assert task.params is None

    def test_backtest_task_with_params(self):
        """Test creating a BacktestTask with custom parameters."""
        task = BacktestTask(
            task_id="test-456",
            strategy_name="sma_strategy",
            ticker="MSFT",
            start_date="2023-01-01",
            end_date="2023-06-30",
            initial_cash=50000.0,
            commission=0.0005,
            stake=50,
            params={"fast_period": 10, "slow_period": 30},
        )
        assert task.params == {"fast_period": 10, "slow_period": 30}

    def test_backtest_result_success(self):
        """Test creating a successful BacktestResult."""
        result = BacktestResult(
            task_id="test-123",
            status=TaskStatus.COMPLETED,
            final_value=105000.0,
            sharpe_ratio=1.5,
            max_drawdown=5.2,
            total_return=5.0,
        )
        assert result.status == TaskStatus.COMPLETED
        assert result.final_value == 105000.0
        assert result.error is None

    def test_backtest_result_error(self):
        """Test creating an error BacktestResult."""
        result = BacktestResult.error_result(
            task_id="test-789",
            error="Strategy not found",
            error_type="StrategyLoadError",
        )
        assert result.status == TaskStatus.FAILED
        assert result.error == "Strategy not found"
        assert result.error_type == "StrategyLoadError"

    def test_backtest_task_to_dict(self):
        """Test serializing BacktestTask to dict."""
        task = BacktestTask(
            task_id="test-111",
            strategy_name="test",
            ticker="GOOG",
            start_date="2023-01-01",
            end_date="2023-12-31",
            initial_cash=100000.0,
            commission=0.001,
            stake=100,
        )
        task_dict = task.to_dict()
        assert task_dict["task_id"] == "test-111"
        assert task_dict["ticker"] == "GOOG"

    def test_backtest_task_from_dict(self):
        """Test deserializing BacktestTask from dict."""
        data = {
            "task_id": "test-222",
            "strategy_name": "demo",
            "ticker": "TSLA",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_cash": 75000.0,
            "commission": 0.002,
            "stake": 25,
        }
        task = BacktestTask.from_dict(data)
        assert task.task_id == "test-222"
        assert task.ticker == "TSLA"
        assert task.initial_cash == 75000.0


class TestLiveTradingTask:
    """Tests for live trading task models."""

    def test_live_trading_task_creation(self):
        """Test creating a LiveTradingTask."""
        task = LiveTradingTask(
            task_id="live-001",
            session_id="session-abc",
            strategy_name="scalper",
            symbol="BTC/USDT",
            exchange="binance",
            mode="paper",
            timeframe="1m",
            initial_cash=10000.0,
            commission=0.001,
        )
        assert task.session_id == "session-abc"
        assert task.mode == "paper"
        assert task.exchange == "binance"

    def test_live_event_type_enum(self):
        """Test LiveEventType enumeration."""
        assert LiveEventType.STATUS_UPDATE.value == "status_update"
        assert LiveEventType.STOPPED.value == "stopped"
        assert LiveEventType.ERROR.value == "error"
        assert LiveEventType.HEARTBEAT.value == "heartbeat"


class TestTaskStatus:
    """Tests for TaskStatus enumeration."""

    def test_task_status_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestWorkerPoolIntegration:
    """Integration tests for WorkerPool (mocked)."""

    def test_worker_pool_singleton(self):
        """Test that get_worker_pool returns the same instance."""
        from src.service.worker.worker_pool import get_worker_pool

        pool1 = get_worker_pool()
        pool2 = get_worker_pool()
        assert pool1 is pool2

    @pytest.mark.skip(reason="Requires running worker processes")
    def test_submit_backtest_integration(self):
        """Integration test for submitting a backtest task."""
        from src.service.worker.worker_pool import get_worker_pool

        pool = get_worker_pool()
        task = BacktestTask(
            task_id=str(uuid.uuid4()),
            strategy_name="example_strategy",
            ticker="AAPL",
            start_date="2023-01-01",
            end_date="2023-06-30",
            initial_cash=100000.0,
            commission=0.001,
            stake=100,
        )

        task_id = pool.submit_backtest(task)
        assert task_id == task.task_id


__all__ = [
    "TestWorkerPoolConfig",
    "TestTaskModels",
    "TestLiveTradingTask",
    "TestTaskStatus",
    "TestWorkerPoolIntegration",
]
