"""
Result Extractor - Structured extraction of backtest results.

This module separates result extraction logic from backtest execution,
providing a clean interface for extracting metrics from completed backtests.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

import backtrader as bt

from .backtest_config import BacktestConfig
from src.utils.backtrader_helpers import (
    safe_get_analyzer_result,
    get_sharpe_ratio,
    get_max_drawdown,
)

logger = logging.getLogger(__name__)


class ResultExtractor:
    """
    Extracts structured results from a completed backtest.

    Separates metric extraction from backtest execution for:
    - Clearer code organization
    - Easier testing
    - Consistent result formatting

    Usage:
        results = cerebro.run()
        strategy = results[0]
        extractor = ResultExtractor(cerebro, strategy, config)
        result = extractor.build_result()
    """

    def __init__(
        self,
        cerebro: bt.Cerebro,
        strategy: bt.Strategy,
        config: BacktestConfig
    ):
        """
        Initialize the result extractor.

        Args:
            cerebro: Completed Cerebro instance
            strategy: Executed strategy instance
            config: Backtest configuration
        """
        self.cerebro = cerebro
        self.strategy = strategy
        self.config = config

    def get_final_value(self) -> float:
        """Get the final portfolio value."""
        return float(self.cerebro.broker.getvalue())

    def get_total_return(self) -> float:
        """Calculate total return percentage."""
        final_value = self.get_final_value()
        initial_cash = self.config.initial_cash
        return ((final_value - initial_cash) / initial_cash) * 100

    def extract_standard_metrics(self) -> Dict[str, Any]:
        """
        Extract metrics from standard Backtrader analyzers.

        Returns:
            Dictionary with sharpe_ratio, max_drawdown, returns, drawdown
        """
        # Sharpe ratio
        sharpe_ratio = get_sharpe_ratio(self.strategy, default=0.0)

        # Max drawdown
        max_drawdown = get_max_drawdown(self.strategy, default=0.0)

        # Returns analysis
        returns_analysis = safe_get_analyzer_result(
            self.strategy, "returns", "rnorm100", {}
        )
        # Get full returns dict if available
        if hasattr(self.strategy, 'analyzers') and hasattr(self.strategy.analyzers, 'returns'):
            try:
                returns_analysis = dict(self.strategy.analyzers.returns.get_analysis())
            except Exception:
                pass

        # Drawdown analysis
        drawdown_analysis = {}
        if hasattr(self.strategy, 'analyzers') and hasattr(self.strategy.analyzers, 'drawdown'):
            try:
                drawdown_analysis = dict(self.strategy.analyzers.drawdown.get_analysis())
            except Exception:
                pass

        return {
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown * 100 if max_drawdown < 1 else max_drawdown,  # Ensure percentage
            "returns": returns_analysis,
            "drawdown": drawdown_analysis,
        }

    def extract_portfolio_metrics(self) -> Dict[str, Any]:
        """
        Extract metrics from custom portfolio analyzers.

        Returns:
            Dictionary with equity_curve, rebalancing_events, trades, etc.
        """
        # Portfolio value analyzer
        portfolio_value = self._get_portfolio_value_analysis()

        # Rebalancing events
        rebalancing = self._get_rebalancing_analysis()

        # Asset contributions
        contributions = self._get_asset_contribution_analysis()

        # Trade recorder
        trades = self._get_trade_recorder_analysis()

        # Portfolio metrics
        portfolio_metrics = self._get_portfolio_metrics_analysis()

        return {
            "equity_curve": portfolio_value.get("equity_curve", {}),
            "rebalancing_events": rebalancing.get("events", []),
            "all_trades": trades.get("trades", []),
            "asset_contributions": contributions.get("contributions", {}),
            "portfolio_metrics": portfolio_metrics,
            "total_transaction_costs": rebalancing.get("total_transaction_costs", 0.0),
            "rebalancing_count": rebalancing.get("total_events", 0),
        }

    def _get_portfolio_value_analysis(self) -> Dict:
        """Get portfolio value analyzer results."""
        return self._safe_get_analyzer("portfolio_value")

    def _get_rebalancing_analysis(self) -> Dict:
        """Get rebalancing analyzer results."""
        return self._safe_get_analyzer("rebalancing")

    def _get_asset_contribution_analysis(self) -> Dict:
        """Get asset contribution analyzer results."""
        return self._safe_get_analyzer("contributions")

    def _get_trade_recorder_analysis(self) -> Dict:
        """Get trade recorder analyzer results."""
        return self._safe_get_analyzer("trade_recorder")

    def _get_portfolio_metrics_analysis(self) -> Dict:
        """Get portfolio metrics analyzer results."""
        return self._safe_get_analyzer("portfolio_metrics")

    def _safe_get_analyzer(self, analyzer_name: str) -> Dict:
        """Safely get analyzer results with error handling."""
        try:
            if hasattr(self.strategy, 'analyzers'):
                analyzer = getattr(self.strategy.analyzers, analyzer_name, None)
                if analyzer is not None:
                    return dict(analyzer.get_analysis())
        except Exception as e:
            logger.warning(f"Failed to get {analyzer_name} analyzer: {e}")
        return {}

    def build_individual_results(self) -> List[Dict]:
        """
        Build per-asset results for UI compatibility.

        Returns:
            List of individual asset result dictionaries
        """
        contributions = self._get_asset_contribution_analysis().get("contributions", {})
        individual_results = []

        for i, ticker in enumerate(self.config.tickers):
            contrib = contributions.get(ticker, {})

            # Use start_value and end_value from contributions if available
            default_value = self.config.initial_cash * self.config.weights[i]
            start_value = contrib.get("start_value", default_value)
            end_value = contrib.get("end_value", default_value)

            # Calculate return based on actual values
            asset_return = 0.0
            if start_value > 0:
                asset_return = ((end_value - start_value) / start_value) * 100

            individual_results.append({
                "ticker": ticker,
                "weight": self.config.weights[i],
                "success": True,
                "initial_cash": start_value,
                "final_value": end_value,
                "total_return": asset_return,
                "sharpe": None,  # Not available per-asset in unified backtest
                "max_drawdown": None,
                "total_trades": contrib.get("end_shares", 0),
            })

        return individual_results

    def build_result(
        self,
        correlation: Optional[Dict] = None,
        optimization: Optional[Dict] = None,
        plot_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build the complete result dictionary.

        Args:
            correlation: Pre-calculated correlation matrix
            optimization: Pre-calculated optimization suggestions
            plot_url: URL to generated chart image

        Returns:
            Complete backtest result dictionary
        """
        final_value = self.get_final_value()
        total_return = self.get_total_return()

        standard_metrics = self.extract_standard_metrics()
        portfolio_metrics = self.extract_portfolio_metrics()
        individual_results = self.build_individual_results()

        result = {
            # Core results
            "final_value": final_value,
            "total_return": total_return,
            "sharpe_ratio": standard_metrics["sharpe_ratio"],
            "max_drawdown": standard_metrics["max_drawdown"],
            "initial_cash": self.config.initial_cash,

            # Asset configuration
            "num_assets": len(self.config.tickers),
            "tickers": self.config.tickers,
            "weights": self.config.weights,

            # Portfolio-specific results
            "equity_curve": portfolio_metrics["equity_curve"],
            "rebalancing_events": portfolio_metrics["rebalancing_events"],
            "all_trades": portfolio_metrics["all_trades"],
            "asset_contributions": portfolio_metrics["asset_contributions"],

            # Individual asset results (for UI compatibility)
            "individual_results": individual_results,

            # Correlation and optimization (if provided)
            "correlation": correlation or {},
            "optimization": optimization or {},

            # Comprehensive metrics
            "metrics": {
                "returns": standard_metrics["returns"],
                "drawdown": standard_metrics["drawdown"],
                "portfolio_metrics": portfolio_metrics["portfolio_metrics"],
                "optimization_method": self.config.optimization_method,
                "rebalance_frequency": (
                    self.config.rebalance_config.frequency
                    if self.config.rebalance_config else None
                ),
                "total_transaction_costs": portfolio_metrics["total_transaction_costs"],
                "rebalancing_count": portfolio_metrics["rebalancing_count"],
            }
        }

        # Add plot URL if provided
        if plot_url:
            result["plot_url"] = plot_url

        self._log_result_summary(result)

        return result

    def _log_result_summary(self, result: Dict):
        """Log a summary of the results."""
        logger.info(f"Backtest complete! Final value: ${result['final_value']:,.2f}")
        logger.info(
            f"Total return: {result['total_return']:.2f}%, "
            f"Sharpe: {result['sharpe_ratio']:.2f}, "
            f"Max DD: {result['max_drawdown']:.2f}%"
        )
        logger.info(f"Equity curve: {len(result['equity_curve'])} days")
        logger.info(f"Asset contributions: {len(result['asset_contributions'])} assets")
        logger.info(f"All trades: {len(result['all_trades'])} trades")


__all__ = ["ResultExtractor"]
