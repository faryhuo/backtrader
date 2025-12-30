"""
Unit tests for contracts exceptions module.
"""
import pytest

from src.contracts.exceptions import (
    StrategyLoadError,
    DataLoadError,
    BacktestError,
)


class TestStrategyLoadError:
    """Tests for StrategyLoadError exception."""

    def test_strategy_load_error_message(self):
        """Test that StrategyLoadError can be raised with a message."""
        with pytest.raises(StrategyLoadError) as excinfo:
            raise StrategyLoadError("Failed to load strategy: syntax error")
        assert "Failed to load strategy" in str(excinfo.value)

    def test_strategy_load_error_no_message(self):
        """Test that StrategyLoadError can be raised without a message."""
        with pytest.raises(StrategyLoadError):
            raise StrategyLoadError()

    def test_strategy_load_error_inheritance(self):
        """Test that StrategyLoadError inherits from Exception."""
        assert issubclass(StrategyLoadError, Exception)


class TestDataLoadError:
    """Tests for DataLoadError exception."""

    def test_data_load_error_message(self):
        """Test that DataLoadError can be raised with a message."""
        with pytest.raises(DataLoadError) as excinfo:
            raise DataLoadError("Failed to load data for AAPL")
        assert "AAPL" in str(excinfo.value)

    def test_data_load_error_no_message(self):
        """Test that DataLoadError can be raised without a message."""
        with pytest.raises(DataLoadError):
            raise DataLoadError()

    def test_data_load_error_inheritance(self):
        """Test that DataLoadError inherits from Exception."""
        assert issubclass(DataLoadError, Exception)


class TestBacktestError:
    """Tests for BacktestError exception."""

    def test_backtest_error_message(self):
        """Test that BacktestError can be raised with a message."""
        with pytest.raises(BacktestError) as excinfo:
            raise BacktestError("Backtest execution failed")
        assert "Backtest execution failed" in str(excinfo.value)

    def test_backtest_error_no_message(self):
        """Test that BacktestError can be raised without a message."""
        with pytest.raises(BacktestError):
            raise BacktestError()

    def test_backtest_error_inheritance(self):
        """Test that BacktestError inherits from Exception."""
        assert issubclass(BacktestError, Exception)


class TestExceptionCatching:
    """Tests for exception catching behavior."""

    def test_catch_strategy_load_error_as_exception(self):
        """Test that StrategyLoadError can be caught as Exception."""
        try:
            raise StrategyLoadError("test")
        except Exception as e:
            assert isinstance(e, StrategyLoadError)

    def test_catch_data_load_error_as_exception(self):
        """Test that DataLoadError can be caught as Exception."""
        try:
            raise DataLoadError("test")
        except Exception as e:
            assert isinstance(e, DataLoadError)

    def test_catch_backtest_error_as_exception(self):
        """Test that BacktestError can be caught as Exception."""
        try:
            raise BacktestError("test")
        except Exception as e:
            assert isinstance(e, BacktestError)
