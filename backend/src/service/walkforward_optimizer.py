"""
Walk-Forward Optimization Engine

Implements walk-forward analysis with train/validation split for detecting overfitting:
- Parameter optimization on training window
- Validation on out-of-sample test window
- Rolling window analysis across entire dataset
- Overfitting detection metrics
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from itertools import product
from typing import Any, Dict, List, Optional, Tuple

import backtrader as bt
import pandas as pd

from src.config.settings import IMAGES_DIR
from src.db.datasource import get_bt_feed
from src.service.backtest_engine import load_user_strategy
from src.service.parameter_analysis import get_parameter_analysis

logger = logging.getLogger(__name__)


@dataclass
class OptimizationWindow:
    """Represents a single walk-forward window."""
    window_id: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    best_params: Dict[str, Any] = field(default_factory=dict)
    train_metrics: Dict[str, Any] = field(default_factory=dict)
    test_metrics: Dict[str, Any] = field(default_factory=dict)
    all_train_results: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class WalkForwardResult:
    """Complete walk-forward optimization result."""
    optimization_id: str
    strategy_name: str
    ticker: str
    total_start_date: str
    total_end_date: str
    windows: List[OptimizationWindow]
    param_grid: Dict[str, List[Any]]
    overfitting_metrics: Dict[str, float] = field(default_factory=dict)
    combined_test_metrics: Dict[str, Any] = field(default_factory=dict)
    parameter_analysis: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


class WalkForwardOptimizer:
    """
    Walk-forward optimization engine.

    Splits data into rolling windows, optimizes parameters on training set,
    and validates on out-of-sample test set to detect overfitting.
    """

    def __init__(
        self,
        strategy_name: str,
        ticker: str,
        start_date: str,
        end_date: str,
        param_grid: Dict[str, List[Any]],
        initial_cash: float = 100000.0,
        commission: float = 0.0005,
        stake: int = 100,
        train_period_days: int = 365,
        test_period_days: int = 90,
        anchored: bool = False,
    ):
        """
        Initialize walk-forward optimizer.

        Args:
            strategy_name: Name of the strategy to optimize
            ticker: Symbol to backtest
            start_date: Overall start date (YYYY-MM-DD)
            end_date: Overall end date (YYYY-MM-DD)
            param_grid: Dictionary of parameter names to list of values to test
                       e.g., {"fast_period": [5, 10, 20], "slow_period": [20, 30, 50]}
            initial_cash: Initial cash for backtesting
            commission: Commission rate
            stake: Position size
            train_period_days: Training window size in days
            test_period_days: Testing window size in days
            anchored: If True, training window grows from start (anchored),
                     If False, training window slides (rolling)
        """
        self.strategy_name = strategy_name
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.param_grid = param_grid
        self.initial_cash = initial_cash
        self.commission = commission
        self.stake = stake
        self.train_period_days = train_period_days
        self.test_period_days = test_period_days
        self.anchored = anchored

        # Load strategy class once
        self.strategy_cls = load_user_strategy(strategy_name)

        logger.info(
            f"Initialized WalkForwardOptimizer: {strategy_name} on {ticker} "
            f"from {start_date} to {end_date}"
        )

    def _generate_windows(self) -> List[Tuple[str, str, str, str]]:
        """
        Generate rolling/anchored windows for walk-forward analysis.

        Returns:
            List of (train_start, train_end, test_start, test_end) tuples
        """
        start_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(self.end_date, "%Y-%m-%d")

        windows = []
        window_start = start_dt

        while True:
            # Training period
            train_start = window_start
            train_end = train_start + timedelta(days=self.train_period_days)

            # Testing period
            test_start = train_end + timedelta(days=1)
            test_end = test_start + timedelta(days=self.test_period_days)

            # Break if test window exceeds end date
            if test_end > end_dt:
                break

            windows.append((
                train_start.strftime("%Y-%m-%d"),
                train_end.strftime("%Y-%m-%d"),
                test_start.strftime("%Y-%m-%d"),
                test_end.strftime("%Y-%m-%d"),
            ))

            # Move to next window
            if self.anchored:
                # Anchored: keep same start, extend training window
                window_start = start_dt
                self.train_period_days += self.test_period_days
            else:
                # Rolling: slide the window forward
                window_start = test_start

        logger.info(f"Generated {len(windows)} walk-forward windows")
        return windows

    def _generate_param_combinations(self) -> List[Dict[str, Any]]:
        """
        Generate all parameter combinations from grid.

        Returns:
            List of parameter dictionaries
        """
        if not self.param_grid:
            return [{}]

        param_names = list(self.param_grid.keys())
        param_values = list(self.param_grid.values())

        combinations = []
        for values in product(*param_values):
            combinations.append(dict(zip(param_names, values)))

        logger.info(f"Generated {len(combinations)} parameter combinations")
        return combinations

    def _run_single_backtest(
        self,
        start_date: str,
        end_date: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run a single backtest with given parameters and date range.

        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            params: Strategy parameters

        Returns:
            Dictionary of metrics
        """
        try:
            cerebro = bt.Cerebro()

            # Add strategy with parameters
            cerebro.addstrategy(self.strategy_cls, **params)

            # Add data feed
            data = get_bt_feed(self.ticker, start_date, end_date)
            cerebro.adddata(data)

            # Configure broker
            cerebro.broker.setcash(self.initial_cash)
            cerebro.broker.setcommission(commission=self.commission)
            cerebro.addsizer(bt.sizers.FixedSize, stake=self.stake)

            # Add analyzers
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
            cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
            cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")

            # Run backtest
            results = cerebro.run()
            strat = results[0]

            # Extract metrics
            final_value = cerebro.broker.getvalue()
            sharpe = strat.analyzers.sharpe.get_analysis().get("sharperatio", None)
            drawdown = strat.analyzers.drawdown.get_analysis().get("max", {}).get("drawdown", 0.0)
            returns = strat.analyzers.returns.get_analysis().get("rnorm100", 0.0)
            sqn = strat.analyzers.sqn.get_analysis().get("sqn", None)
            trades_analysis = strat.analyzers.trades.get_analysis()

            total_trades = trades_analysis.get("total", {}).get("total", 0)
            won_trades = trades_analysis.get("won", {}).get("total", 0)
            lost_trades = trades_analysis.get("lost", {}).get("total", 0)

            # Calculate profit factor
            gross_won = trades_analysis.get("won", {}).get("pnl", {}).get("total", 0.0)
            gross_lost = abs(trades_analysis.get("lost", {}).get("pnl", {}).get("total", 0.0))
            profit_factor = gross_won / gross_lost if gross_lost > 0 else 0.0

            metrics = {
                "params": params,
                "final_value": final_value,
                "total_return": returns,
                "sharpe_ratio": sharpe if sharpe is not None else 0.0,
                "max_drawdown": drawdown,
                "sqn": sqn if sqn is not None else 0.0,
                "total_trades": total_trades,
                "winning_trades": won_trades,
                "losing_trades": lost_trades,
                "win_rate": (won_trades / total_trades * 100) if total_trades > 0 else 0.0,
                "profit_factor": profit_factor,
            }

            return metrics

        except Exception as e:
            logger.error(f"Backtest failed for params {params}: {e}")
            return {
                "params": params,
                "final_value": self.initial_cash,
                "total_return": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "sqn": 0.0,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "error": str(e),
            }

    def _optimize_on_train_window(
        self,
        train_start: str,
        train_end: str,
        param_combinations: List[Dict[str, Any]],
        optimization_metric: str = "sharpe_ratio",
    ) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
        """
        Optimize parameters on training window.

        Args:
            train_start: Training period start
            train_end: Training period end
            param_combinations: List of parameter combinations to test
            optimization_metric: Metric to optimize (sharpe_ratio, total_return, profit_factor)

        Returns:
            Tuple of (best_params, best_metrics, all_results)
        """
        logger.info(
            f"Optimizing {len(param_combinations)} parameter combinations "
            f"on training window {train_start} to {train_end}"
        )

        all_results = []
        best_metric_value = float("-inf")
        best_params = {}
        best_metrics = {}

        for params in param_combinations:
            metrics = self._run_single_backtest(train_start, train_end, params)
            all_results.append(metrics)

            metric_value = metrics.get(optimization_metric, float("-inf"))

            # Handle None values (e.g., sharpe_ratio can be None)
            if metric_value is None:
                metric_value = float("-inf")

            if metric_value > best_metric_value:
                best_metric_value = metric_value
                best_params = params.copy()
                best_metrics = metrics.copy()

        logger.info(f"Best params on training: {best_params} with {optimization_metric}={best_metric_value}")
        return best_params, best_metrics, all_results

    def _validate_on_test_window(
        self,
        test_start: str,
        test_end: str,
        best_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate best parameters on out-of-sample test window.

        Args:
            test_start: Test period start
            test_end: Test period end
            best_params: Best parameters from training

        Returns:
            Test metrics dictionary
        """
        logger.info(f"Validating on test window {test_start} to {test_end} with params {best_params}")
        return self._run_single_backtest(test_start, test_end, best_params)

    def run_walkforward(
        self,
        optimization_metric: str = "sharpe_ratio",
        optimization_id: Optional[str] = None,
    ) -> WalkForwardResult:
        """
        Run complete walk-forward optimization.

        Args:
            optimization_metric: Metric to optimize on training windows
            optimization_id: Optional ID for this optimization run

        Returns:
            WalkForwardResult with all windows and overfitting metrics
        """
        if optimization_id is None:
            import uuid
            optimization_id = str(uuid.uuid4())

        logger.info(f"Starting walk-forward optimization {optimization_id}")

        # Generate windows and parameter combinations
        windows_dates = self._generate_windows()
        param_combinations = self._generate_param_combinations()

        # Process each window
        optimization_windows = []

        for window_id, (train_start, train_end, test_start, test_end) in enumerate(windows_dates, 1):
            logger.info(f"Processing window {window_id}/{len(windows_dates)}")

            # Optimize on training window
            best_params, train_metrics, all_train_results = self._optimize_on_train_window(
                train_start, train_end, param_combinations, optimization_metric
            )

            # Validate on test window
            test_metrics = self._validate_on_test_window(test_start, test_end, best_params)

            window = OptimizationWindow(
                window_id=window_id,
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
                best_params=best_params,
                train_metrics=train_metrics,
                test_metrics=test_metrics,
                all_train_results=all_train_results,
            )

            optimization_windows.append(window)

        # Calculate overfitting metrics
        overfitting_metrics = self._calculate_overfitting_metrics(
            optimization_windows, optimization_metric
        )

        # Calculate combined test metrics (performance across all test windows)
        combined_test_metrics = self._calculate_combined_test_metrics(optimization_windows)

        # Calculate parameter analysis for visualization
        parameter_analysis = get_parameter_analysis(
            windows=optimization_windows,
            param_grid=self.param_grid,
            optimization_metric=optimization_metric,
            overfitting_metrics=overfitting_metrics,
        )

        result = WalkForwardResult(
            optimization_id=optimization_id,
            strategy_name=self.strategy_name,
            ticker=self.ticker,
            total_start_date=self.start_date,
            total_end_date=self.end_date,
            windows=optimization_windows,
            param_grid=self.param_grid,
            overfitting_metrics=overfitting_metrics,
            combined_test_metrics=combined_test_metrics,
            parameter_analysis=parameter_analysis,
        )

        logger.info(f"Walk-forward optimization {optimization_id} completed")
        logger.info(f"Overfitting metrics: {overfitting_metrics}")

        return result

    def _calculate_overfitting_metrics(
        self,
        windows: List[OptimizationWindow],
        optimization_metric: str,
    ) -> Dict[str, float]:
        """
        Calculate overfitting detection metrics.

        Compares training vs test performance to detect overfitting:
        - Train/Test correlation
        - Average train vs test degradation
        - Consistency score

        Args:
            windows: List of optimization windows
            optimization_metric: The metric that was optimized

        Returns:
            Dictionary of overfitting metrics
        """
        if not windows:
            return {}

        train_values = []
        test_values = []
        degradations = []

        for window in windows:
            train_val = window.train_metrics.get(optimization_metric, 0.0)
            test_val = window.test_metrics.get(optimization_metric, 0.0)

            # Handle None values
            if train_val is None:
                train_val = 0.0
            if test_val is None:
                test_val = 0.0

            train_values.append(train_val)
            test_values.append(test_val)

            # Calculate degradation (positive means worse performance on test)
            if train_val != 0:
                degradation = ((train_val - test_val) / abs(train_val)) * 100
            else:
                degradation = 0.0

            degradations.append(degradation)

        # Calculate correlation between train and test performance
        try:
            train_series = pd.Series(train_values)
            test_series = pd.Series(test_values)
            correlation = train_series.corr(test_series)
        except Exception:
            correlation = 0.0

        # Average degradation
        avg_degradation = sum(degradations) / len(degradations) if degradations else 0.0

        # Consistency score: percentage of windows where test performance is within 20% of train
        consistent_windows = sum(1 for d in degradations if abs(d) <= 20)
        consistency_score = (consistent_windows / len(windows)) * 100 if windows else 0.0

        # Calculate standard deviation of degradations (lower is better)
        std_degradation = pd.Series(degradations).std() if len(degradations) > 1 else 0.0

        return {
            "train_test_correlation": round(correlation if not pd.isna(correlation) else 0.0, 4),
            "avg_train_performance": round(sum(train_values) / len(train_values), 4) if train_values else 0.0,
            "avg_test_performance": round(sum(test_values) / len(test_values), 4) if test_values else 0.0,
            "avg_degradation_pct": round(avg_degradation, 2),
            "consistency_score": round(consistency_score, 2),
            "degradation_std": round(std_degradation, 2),
            "overfitting_detected": avg_degradation > 30 or consistency_score < 50,
        }

    def _calculate_combined_test_metrics(
        self,
        windows: List[OptimizationWindow],
    ) -> Dict[str, Any]:
        """
        Calculate combined metrics across all test windows.

        This represents the actual out-of-sample performance of the strategy
        when parameters are optimized on each training window.

        Args:
            windows: List of optimization windows

        Returns:
            Combined test metrics
        """
        if not windows:
            return {}

        total_return = sum(w.test_metrics.get("total_return", 0.0) for w in windows)
        sharpe_ratios = [w.test_metrics.get("sharpe_ratio", 0.0) for w in windows if w.test_metrics.get("sharpe_ratio") is not None]
        max_drawdowns = [w.test_metrics.get("max_drawdown", 0.0) for w in windows]
        total_trades = sum(w.test_metrics.get("total_trades", 0) for w in windows)
        winning_trades = sum(w.test_metrics.get("winning_trades", 0) for w in windows)
        losing_trades = sum(w.test_metrics.get("losing_trades", 0) for w in windows)

        return {
            "num_windows": len(windows),
            "total_return": round(total_return, 2),
            "avg_sharpe_ratio": round(sum(sharpe_ratios) / len(sharpe_ratios), 4) if sharpe_ratios else 0.0,
            "avg_max_drawdown": round(sum(max_drawdowns) / len(max_drawdowns), 2) if max_drawdowns else 0.0,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": round((winning_trades / total_trades * 100), 2) if total_trades > 0 else 0.0,
        }


__all__ = [
    "WalkForwardOptimizer",
    "WalkForwardResult",
    "OptimizationWindow",
]
