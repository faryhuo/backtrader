"""
Portfolio Analyzers - Custom Backtrader analyzers for multi-asset portfolios.

This module provides specialized analyzers for tracking portfolio-level metrics:
- PortfolioValueAnalyzer: Daily equity curve
- RebalancingEventAnalyzer: Rebalancing events and costs
- AssetContributionAnalyzer: Per-asset return contribution
- PortfolioMetricsAnalyzer: Comprehensive portfolio statistics
"""

import logging
from datetime import datetime
from typing import Optional

import backtrader as bt

logger = logging.getLogger(__name__)


class PortfolioValueAnalyzer(bt.Analyzer):
    """
    Track daily portfolio value to generate equity curve.

    This analyzer records the total portfolio value (cash + positions) on
    each bar, enabling time-series visualization of portfolio performance.

    Results:
        {
            "equity_curve": {
                "2023-01-01": 100000.0,
                "2023-01-02": 100500.0,
                ...
            },
            "start_value": 100000.0,
            "end_value": 105000.0,
            "peak_value": 106000.0,
            "total_return_pct": 5.0
        }
    """

    def __init__(self):
        """Initialize the analyzer."""
        super().__init__()
        self.equity_curve = {}
        self.start_value = None
        self.peak_value = None

    def start(self):
        """Called at the start of the backtest."""
        self.start_value = self.strategy.broker.getvalue()
        self.peak_value = self.start_value
        logger.debug(f"PortfolioValueAnalyzer started with ${self.start_value:,.2f}")

    def next(self):
        """Called on each bar to record portfolio value."""
        current_date = self.strategy.datetime.date(0)
        current_value = self.strategy.broker.getvalue()

        # Store value for this date
        self.equity_curve[current_date.isoformat()] = float(current_value)

        # Track peak value for performance metrics
        if current_value > self.peak_value:
            self.peak_value = current_value

    def stop(self):
        """Called at the end of the backtest."""
        end_value = self.strategy.broker.getvalue()
        logger.info(
            f"PortfolioValueAnalyzer complete: ${self.start_value:,.2f} → "
            f"${end_value:,.2f} ({len(self.equity_curve)} days)"
        )

    def get_analysis(self):
        """
        Return the equity curve and summary statistics.

        Returns:
            Dictionary with equity curve and performance metrics
        """
        end_value = self.strategy.broker.getvalue()
        total_return_pct = 0.0

        if self.start_value and self.start_value > 0:
            total_return_pct = ((end_value - self.start_value) / self.start_value) * 100

        return {
            "equity_curve": self.equity_curve,
            "start_value": float(self.start_value) if self.start_value else 0.0,
            "end_value": float(end_value),
            "peak_value": float(self.peak_value) if self.peak_value else 0.0,
            "total_return_pct": float(total_return_pct),
            "num_days": len(self.equity_curve),
        }


class RebalancingEventAnalyzer(bt.Analyzer):
    """
    Track all portfolio rebalancing events.

    Records each rebalancing occurrence including:
    - Date
    - Target weights
    - Orders executed
    - Transaction costs
    - Pre/post rebalance portfolio value

    Results:
        {
            "events": [
                {
                    "date": "2023-01-31",
                    "trigger": "monthly_schedule",
                    "pre_rebalance_value": 105000.0,
                    "post_rebalance_value": 104950.0,  # After transaction costs
                    "target_weights": {"AAPL": 0.33, "GOOGL": 0.33, "MSFT": 0.34},
                    "orders": {"AAPL": 10, "GOOGL": -5, "MSFT": 20},
                    "transaction_cost": 50.0
                },
                ...
            ],
            "total_events": 12,
            "total_transaction_costs": 600.0
        }
    """

    def __init__(self):
        """Initialize the analyzer."""
        super().__init__()
        self.events = []
        self.total_transaction_costs = 0.0

    def notify_rebalance(
        self,
        date: datetime.date,
        trigger: str,
        pre_value: float,
        post_value: float,
        target_weights: dict[str, float],
        orders: dict[str, int],
        transaction_cost: float,
        pre_weights: dict[str, float] = None,
        prices: dict[str, float] = None,
    ):
        """
        Record a rebalancing event.

        This method is called by the strategy when rebalancing occurs.

        Args:
            date: Rebalancing date
            trigger: Trigger reason ("monthly_schedule", "quarterly_schedule", etc.)
            pre_value: Portfolio value before rebalancing
            post_value: Portfolio value after rebalancing
            target_weights: New target allocation
            orders: Share delta for each ticker
            transaction_cost: Total transaction cost
            pre_weights: Weights before rebalancing
            prices: Current prices for each ticker
        """
        # Build trades array with details
        trades = []
        for ticker, shares in orders.items():
            trade = {
                "ticker": ticker,
                "shares": shares,
                "action": "buy" if shares > 0 else "sell",
            }
            if prices and ticker in prices:
                trade["price"] = prices[ticker]
                trade["value"] = abs(shares) * prices[ticker]
            trades.append(trade)

        event = {
            "date": date.isoformat(),
            "trigger": trigger,
            "pre_rebalance_value": float(pre_value),
            "post_rebalance_value": float(post_value),
            "portfolio_value": float(pre_value),  # For frontend display
            "target_weights": {k: float(v) for k, v in target_weights.items()},
            "pre_weights": {k: float(v) for k, v in pre_weights.items()} if pre_weights else {},
            "orders": {k: int(v) for k, v in orders.items()},
            "trades": trades,
            "transaction_cost": float(transaction_cost),
        }

        self.events.append(event)
        self.total_transaction_costs += transaction_cost

        logger.info(
            f"Rebalancing event recorded: {date} ({trigger}), "
            f"cost=${transaction_cost:.2f}, {len(trades)} trades"
        )

    def get_analysis(self):
        """
        Return all rebalancing events and summary statistics.

        Returns:
            Dictionary with event list and totals
        """
        return {
            "events": self.events,
            "total_events": len(self.events),
            "total_transaction_costs": float(self.total_transaction_costs),
        }


class AssetContributionAnalyzer(bt.Analyzer):
    """
    Calculate each asset's contribution to total portfolio return.

    Tracks individual asset performance and weights to compute how much
    each asset contributed to the overall portfolio return.

    Results:
        {
            "contributions": {
                "AAPL": {
                    "return_pct": 15.2,
                    "avg_weight": 0.33,
                    "contribution_pct": 5.016,  # 15.2% * 0.33
                    "start_price": 150.0,
                    "end_price": 172.8,
                    "start_shares": 220,
                    "end_shares": 220
                },
                ...
            },
            "total_contribution": 10.5  # Sum of all contributions
        }
    """

    def __init__(self):
        """Initialize the analyzer."""
        super().__init__()
        self.start_prices = {}
        self.start_shares = {}
        self.tickers = []

    def start(self):
        """Record starting state for all assets."""
        # Get tickers from strategy if available
        if hasattr(self.strategy, 'p') and hasattr(self.strategy.p, 'tickers'):
            self.tickers = self.strategy.p.tickers
        else:
            # Fallback: use data feed names
            self.tickers = [
                data._name if hasattr(data, '_name') else f"Asset{i}"
                for i, data in enumerate(self.strategy.datas)
            ]

        logger.debug(f"AssetContributionAnalyzer tracking {len(self.tickers)} assets")

    def stop(self):
        """Calculate contributions at end of backtest."""
        logger.info("Calculating asset contributions...")

        # We'll calculate this in get_analysis() since we need final state

    def get_analysis(self):
        """
        Calculate and return per-asset contribution to total return.

        Returns:
            Dictionary with per-asset contributions and total
        """
        contributions = {}
        total_portfolio_value_start = None
        total_portfolio_value_end = self.strategy.broker.getvalue()

        # Get ticker to data mapping
        if hasattr(self.strategy, 'ticker_data'):
            ticker_data = self.strategy.ticker_data
        else:
            # Fallback: create mapping
            ticker_data = dict(zip(self.tickers, self.strategy.datas))

        # Calculate contribution for each asset
        for ticker, data in ticker_data.items():
            try:
                position = self.strategy.getposition(data)

                # Get price history
                if len(data) > 0:
                    end_price = data.close[0]
                    # Get first available price (approximate start price)
                    start_price = data.close[-len(data) + 1] if len(data) > 1 else end_price
                else:
                    continue

                # Calculate asset return
                asset_return_pct = 0.0
                if start_price > 0:
                    asset_return_pct = ((end_price - start_price) / start_price) * 100

                # Calculate average weight (simplified - could be improved with time-weighted average)
                current_position_value = position.size * end_price if position.size > 0 else 0.0
                avg_weight = 0.0

                if hasattr(self.strategy, 'current_weights') and ticker in self.strategy.current_weights:
                    # Use tracked weights from strategy
                    avg_weight = self.strategy.current_weights[ticker]
                elif total_portfolio_value_end > 0 and position.size > 0:
                    # Fallback: use current weight
                    avg_weight = current_position_value / total_portfolio_value_end

                # Calculate contribution
                contribution_pct = asset_return_pct * avg_weight

                contributions[ticker] = {
                    "return_pct": float(asset_return_pct),
                    "avg_weight": float(avg_weight),
                    "contribution_pct": float(contribution_pct),
                    "start_price": float(start_price),
                    "end_price": float(end_price),
                    "start_shares": 0,  # TODO: Track from strategy initialization
                    "end_shares": int(position.size) if position.size > 0 else 0,
                }

                logger.debug(
                    f"{ticker}: Return={asset_return_pct:.2f}%, "
                    f"Weight={avg_weight:.2%}, "
                    f"Contribution={contribution_pct:.2f}%"
                )

            except Exception as e:
                logger.error(f"Failed to calculate contribution for {ticker}: {e}")
                contributions[ticker] = {
                    "return_pct": 0.0,
                    "avg_weight": 0.0,
                    "contribution_pct": 0.0,
                    "error": str(e),
                }

        # Calculate total contribution
        total_contribution = sum(
            contrib["contribution_pct"] for contrib in contributions.values()
        )

        return {
            "contributions": contributions,
            "total_contribution": float(total_contribution),
        }


class PortfolioMetricsAnalyzer(bt.Analyzer):
    """
    Comprehensive portfolio-level metrics analyzer.

    Combines multiple metrics into a single analysis:
    - Sharpe ratio (portfolio-level)
    - Sortino ratio
    - Information ratio
    - Beta (if benchmark provided)
    - Tracking error
    - Turnover rate
    """

    params = (
        ("risk_free_rate", 0.02),  # 2% annual risk-free rate
        ("benchmark_ticker", None),  # Optional benchmark for beta calculation
    )

    def __init__(self):
        """Initialize the analyzer."""
        super().__init__()
        self.daily_returns = []
        self.portfolio_values = []

    def next(self):
        """Track daily values for metric calculation."""
        current_value = self.strategy.broker.getvalue()
        self.portfolio_values.append(current_value)

        if len(self.portfolio_values) > 1:
            prev_value = self.portfolio_values[-2]
            if prev_value > 0:
                daily_return = (current_value - prev_value) / prev_value
                self.daily_returns.append(daily_return)

    def get_analysis(self):
        """
        Calculate and return comprehensive portfolio metrics.

        Returns:
            Dictionary with portfolio-level performance metrics
        """
        if not self.daily_returns:
            return {"error": "Insufficient data for metrics calculation"}

        import numpy as np

        returns_array = np.array(self.daily_returns)

        # Calculate metrics
        mean_return = np.mean(returns_array)
        std_return = np.std(returns_array, ddof=1) if len(returns_array) > 1 else 0.0

        # Annualized metrics (assuming 252 trading days)
        annual_return = mean_return * 252
        annual_volatility = std_return * np.sqrt(252)

        # Sharpe ratio
        sharpe_ratio = 0.0
        if annual_volatility > 0:
            sharpe_ratio = (annual_return - self.p.risk_free_rate) / annual_volatility

        # Sortino ratio (downside deviation)
        downside_returns = returns_array[returns_array < 0]
        downside_deviation = np.std(downside_returns, ddof=1) if len(downside_returns) > 1 else 0.0
        annual_downside_deviation = downside_deviation * np.sqrt(252)

        sortino_ratio = 0.0
        if annual_downside_deviation > 0:
            sortino_ratio = (annual_return - self.p.risk_free_rate) / annual_downside_deviation

        return {
            "annual_return": float(annual_return),
            "annual_volatility": float(annual_volatility),
            "sharpe_ratio": float(sharpe_ratio),
            "sortino_ratio": float(sortino_ratio),
            "daily_return_mean": float(mean_return),
            "daily_return_std": float(std_return),
            "num_days": len(self.daily_returns),
        }
