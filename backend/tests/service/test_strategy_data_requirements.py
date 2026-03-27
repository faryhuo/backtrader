"""
Unit tests for strategy data requirement helpers.
"""

from src.service.strategy_data_requirements import (
    estimate_strategy_min_bars,
    format_insufficient_data_error,
)
from src.service.strategy_repo import read_user_strategy_source


def test_estimate_strategy_min_bars_for_kdj_strategy():
    """KDJ should require enough bars for stochastic smoothing."""
    _, source = read_user_strategy_source("KDJ")

    assert estimate_strategy_min_bars(source) == 18


def test_estimate_strategy_min_bars_uses_runtime_param_overrides():
    """Runtime params should override defaults when estimating lookback."""
    _, source = read_user_strategy_source("KDJ")

    assert estimate_strategy_min_bars(source, {"period_k": 9, "period_d": 5}) == 15


def test_format_insufficient_data_error_includes_counts_and_dates():
    """The user-facing message should include exact bar counts and dates."""
    message = format_insufficient_data_error(
        strategy_name="KDJ",
        ticker="AAPL",
        timeframe="1d",
        start_date="2026-03-22",
        end_date="2026-03-27",
        available_bars=4,
        required_bars=18,
    )

    assert "2026-03-22 to 2026-03-27" in message
    assert "returned 4 bars" in message
    assert "at least 18 bars" in message
