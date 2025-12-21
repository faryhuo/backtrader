"""
Deep Analysis Service - Compute advanced backtest analytics.

Provides comprehensive analysis of backtest results including:
- Monthly returns heatmap
- Rolling Sharpe ratio with benchmark comparison
- Returns distribution
- Drawdown distribution
- Consecutive losing periods
- Benchmark comparison (alpha, beta, correlation)
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.db.storage.market_data import get_data, DataLoadError

logger = logging.getLogger(__name__)

# Default benchmarks
DEFAULT_BENCHMARKS = ["SPY", "000300.SS"]
DEFAULT_ROLLING_WINDOW = 60
DEFAULT_RISK_FREE_RATE = 0.02


class DeepAnalysisError(Exception):
    """Raised when deep analysis computation fails."""


def compute_deep_analysis(
    equity_curve: Dict[datetime, float],
    start_date: str,
    end_date: str,
    initial_cash: float = 100000.0,
    benchmarks: Optional[List[str]] = None,
    risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
    rolling_window: int = DEFAULT_ROLLING_WINDOW,
) -> Dict[str, Any]:
    """
    Compute comprehensive deep analysis for a backtest.

    Args:
        equity_curve: Dict mapping dates to daily returns (from TimeReturn analyzer)
        start_date: Backtest start date (YYYY-MM-DD)
        end_date: Backtest end date (YYYY-MM-DD)
        initial_cash: Initial portfolio value
        benchmarks: List of benchmark tickers to compare against
        risk_free_rate: Annual risk-free rate for Sharpe calculation
        rolling_window: Window size for rolling calculations (days)

    Returns:
        Dict containing all analysis results
    """
    if benchmarks is None:
        benchmarks = DEFAULT_BENCHMARKS

    if not equity_curve:
        raise DeepAnalysisError("Equity curve is empty - cannot compute analysis")

    # Convert equity curve to pandas Series of daily returns
    daily_returns = _equity_curve_to_returns(equity_curve)

    if daily_returns.empty or len(daily_returns) < 5:
        raise DeepAnalysisError(
            f"Insufficient data points ({len(daily_returns)}) - need at least 5 trading days"
        )

    # Compute cumulative equity from returns
    cumulative_equity = (1 + daily_returns).cumprod() * initial_cash

    # Fetch benchmark data
    benchmark_returns = {}
    for ticker in benchmarks:
        try:
            bench_ret = fetch_benchmark_returns(ticker, start_date, end_date)
            if bench_ret is not None and not bench_ret.empty:
                # Align benchmark to strategy dates
                aligned = bench_ret.reindex(daily_returns.index).ffill().dropna()
                if len(aligned) >= len(daily_returns) * 0.5:  # At least 50% overlap
                    benchmark_returns[ticker] = aligned
                else:
                    logger.warning(
                        f"Benchmark {ticker} has insufficient overlap with strategy dates"
                    )
        except Exception as e:
            logger.warning(f"Failed to fetch benchmark {ticker}: {e}")

    # Compute all analyses
    result = {
        "computed_at": datetime.utcnow().isoformat() + "Z",
        "config": {
            "benchmarks": benchmarks,
            "rolling_window": rolling_window,
            "risk_free_rate": risk_free_rate,
        },
        "monthly_returns": compute_monthly_returns(daily_returns),
        "rolling_sharpe": compute_rolling_sharpe(
            daily_returns, benchmark_returns, rolling_window, risk_free_rate
        ),
        "returns_distribution": compute_returns_distribution(
            daily_returns, benchmark_returns
        ),
        "drawdown_distribution": compute_drawdown_distribution(cumulative_equity),
        "consecutive_losses": compute_consecutive_losses(daily_returns),
        "benchmark_comparison": compute_benchmark_comparison(
            daily_returns, benchmark_returns, risk_free_rate
        ),
    }

    return result


def _equity_curve_to_returns(equity_curve: Dict[datetime, float]) -> pd.Series:
    """
    Convert equity curve dict to daily returns Series.

    The equity_curve from TimeReturn analyzer contains {datetime: return} pairs
    where return is the daily percentage return.
    """
    if not equity_curve:
        return pd.Series(dtype=float)

    # Convert to Series and sort by date
    returns_data = {}
    for date_key, return_val in equity_curve.items():
        # Handle both datetime objects and date objects
        if isinstance(date_key, datetime):
            date = date_key.date()
        else:
            date = date_key
        returns_data[pd.Timestamp(date)] = float(return_val)

    series = pd.Series(returns_data)
    series = series.sort_index()
    series.index.name = "Date"

    return series


def fetch_benchmark_returns(
    ticker: str, start_date: str, end_date: str
) -> Optional[pd.Series]:
    """
    Fetch benchmark data and return daily returns.

    Args:
        ticker: Benchmark ticker (e.g., "SPY", "000300.SS")
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)

    Returns:
        pd.Series of daily returns, or None if fetch fails
    """
    try:
        data = get_data(ticker, start_date, end_date)
        if data is None or data.empty:
            return None

        # Compute daily returns from close prices
        close = data["Close"] if "Close" in data.columns else data["close"]
        returns = close.pct_change().dropna()
        returns.index = pd.to_datetime(returns.index)

        return returns

    except (DataLoadError, Exception) as e:
        logger.warning(f"Failed to fetch benchmark {ticker}: {e}")
        return None


def compute_monthly_returns(daily_returns: pd.Series) -> Dict[str, Any]:
    """
    Compute monthly returns matrix for heatmap display.

    Returns:
        Dict with years, months, and matrix data for heatmap
    """
    if daily_returns.empty:
        return {"years": [], "months": [], "matrix": []}

    # Resample to monthly returns
    monthly = daily_returns.resample("M").apply(lambda x: (1 + x).prod() - 1)

    # Extract years and build matrix
    years = sorted(monthly.index.year.unique())
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    matrix = []
    for year in years:
        year_data = []
        for month_idx in range(1, 13):
            # Find return for this year-month
            matches = monthly[(monthly.index.year == year) &
                              (monthly.index.month == month_idx)]
            if not matches.empty:
                year_data.append(round(float(matches.iloc[0]), 4))
            else:
                year_data.append(None)  # No data for this month
        matrix.append(year_data)

    return {
        "years": [int(y) for y in years],
        "months": months,
        "matrix": matrix,
    }


def compute_rolling_sharpe(
    daily_returns: pd.Series,
    benchmark_returns: Dict[str, pd.Series],
    window: int = DEFAULT_ROLLING_WINDOW,
    risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
) -> Dict[str, Any]:
    """
    Compute rolling Sharpe ratio for strategy and benchmarks.

    Returns:
        Dict with window size and series data for each ticker
    """
    result = {"window": window}

    # Daily risk-free rate
    daily_rf = risk_free_rate / 252

    def _rolling_sharpe(returns: pd.Series) -> List[Dict[str, Any]]:
        if len(returns) < window:
            return []

        rolling_mean = returns.rolling(window).mean()
        rolling_std = returns.rolling(window).std()

        # Annualized Sharpe
        sharpe = ((rolling_mean - daily_rf) * np.sqrt(252)) / rolling_std
        sharpe = sharpe.dropna()

        return [
            {"date": date.strftime("%Y-%m-%d"), "value": round(float(val), 4)}
            for date, val in sharpe.items()
            if not np.isnan(val) and not np.isinf(val)
        ]

    # Strategy rolling Sharpe
    result["strategy"] = _rolling_sharpe(daily_returns)

    # Benchmark rolling Sharpe
    for ticker, bench_ret in benchmark_returns.items():
        result[ticker] = _rolling_sharpe(bench_ret)

    return result


def compute_returns_distribution(
    daily_returns: pd.Series,
    benchmark_returns: Dict[str, pd.Series],
    num_bins: int = 50,
) -> Dict[str, Any]:
    """
    Compute returns distribution histogram and statistics.

    Returns:
        Dict with bins, counts, and statistical measures
    """
    returns_array = daily_returns.dropna().values

    if len(returns_array) < 2:
        return {
            "bins": [],
            "strategy_counts": [],
            "benchmark_counts": {},
            "statistics": {},
        }

    # Compute histogram bins based on strategy returns
    min_val = np.percentile(returns_array, 1)  # 1st percentile
    max_val = np.percentile(returns_array, 99)  # 99th percentile
    bins = np.linspace(min_val, max_val, num_bins + 1)

    strategy_counts, _ = np.histogram(returns_array, bins=bins)

    # Benchmark counts
    benchmark_counts = {}
    for ticker, bench_ret in benchmark_returns.items():
        counts, _ = np.histogram(bench_ret.dropna().values, bins=bins)
        benchmark_counts[ticker] = counts.tolist()

    # Statistical measures
    statistics = {
        "mean": round(float(np.mean(returns_array)), 6),
        "std": round(float(np.std(returns_array)), 6),
        "skewness": round(float(_compute_skewness(returns_array)), 4),
        "kurtosis": round(float(_compute_kurtosis(returns_array)), 4),
        "var_95": round(float(np.percentile(returns_array, 5)), 6),
        "cvar_95": round(float(_compute_cvar(returns_array, 0.05)), 6),
        "min": round(float(np.min(returns_array)), 6),
        "max": round(float(np.max(returns_array)), 6),
    }

    return {
        "bins": [round(float(b), 6) for b in bins],
        "strategy_counts": strategy_counts.tolist(),
        "benchmark_counts": benchmark_counts,
        "statistics": statistics,
    }


def _compute_skewness(returns: np.ndarray) -> float:
    """Compute skewness of returns."""
    n = len(returns)
    if n < 3:
        return 0.0
    mean = np.mean(returns)
    std = np.std(returns, ddof=1)
    if std == 0:
        return 0.0
    return (n / ((n - 1) * (n - 2))) * np.sum(((returns - mean) / std) ** 3)


def _compute_kurtosis(returns: np.ndarray) -> float:
    """Compute excess kurtosis of returns."""
    n = len(returns)
    if n < 4:
        return 0.0
    mean = np.mean(returns)
    std = np.std(returns, ddof=1)
    if std == 0:
        return 0.0
    m4 = np.mean((returns - mean) ** 4)
    return (m4 / (std ** 4)) - 3


def _compute_cvar(returns: np.ndarray, alpha: float = 0.05) -> float:
    """Compute Conditional Value at Risk (Expected Shortfall)."""
    var = np.percentile(returns, alpha * 100)
    return np.mean(returns[returns <= var])


def compute_drawdown_distribution(equity_curve: pd.Series) -> Dict[str, Any]:
    """
    Compute drawdown analysis including distribution and periods.

    Args:
        equity_curve: Cumulative equity curve (portfolio value over time)

    Returns:
        Dict with drawdown distribution and period analysis
    """
    if equity_curve.empty or len(equity_curve) < 2:
        return {
            "bins": [],
            "counts": [],
            "max_drawdown": 0,
            "avg_drawdown": 0,
            "drawdown_periods": [],
        }

    # Compute drawdown series
    running_max = equity_curve.cummax()
    drawdown = (equity_curve - running_max) / running_max

    # Drawdown distribution (histogram of all drawdown values)
    dd_values = drawdown.values
    dd_values = dd_values[dd_values < 0]  # Only negative values

    if len(dd_values) == 0:
        return {
            "bins": [],
            "counts": [],
            "max_drawdown": 0,
            "avg_drawdown": 0,
            "drawdown_periods": [],
        }

    bins = np.linspace(dd_values.min(), 0, 21)
    counts, _ = np.histogram(dd_values, bins=bins)

    # Identify drawdown periods
    drawdown_periods = _identify_drawdown_periods(drawdown)

    return {
        "bins": [round(float(b), 4) for b in bins],
        "counts": counts.tolist(),
        "max_drawdown": round(float(dd_values.min()), 4),
        "avg_drawdown": round(float(np.mean(dd_values)), 4),
        "drawdown_periods": drawdown_periods,
    }


def _identify_drawdown_periods(
    drawdown: pd.Series, min_depth: float = -0.01
) -> List[Dict[str, Any]]:
    """
    Identify distinct drawdown periods.

    Args:
        drawdown: Series of drawdown values (negative)
        min_depth: Minimum drawdown depth to include (-0.01 = -1%)

    Returns:
        List of drawdown period dictionaries
    """
    periods = []
    in_drawdown = False
    start_date = None
    max_depth = 0

    for date, dd in drawdown.items():
        if dd < min_depth and not in_drawdown:
            # Start of drawdown
            in_drawdown = True
            start_date = date
            max_depth = dd
        elif in_drawdown:
            if dd < max_depth:
                max_depth = dd
            if dd >= 0:
                # End of drawdown (recovered)
                duration = (date - start_date).days
                periods.append({
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": date.strftime("%Y-%m-%d"),
                    "depth": round(float(max_depth), 4),
                    "duration": duration,
                })
                in_drawdown = False
                start_date = None
                max_depth = 0

    # Handle ongoing drawdown at end of data
    if in_drawdown and start_date is not None:
        end_date = drawdown.index[-1]
        duration = (end_date - start_date).days
        periods.append({
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
            "depth": round(float(max_depth), 4),
            "duration": duration,
            "ongoing": True,
        })

    # Sort by depth (most severe first) and limit to top 10
    periods.sort(key=lambda x: x["depth"])
    return periods[:10]


def compute_consecutive_losses(daily_returns: pd.Series) -> Dict[str, Any]:
    """
    Analyze consecutive losing periods.

    Returns:
        Dict with max streak info and streak distribution
    """
    if daily_returns.empty:
        return {
            "max_streak": 0,
            "max_streak_period": None,
            "max_streak_loss": 0,
            "streaks_distribution": {},
        }

    # Identify losing days
    is_loss = daily_returns < 0

    # Count consecutive losses
    streaks = []
    current_streak = 0
    streak_start = None
    current_loss = 0

    for date, (is_losing, ret) in enumerate(
        zip(is_loss.values, daily_returns.values)
    ):
        if is_losing:
            if current_streak == 0:
                streak_start = daily_returns.index[date]
            current_streak += 1
            current_loss += ret
        else:
            if current_streak > 0:
                streak_end = daily_returns.index[date - 1] if date > 0 else streak_start
                streaks.append({
                    "length": current_streak,
                    "start": streak_start,
                    "end": streak_end,
                    "total_loss": current_loss,
                })
            current_streak = 0
            current_loss = 0
            streak_start = None

    # Handle streak at end of data
    if current_streak > 0:
        streaks.append({
            "length": current_streak,
            "start": streak_start,
            "end": daily_returns.index[-1],
            "total_loss": current_loss,
        })

    if not streaks:
        return {
            "max_streak": 0,
            "max_streak_period": None,
            "max_streak_loss": 0,
            "streaks_distribution": {},
        }

    # Find max streak
    max_streak_info = max(streaks, key=lambda x: x["length"])

    # Build distribution
    streak_dist = {}
    for s in streaks:
        length = s["length"]
        streak_dist[str(length)] = streak_dist.get(str(length), 0) + 1

    return {
        "max_streak": max_streak_info["length"],
        "max_streak_period": {
            "start": max_streak_info["start"].strftime("%Y-%m-%d"),
            "end": max_streak_info["end"].strftime("%Y-%m-%d"),
        },
        "max_streak_loss": round(float(max_streak_info["total_loss"]), 4),
        "streaks_distribution": streak_dist,
    }


def compute_benchmark_comparison(
    strategy_returns: pd.Series,
    benchmark_returns: Dict[str, pd.Series],
    risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
) -> Dict[str, Any]:
    """
    Compute comprehensive comparison with benchmarks.

    Returns:
        Dict with cumulative returns, correlation, alpha, beta, etc.
    """
    if strategy_returns.empty:
        return {
            "cumulative_returns": {},
            "correlation": {},
            "beta": {},
            "alpha": {},
            "information_ratio": {},
            "tracking_error": {},
        }

    # Cumulative returns
    strategy_cumret = (1 + strategy_returns).cumprod() - 1
    cumulative_returns = {
        "strategy": [
            {"date": d.strftime("%Y-%m-%d"), "value": round(float(v), 4)}
            for d, v in strategy_cumret.items()
        ]
    }

    correlation = {}
    beta = {}
    alpha = {}
    information_ratio = {}
    tracking_error = {}

    for ticker, bench_ret in benchmark_returns.items():
        # Align dates
        aligned = pd.DataFrame({
            "strategy": strategy_returns,
            "benchmark": bench_ret,
        }).dropna()

        if len(aligned) < 20:
            logger.warning(f"Insufficient aligned data for {ticker} comparison")
            continue

        strat_ret = aligned["strategy"]
        bench = aligned["benchmark"]

        # Cumulative returns for benchmark
        bench_cumret = (1 + bench).cumprod() - 1
        cumulative_returns[ticker] = [
            {"date": d.strftime("%Y-%m-%d"), "value": round(float(v), 4)}
            for d, v in bench_cumret.items()
        ]

        # Correlation
        corr = strat_ret.corr(bench)
        correlation[ticker] = round(float(corr), 4) if not np.isnan(corr) else None

        # Beta (covariance / variance)
        cov = np.cov(strat_ret, bench)[0, 1]
        var = np.var(bench, ddof=1)
        b = cov / var if var > 0 else 0
        beta[ticker] = round(float(b), 4)

        # Alpha (annualized)
        daily_rf = risk_free_rate / 252
        excess_strat = strat_ret.mean() - daily_rf
        excess_bench = bench.mean() - daily_rf
        a = (excess_strat - b * excess_bench) * 252  # Annualized
        alpha[ticker] = round(float(a), 4)

        # Tracking error
        tracking_diff = strat_ret - bench
        te = tracking_diff.std() * np.sqrt(252)  # Annualized
        tracking_error[ticker] = round(float(te), 4)

        # Information ratio
        ir = (tracking_diff.mean() * 252) / te if te > 0 else 0
        information_ratio[ticker] = round(float(ir), 4)

    return {
        "cumulative_returns": cumulative_returns,
        "correlation": correlation,
        "beta": beta,
        "alpha": alpha,
        "information_ratio": information_ratio,
        "tracking_error": tracking_error,
    }


__all__ = [
    "compute_deep_analysis",
    "compute_monthly_returns",
    "compute_rolling_sharpe",
    "compute_returns_distribution",
    "compute_drawdown_distribution",
    "compute_consecutive_losses",
    "compute_benchmark_comparison",
    "fetch_benchmark_returns",
    "DeepAnalysisError",
    "DEFAULT_BENCHMARKS",
    "DEFAULT_ROLLING_WINDOW",
    "DEFAULT_RISK_FREE_RATE",
]
