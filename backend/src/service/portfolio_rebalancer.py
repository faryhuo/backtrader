"""
Portfolio Rebalancer - Rebalancing scheduler and execution logic.

This module provides components for portfolio rebalancing:
- RebalanceScheduler: Generates rebalancing dates based on frequency
- PortfolioRebalancer: Calculates target positions and executes orders
- Integration with portfolio optimizers for dynamic weight calculation

Rebalancing strategies supported:
- Fixed schedule (monthly, quarterly, annually)
- Threshold-based (when allocation drift exceeds threshold)
- Dynamic optimization (recalculate optimal weights at each rebalance)
"""

import logging
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from src.service.portfolio.date_generator import (
    RebalanceDateGenerator,
    is_rebalance_date,
)

logger = logging.getLogger(__name__)


class RebalanceScheduler:
    """
    Schedule generator for portfolio rebalancing.

    Determines when rebalancing should occur based on configured frequency.
    Supports:
    - Monthly rebalancing (first/last trading day of month)
    - Quarterly rebalancing (first/last trading day of quarter)
    - Annual rebalancing (first/last trading day of year)
    - Custom day-of-month scheduling
    """

    SUPPORTED_FREQUENCIES = [
        "monthly",
        "monthly_first",  # First trading day of month
        "monthly_last",   # Last trading day of month
        "quarterly",
        "quarterly_first",
        "quarterly_last",
        "annually",
        "annually_first",
        "annually_last",
    ]

    def __init__(self, frequency: str, custom_day: Optional[int] = None):
        """
        Initialize the rebalance scheduler.

        Args:
            frequency: Rebalancing frequency (monthly, quarterly, annually, etc.)
            custom_day: Day of month for custom scheduling (1-31)
                        If specified, rebalances on this day each period

        Raises:
            ValueError: If frequency is not supported
        """
        if frequency not in self.SUPPORTED_FREQUENCIES:
            raise ValueError(
                f"Unsupported frequency: {frequency}. "
                f"Supported: {', '.join(self.SUPPORTED_FREQUENCIES)}"
            )

        self.frequency = frequency
        self.custom_day = custom_day
        self._rebalance_dates = None  # Cache for generated dates

        logger.info(f"RebalanceScheduler initialized: {frequency}")
        if custom_day:
            logger.info(f"Custom day-of-month: {custom_day}")

    def generate_rebalance_dates(
        self, start_date: datetime, end_date: datetime
    ) -> list[datetime]:
        """
        Generate all rebalancing dates within the date range.

        Uses the unified RebalanceDateGenerator for consistent date generation
        across all frequency types.

        Args:
            start_date: Backtest start date
            end_date: Backtest end date

        Returns:
            List of datetime objects representing rebalancing dates
        """
        logger.info(f"Generating rebalance dates: {start_date.date()} to {end_date.date()}")

        dates = RebalanceDateGenerator.generate(
            frequency=self.frequency,
            start_date=start_date,
            end_date=end_date,
            custom_day=self.custom_day
        )

        logger.info(f"Generated {len(dates)} rebalancing dates")
        return dates

    def should_rebalance(
        self, current_date: datetime, rebalance_dates: Optional[list[datetime]] = None
    ) -> bool:
        """
        Check if rebalancing should occur on the current date.

        Uses O(1) set-based lookup via is_rebalance_date for efficiency.

        Args:
            current_date: Current trading date
            rebalance_dates: Pre-generated list of rebalance dates (optional)

        Returns:
            True if current_date is a rebalancing date
        """
        if rebalance_dates is None:
            logger.warning("No rebalance_dates provided to should_rebalance()")
            return False

        return is_rebalance_date(current_date, rebalance_dates)


class PortfolioRebalancer:
    """
    Portfolio rebalancing calculator and executor.

    Responsibilities:
    - Calculate current portfolio weights
    - Determine target weights (via optimizer or fixed weights)
    - Calculate required trades to reach target allocation
    - Estimate transaction costs
    - Track rebalancing history
    """

    def __init__(
        self,
        scheduler: RebalanceScheduler,
        optimizer=None,  # Will be a PortfolioOptimizer instance (Phase 3)
        min_trade_threshold: float = 0.01,  # 1% minimum position change to trade
        transaction_cost_pct: float = 0.001,  # 0.1% transaction cost
    ):
        """
        Initialize the portfolio rebalancer.

        Args:
            scheduler: RebalanceScheduler instance
            optimizer: PortfolioOptimizer instance (None = use fixed weights)
            min_trade_threshold: Minimum position change % to execute trade
            transaction_cost_pct: Transaction cost as % of trade value
        """
        self.scheduler = scheduler
        self.optimizer = optimizer
        self.min_trade_threshold = min_trade_threshold
        self.transaction_cost_pct = transaction_cost_pct

        # Track rebalancing history
        self.rebalancing_history = []

        logger.info(f"PortfolioRebalancer initialized")
        logger.info(f"  Scheduler: {scheduler.frequency}")
        logger.info(f"  Optimizer: {optimizer.__class__.__name__ if optimizer else 'Fixed weights'}")
        logger.info(f"  Min trade threshold: {min_trade_threshold:.1%}")
        logger.info(f"  Transaction cost: {transaction_cost_pct:.2%}")

    def calculate_current_weights(
        self,
        positions: dict[str, float],  # {ticker: shares}
        prices: dict[str, float],  # {ticker: current_price}
        total_value: float,
    ) -> dict[str, float]:
        """
        Calculate current portfolio weights.

        Args:
            positions: Current positions {ticker: shares}
            prices: Current prices {ticker: price}
            total_value: Total portfolio value (cash + positions)

        Returns:
            Dictionary of current weights {ticker: weight}
        """
        if total_value <= 0:
            logger.warning("Total portfolio value is zero or negative")
            return {ticker: 0.0 for ticker in positions.keys()}

        current_weights = {}

        for ticker, shares in positions.items():
            if ticker not in prices:
                logger.warning(f"No price available for {ticker}")
                current_weights[ticker] = 0.0
                continue

            position_value = shares * prices[ticker]
            weight = position_value / total_value
            current_weights[ticker] = weight

        logger.debug(f"Current weights: {current_weights}")
        return current_weights

    def calculate_target_weights(
        self,
        tickers: list[str],
        returns_df: pd.DataFrame,
        current_weights: Optional[dict[str, float]] = None,
    ) -> dict[str, float]:
        """
        Calculate target portfolio weights.

        If optimizer is configured, uses optimizer to calculate optimal weights.
        Otherwise, uses equal weighting.

        Args:
            tickers: List of ticker symbols
            returns_df: Historical returns DataFrame for optimization
            current_weights: Current portfolio weights (optional, for some optimizers)

        Returns:
            Dictionary of target weights {ticker: weight}
        """
        if self.optimizer is not None:
            # Use optimizer to calculate optimal weights (Phase 3)
            logger.info(f"Calculating optimal weights using {self.optimizer.__class__.__name__}")
            try:
                optimization_result = self.optimizer.optimize(returns_df)
                target_weights = dict(zip(tickers, optimization_result["weights"]))
                logger.info(f"Optimized weights: {target_weights}")
                return target_weights
            except Exception as e:
                logger.error(f"Optimization failed: {e}. Falling back to equal weights.")
                # Fall through to equal weights

        # Default: Equal weighting
        equal_weight = 1.0 / len(tickers)
        target_weights = {ticker: equal_weight for ticker in tickers}
        logger.info(f"Using equal weights: {equal_weight:.2%} per asset")

        return target_weights

    def calculate_rebalance_orders(
        self,
        current_positions: dict[str, float],
        current_prices: dict[str, float],
        total_value: float,
        target_weights: dict[str, float],
    ) -> dict:
        """
        Calculate orders needed to rebalance portfolio to target weights.

        Args:
            current_positions: Current positions {ticker: shares}
            current_prices: Current prices {ticker: price}
            total_value: Total portfolio value
            target_weights: Target allocation {ticker: weight}

        Returns:
            Dictionary with:
            {
                "orders": {ticker: shares_delta},
                "target_weights": {ticker: weight},
                "estimated_cost": float,
                "pre_rebalance_weights": {ticker: weight}
            }
        """
        logger.info("Calculating rebalance orders...")

        # Calculate current weights
        current_weights = self.calculate_current_weights(
            current_positions, current_prices, total_value
        )

        orders = {}
        total_trade_value = 0.0

        for ticker, target_weight in target_weights.items():
            current_weight = current_weights.get(ticker, 0.0)
            price = current_prices.get(ticker, 0.0)

            if price <= 0:
                logger.warning(f"Invalid price for {ticker}: {price}")
                continue

            # Calculate target shares
            target_value = total_value * target_weight
            target_shares = int(target_value / price)

            # Calculate current shares
            current_shares = current_positions.get(ticker, 0)

            # Calculate delta
            delta_shares = target_shares - current_shares

            # Check if change is significant enough to trade
            weight_change = abs(target_weight - current_weight)
            if weight_change < self.min_trade_threshold:
                logger.debug(
                    f"{ticker}: Weight change {weight_change:.2%} below threshold "
                    f"{self.min_trade_threshold:.2%}, skipping"
                )
                continue

            if delta_shares != 0:
                orders[ticker] = delta_shares
                trade_value = abs(delta_shares) * price
                total_trade_value += trade_value

                logger.info(
                    f"{ticker}: {current_shares} → {target_shares} shares "
                    f"({current_weight:.2%} → {target_weight:.2%})"
                )

        # Estimate transaction costs
        estimated_cost = total_trade_value * self.transaction_cost_pct

        result = {
            "orders": orders,
            "target_weights": target_weights,
            "pre_rebalance_weights": current_weights,
            "estimated_cost": estimated_cost,
            "total_trade_value": total_trade_value,
        }

        logger.info(f"Rebalancing plan: {len(orders)} trades, ${total_trade_value:,.2f} traded")
        logger.info(f"Estimated transaction cost: ${estimated_cost:,.2f}")

        return result

    def record_rebalance_event(
        self,
        date: datetime,
        trigger: str,
        pre_value: float,
        post_value: float,
        orders: dict[str, int],
        target_weights: dict[str, float],
        transaction_cost: float,
    ):
        """
        Record a rebalancing event in history.

        Args:
            date: Rebalancing date
            trigger: Trigger reason (e.g., "monthly_schedule")
            pre_value: Portfolio value before rebalancing
            post_value: Portfolio value after rebalancing
            orders: Orders executed {ticker: shares_delta}
            target_weights: Target allocation
            transaction_cost: Actual transaction cost incurred
        """
        event = {
            "date": date.isoformat() if isinstance(date, datetime) else str(date),
            "trigger": trigger,
            "pre_rebalance_value": float(pre_value),
            "post_rebalance_value": float(post_value),
            "orders": {k: int(v) for k, v in orders.items()},
            "target_weights": {k: float(v) for k, v in target_weights.items()},
            "transaction_cost": float(transaction_cost),
        }

        self.rebalancing_history.append(event)

        logger.info(
            f"Recorded rebalancing event: {date.date() if isinstance(date, datetime) else date}, "
            f"cost=${transaction_cost:.2f}"
        )

    def get_rebalancing_history(self) -> list[dict]:
        """
        Get the complete rebalancing history.

        Returns:
            List of rebalancing events
        """
        return self.rebalancing_history
