"""
Unit tests for defaults contracts module.
"""
import pytest

from src.contracts.defaults import (
    BacktestDefaults,
    BACKTEST_DEFAULTS,
    TIMEFRAME_OPTIONS,
    SIZER_TYPE_OPTIONS,
    OPTIMIZATION_METRIC_OPTIONS,
)


class TestBacktestDefaults:
    """Tests for BacktestDefaults dataclass."""

    def test_default_values(self):
        """Test that defaults have expected values."""
        assert BACKTEST_DEFAULTS.INITIAL_CASH == 100000.0
        assert BACKTEST_DEFAULTS.COMMISSION == 0.0005
        assert BACKTEST_DEFAULTS.STAKE == 100
        assert BACKTEST_DEFAULTS.TIMEFRAME == "1d"
        assert BACKTEST_DEFAULTS.SIZER_TYPE == "fixed_size"

    def test_walkforward_defaults(self):
        """Test walk-forward specific defaults."""
        assert BACKTEST_DEFAULTS.TRAIN_PERIOD_DAYS == 365
        assert BACKTEST_DEFAULTS.TEST_PERIOD_DAYS == 90
        assert BACKTEST_DEFAULTS.ANCHORED is False
        assert BACKTEST_DEFAULTS.OPTIMIZATION_METRIC == "sharpe_ratio"

    def test_live_trading_defaults(self):
        """Test live trading specific defaults."""
        assert BACKTEST_DEFAULTS.LIVE_INITIAL_CASH == 10000.0
        assert BACKTEST_DEFAULTS.LIVE_COMMISSION == 0.001

    def test_sizer_defaults(self):
        """Test sizer configuration defaults."""
        assert BACKTEST_DEFAULTS.SIZER_PERCENT == 10.0
        assert BACKTEST_DEFAULTS.SIZER_RISK_PERCENT == 2.0

    def test_defaults_are_frozen(self):
        """Test that defaults cannot be modified (frozen dataclass)."""
        with pytest.raises(AttributeError):
            BACKTEST_DEFAULTS.INITIAL_CASH = 50000.0

    def test_singleton_instance(self):
        """Test that BACKTEST_DEFAULTS is the canonical instance."""
        assert isinstance(BACKTEST_DEFAULTS, BacktestDefaults)


class TestOptionLists:
    """Tests for option list constants."""

    def test_timeframe_options(self):
        """Test timeframe options list."""
        assert TIMEFRAME_OPTIONS == ["1d", "1h", "15m", "5m", "1m"]
        assert len(TIMEFRAME_OPTIONS) == 5
        assert BACKTEST_DEFAULTS.TIMEFRAME in TIMEFRAME_OPTIONS

    def test_sizer_type_options(self):
        """Test sizer type options list."""
        expected = ["fixed_size", "percent_sizer", "all_in_sizer", "risk_sizer", "kelly_sizer"]
        assert SIZER_TYPE_OPTIONS == expected
        assert BACKTEST_DEFAULTS.SIZER_TYPE in SIZER_TYPE_OPTIONS

    def test_optimization_metric_options(self):
        """Test optimization metric options list."""
        expected = ["sharpe_ratio", "total_return", "profit_factor"]
        assert OPTIMIZATION_METRIC_OPTIONS == expected
        assert BACKTEST_DEFAULTS.OPTIMIZATION_METRIC in OPTIMIZATION_METRIC_OPTIONS


class TestModuleExports:
    """Tests for module exports."""

    def test_all_exports_available(self):
        """Test that all expected exports are available."""
        from src.contracts import (
            BacktestDefaults,
            BACKTEST_DEFAULTS,
            TIMEFRAME_OPTIONS,
            SIZER_TYPE_OPTIONS,
            OPTIMIZATION_METRIC_OPTIONS,
        )
        assert BacktestDefaults is not None
        assert BACKTEST_DEFAULTS is not None
        assert TIMEFRAME_OPTIONS is not None
        assert SIZER_TYPE_OPTIONS is not None
        assert OPTIMIZATION_METRIC_OPTIONS is not None
