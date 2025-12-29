"""
Result Aggregator - Clean interface for extracting backtest results.

This module provides a clean interface that hides analyzer internal structure
from routes and other consumers, enabling loose coupling.

Key benefits:
- Routes don't need to know analyzer internals
- Changes to analyzer output don't require route changes
- Consistent result format across different analyzers
- Easy to mock for testing
"""

from typing import Dict, List, Any, Optional, Protocol
from abc import ABC, abstractmethod
import logging

import backtrader as bt

logger = logging.getLogger(__name__)


class IResultAggregator(Protocol):
    """
    Protocol defining the interface for result aggregation.

    This enables duck typing and easier mocking for tests.
    """

    def get_equity_curve(self) -> Dict[str, float]:
        """Get equity curve data."""
        ...

    def get_rebalancing_events(self) -> List[Dict]:
        """Get list of rebalancing events."""
        ...

    def get_asset_contributions(self) -> Dict[str, Dict]:
        """Get per-asset contribution data."""
        ...

    def get_all_trades(self) -> List[Dict]:
        """Get all executed trades."""
        ...

    def get_portfolio_metrics(self) -> Dict[str, Any]:
        """Get portfolio-level metrics."""
        ...

    def aggregate(self) -> Dict[str, Any]:
        """Aggregate all results into a single dict."""
        ...


class PortfolioResultAggregator:
    """
    Aggregates results from multiple portfolio analyzers.

    Provides a clean API that hides analyzer internals from routes
    and other consumers.

    Usage:
        aggregator = PortfolioResultAggregator(strategy)
        result = aggregator.aggregate()

        # Or access individual components
        equity_curve = aggregator.get_equity_curve()
        events = aggregator.get_rebalancing_events()
    """

    def __init__(self, strategy: bt.Strategy):
        """
        Initialize the aggregator with a strategy instance.

        Args:
            strategy: Executed Backtrader strategy with analyzers
        """
        self.strategy = strategy
        self._analyzers = getattr(strategy, 'analyzers', None)

    def _safe_get_analyzer(
        self,
        analyzer_name: str,
        default: Any = None
    ) -> Any:
        """
        Safely get an analyzer result.

        Args:
            analyzer_name: Name of the analyzer
            default: Default value if analyzer not found

        Returns:
            Analyzer results or default value
        """
        if self._analyzers is None:
            return default

        try:
            analyzer = getattr(self._analyzers, analyzer_name, None)
            if analyzer is not None:
                analysis = analyzer.get_analysis()
                return dict(analysis) if hasattr(analysis, 'items') else analysis
        except Exception as e:
            logger.warning(f"Failed to get analyzer {analyzer_name}: {e}")

        return default

    def _safe_get_analyzer_key(
        self,
        analyzer_name: str,
        key: str,
        default: Any = None
    ) -> Any:
        """
        Safely get a specific key from analyzer results.

        Args:
            analyzer_name: Name of the analyzer
            key: Key to extract from results
            default: Default value if key not found

        Returns:
            Value for the key or default
        """
        analysis = self._safe_get_analyzer(analyzer_name, {})
        if isinstance(analysis, dict):
            return analysis.get(key, default)
        return default

    def get_equity_curve(self) -> Dict[str, float]:
        """
        Get the portfolio equity curve.

        Returns:
            Dictionary mapping date strings to portfolio values
        """
        return self._safe_get_analyzer_key("portfolio_value", "equity_curve", {})

    def get_rebalancing_events(self) -> List[Dict]:
        """
        Get list of rebalancing events.

        Returns:
            List of rebalancing event dictionaries
        """
        return self._safe_get_analyzer_key("rebalancing", "events", [])

    def get_asset_contributions(self) -> Dict[str, Dict]:
        """
        Get per-asset contribution data.

        Returns:
            Dictionary mapping tickers to contribution data
        """
        return self._safe_get_analyzer_key("contributions", "contributions", {})

    def get_all_trades(self) -> List[Dict]:
        """
        Get all executed trades.

        First tries the trade_recorder analyzer, then falls back to
        extracting trades from rebalancing events.

        Returns:
            List of trade dictionaries
        """
        # Primary: From trade recorder analyzer
        trades = self._safe_get_analyzer_key("trade_recorder", "trades", [])
        if trades:
            return trades

        # Fallback: Extract from rebalancing events
        return self._extract_trades_from_events()

    def _extract_trades_from_events(self) -> List[Dict]:
        """Extract trades from rebalancing events as fallback."""
        trades = []
        events = self.get_rebalancing_events()

        for event in events:
            orders = event.get("orders", {})
            prices = event.get("prices", {})
            event_date = event.get("date", "")

            for ticker, shares in orders.items():
                if shares != 0:
                    trades.append({
                        "date": event_date,
                        "ticker": ticker,
                        "action": "buy" if shares > 0 else "sell",
                        "shares": abs(shares),
                        "price": prices.get(ticker, 0),
                        "value": abs(shares) * prices.get(ticker, 0),
                        "trigger": "rebalance",
                    })

        return trades

    def get_portfolio_metrics(self) -> Dict[str, Any]:
        """
        Get portfolio-level metrics.

        Returns:
            Dictionary of portfolio metrics
        """
        return self._safe_get_analyzer("portfolio_metrics", {})

    def get_total_transaction_costs(self) -> float:
        """Get total transaction costs from all rebalancing."""
        return self._safe_get_analyzer_key(
            "rebalancing", "total_transaction_costs", 0.0
        )

    def get_rebalancing_count(self) -> int:
        """Get total number of rebalancing events."""
        return self._safe_get_analyzer_key(
            "rebalancing", "total_events", 0
        )

    def get_trade_statistics(self) -> Dict[str, Any]:
        """
        Get trading statistics.

        Returns:
            Dictionary with trade counts and volumes
        """
        analysis = self._safe_get_analyzer("trade_recorder", {})
        return {
            "total_trades": analysis.get("total_trades", 0),
            "buy_trades": analysis.get("buy_trades", 0),
            "sell_trades": analysis.get("sell_trades", 0),
            "total_volume": analysis.get("total_volume", 0),
            "total_commission": analysis.get("total_commission", 0),
        }

    def get_drawdown_analysis(self) -> Dict[str, Any]:
        """Get drawdown analysis from standard analyzer."""
        return self._safe_get_analyzer("drawdown", {})

    def get_returns_analysis(self) -> Dict[str, Any]:
        """Get returns analysis from standard analyzer."""
        return self._safe_get_analyzer("returns", {})

    def get_sharpe_ratio(self) -> Optional[float]:
        """Get Sharpe ratio from standard analyzer."""
        analysis = self._safe_get_analyzer("sharpe", {})
        sharpe = analysis.get("sharperatio")
        if sharpe is not None and sharpe == sharpe:  # NaN check
            return float(sharpe)
        return None

    def aggregate(self) -> Dict[str, Any]:
        """
        Aggregate all results into a single dictionary.

        This is the main method that routes should use to get
        all portfolio results in a standardized format.

        Returns:
            Dictionary containing all aggregated results
        """
        return {
            "equity_curve": self.get_equity_curve(),
            "rebalancing_events": self.get_rebalancing_events(),
            "asset_contributions": self.get_asset_contributions(),
            "all_trades": self.get_all_trades(),
            "portfolio_metrics": self.get_portfolio_metrics(),
            "trade_statistics": self.get_trade_statistics(),
            "returns_analysis": self.get_returns_analysis(),
            "drawdown_analysis": self.get_drawdown_analysis(),
            "sharpe_ratio": self.get_sharpe_ratio(),
            "total_transaction_costs": self.get_total_transaction_costs(),
            "rebalancing_count": self.get_rebalancing_count(),
        }

    def to_route_result(
        self,
        final_value: float,
        initial_cash: float,
        tickers: List[str],
        weights: List[float],
        correlation: Optional[Dict] = None,
        optimization: Optional[Dict] = None,
        plot_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build a complete result dictionary for route responses.

        This method combines aggregated analyzer data with additional
        context to create a complete response suitable for API routes.

        Args:
            final_value: Final portfolio value
            initial_cash: Initial cash amount
            tickers: List of ticker symbols
            weights: List of weights
            correlation: Pre-calculated correlation matrix
            optimization: Pre-calculated optimization suggestions
            plot_url: URL to chart image

        Returns:
            Complete result dictionary for API response
        """
        aggregated = self.aggregate()

        total_return = ((final_value - initial_cash) / initial_cash) * 100
        sharpe_ratio = aggregated.get("sharpe_ratio", 0) or 0

        # Calculate max drawdown
        max_drawdown = 0.0
        drawdown = aggregated.get("drawdown_analysis", {})
        if isinstance(drawdown, dict):
            max_dd = drawdown.get("max", {})
            if isinstance(max_dd, dict):
                max_drawdown = max_dd.get("drawdown", 0) or 0

        result = {
            # Core results
            "final_value": final_value,
            "total_return": total_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "initial_cash": initial_cash,

            # Asset configuration
            "num_assets": len(tickers),
            "tickers": tickers,
            "weights": weights,

            # From aggregator
            "equity_curve": aggregated["equity_curve"],
            "rebalancing_events": aggregated["rebalancing_events"],
            "all_trades": aggregated["all_trades"],
            "asset_contributions": aggregated["asset_contributions"],

            # Correlation and optimization
            "correlation": correlation or {},
            "optimization": optimization or {},

            # Comprehensive metrics
            "metrics": {
                "returns": aggregated["returns_analysis"],
                "drawdown": aggregated["drawdown_analysis"],
                "portfolio_metrics": aggregated["portfolio_metrics"],
                "total_transaction_costs": aggregated["total_transaction_costs"],
                "rebalancing_count": aggregated["rebalancing_count"],
            },
        }

        if plot_url:
            result["plot_url"] = plot_url

        return result

    def __repr__(self) -> str:
        has_analyzers = self._analyzers is not None
        return f"PortfolioResultAggregator(has_analyzers={has_analyzers})"


__all__ = [
    "IResultAggregator",
    "PortfolioResultAggregator",
]
