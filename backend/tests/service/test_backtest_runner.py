"""
Unit tests for backtest runner module.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestBacktestRunnerImports:
    """Tests for backtest runner module imports."""

    def test_module_import(self):
        """Test that backtest runner module can be imported."""
        from src.service import backtest_runner
        assert backtest_runner is not None

    def test_run_backtest_worker_import(self):
        """Test that run_backtest_worker function can be imported."""
        from src.service.backtest_runner import run_backtest_worker
        assert run_backtest_worker is not None
        assert callable(run_backtest_worker)

    def test_run_backtest_legacy_import(self):
        """Test that run_backtest_legacy function can be imported."""
        from src.service.backtest_runner import run_backtest_legacy
        assert run_backtest_legacy is not None
        assert callable(run_backtest_legacy)

    def test_backtest_runner_error_import(self):
        """Test that BacktestRunnerError can be imported."""
        from src.service.backtest_runner import BacktestRunnerError
        assert BacktestRunnerError is not None
        assert issubclass(BacktestRunnerError, Exception)


class TestBacktestRunnerError:
    """Tests for BacktestRunnerError exception."""

    def test_error_with_message(self):
        """Test raising BacktestRunnerError with message."""
        from src.service.backtest_runner import BacktestRunnerError
        with pytest.raises(BacktestRunnerError) as excinfo:
            raise BacktestRunnerError("Backtest timed out")
        assert "Backtest timed out" in str(excinfo.value)
