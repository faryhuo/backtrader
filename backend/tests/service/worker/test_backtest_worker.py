"""
Unit tests for backtest worker module.
"""
from pathlib import Path
from unittest.mock import patch

from src.service.strategy_repo import read_user_strategy_source


class TestBacktestWorkerImports:
    """Tests for backtest worker module imports."""

    def test_module_import(self):
        """Test that backtest worker module can be imported."""
        from src.service.worker import backtest_worker
        assert backtest_worker is not None


class TestBacktestWorker:
    """Tests for backtest worker functionality."""

    def test_has_worker_class(self):
        """Test that module has worker-related classes or functions."""
        from src.service.worker import backtest_worker
        assert backtest_worker is not None

    def test_returns_insufficient_data_error_before_strategy_execution(self):
        """Short datasets should fail early with a friendly error."""
        from src.service.worker.backtest_worker import execute_backtest_task
        from src.service.worker.task_models import BacktestTask, TaskStatus

        _, source = read_user_strategy_source("KDJ")

        class FakeFeed:
            def __init__(self, size):
                self.p = type("FeedParams", (), {"dataname": [None] * size})()

        task = BacktestTask(
            task_id="task-123",
            strategy_name="KDJ",
            ticker="AAPL",
            start_date="2026-03-22",
            end_date="2026-03-27",
            generate_chart=False,
        )

        with (
            patch(
                "src.service.strategy_repo.read_user_strategy_source",
                return_value=(Path("KDJ.py"), source),
            ),
            patch("src.db.storage.market_data.get_bt_feed", return_value=FakeFeed(4)),
            patch("src.service.strategy_sandbox.execute_strategy_code") as mock_execute_strategy,
        ):
            result = execute_backtest_task(task)

        assert result.status == TaskStatus.FAILED
        assert result.error_type == "InsufficientDataError"
        assert "returned 4 bars" in result.error
        assert "at least 18 bars" in result.error
        mock_execute_strategy.assert_not_called()
