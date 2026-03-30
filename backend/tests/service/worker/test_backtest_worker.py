"""
Unit tests for backtest worker module.
"""
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import backtrader as bt
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

    def test_execution_logs_are_included_in_successful_result_metrics(self):
        """Worker should return detailed execution logs captured during the run."""
        from src.service.worker.backtest_worker import execute_backtest_task
        from src.service.worker.task_models import BacktestTask, TaskStatus

        class DummyStrategy(bt.Strategy):
            pass

        class FakeBroker:
            def setcash(self, _cash):
                return None

            def setcommission(self, commission=0.0):
                return None

            def getvalue(self):
                return 123456.78

        class FakeCerebro:
            def __init__(self):
                self.broker = FakeBroker()

            def addstrategy(self, *args, **kwargs):
                return None

            def adddata(self, _data):
                return None

            def addsizer(self, *args, **kwargs):
                return None

            def run(self):
                logging.getLogger("worker-test").info("worker logger message")
                print("worker printed message")
                return [MagicMock()]

        task = BacktestTask(
            task_id="task-success-logs",
            strategy_name="KDJ",
            ticker="AAPL",
            start_date="2024-01-01",
            end_date="2024-02-01",
            generate_chart=False,
        )

        metrics_payload = {
            "final_value": 123456.78,
            "sharpe_ratio": 1.23,
            "max_drawdown": 4.56,
            "total_return": 7.89,
            "annual_returns": {},
            "trade_details": {},
            "equity_curve": {},
        }

        with (
            patch("backtrader.Cerebro", FakeCerebro),
            patch("src.db.storage.market_data.get_bt_feed", return_value=MagicMock()),
            patch("src.db.storage.market_data.get_raw_data_json", return_value={}),
            patch("src.service.strategy_repo.read_user_strategy_source", return_value=(Path("KDJ.py"), "class UserStrategy: pass")),
            patch("src.service.strategy_data_requirements.estimate_strategy_min_bars", return_value=None),
            patch("src.service.strategy_data_requirements.count_data_bars", return_value=50),
            patch("src.service.strategy_sandbox.execute_strategy_code", return_value={"UserStrategy": DummyStrategy}),
            patch("src.service.analyzer_config.configure_analyzers"),
            patch("src.service.analyzer_config.extract_metrics", return_value=metrics_payload.copy()),
            patch("src.service.chart_data_extractor.build_backtest_chart_data", return_value={}),
        ):
            result = execute_backtest_task(task)

        assert result.status == TaskStatus.COMPLETED
        assert result.metrics is not None
        execution_logs = result.metrics.get("execution_logs") or []
        assert any("worker logger message" in entry["message"] for entry in execution_logs)
        assert any("worker printed message" in entry["message"] for entry in execution_logs)
