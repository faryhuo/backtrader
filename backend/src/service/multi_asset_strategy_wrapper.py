"""
Multi-Asset Strategy Wrapper - Portfolio-level strategy managing multiple data feeds.

This module provides the MultiAssetPortfolioStrategy class which wraps around
user strategies to enable:
- Managing multiple data feeds (self.datas[0], self.datas[1], ...)
- Per-asset strategy parameter configuration
- Rolling returns tracking for portfolio optimization
- Rebalancing execution integration

The strategy acts as a portfolio manager that delegates to per-asset logic
while maintaining portfolio-level control.
"""

import logging
from collections import deque
from datetime import datetime
from typing import Optional

import backtrader as bt
import pandas as pd

from src.service.portfolio_rebalancer import (
    RebalanceScheduler,
    PortfolioRebalancer,
)
from src.service.portfolio_optimizer import get_optimizer

logger = logging.getLogger(__name__)


class MultiAssetPortfolioStrategy(bt.Strategy):
    """
    Portfolio-level strategy managing multiple data feeds.

    This strategy wraps around user-defined logic to provide portfolio-level
    features like rebalancing and equity curve tracking.

    Parameters:
        tickers (list): List of ticker symbols matching data feed order
        initial_weights (list): Initial allocation weights
        rebalance_config (dict): Rebalancing configuration
            Example: {"frequency": "monthly", "method": "risk_parity"}
        optimization_method (str): Optimization method for rebalancing
        returns_lookback (int): Number of days to track for rolling returns (default: 252)
    """

    params = (
        ("tickers", []),
        ("initial_weights", []),
        ("rebalance_config", None),
        ("optimization_method", "equal_weight"),
        ("returns_lookback", 252),
    )

    def __init__(self):
        """
        Initialize the multi-asset portfolio strategy.

        Sets up:
        - Ticker to data feed mapping
        - Per-asset indicators with custom parameters
        - Rolling returns storage
        - Rebalancer (if configured)
        """
        logger.info(f"Initializing MultiAssetPortfolioStrategy for {len(self.p.tickers)} assets")
        logger.info(f"Tickers: {self.p.tickers}")
        logger.info(f"Initial weights: {[f'{w:.2%}' for w in self.p.initial_weights]}")

        # Validate inputs
        if len(self.p.tickers) != len(self.datas):
            raise ValueError(
                f"Tickers length ({len(self.p.tickers)}) must match "
                f"data feeds length ({len(self.datas)})"
            )

        if len(self.p.initial_weights) != len(self.p.tickers):
            raise ValueError(
                f"Initial weights length ({len(self.p.initial_weights)}) must match "
                f"tickers length ({len(self.p.tickers)})"
            )

        # Step 1: Map tickers to data feeds
        self.ticker_data = dict(zip(self.p.tickers, self.datas))
        logger.debug(f"Mapped {len(self.ticker_data)} tickers to data feeds")

        # Step 2: Create default indicators for all assets
        self.indicators = {}
        for ticker, data in self.ticker_data.items():
            self.indicators[ticker] = self._create_indicators(ticker, data)

        logger.info(f"Created indicators for {len(self.indicators)} assets")

        # Step 3: Initialize rolling returns storage
        # Store last N daily returns for each asset for correlation/optimization
        self.returns_history = {
            ticker: deque(maxlen=self.p.returns_lookback)
            for ticker in self.p.tickers
        }

        # Track previous close prices for return calculation
        self.prev_close = {ticker: None for ticker in self.p.tickers}

        logger.debug(f"Initialized returns tracking with {self.p.returns_lookback}-day lookback")

        # Step 4: Initialize rebalancer
        self.rebalancer = None
        self.rebalance_dates = []
        if self.p.rebalance_config:
            logger.info(f"Rebalancing configured: {self.p.rebalance_config}")
            frequency = self.p.rebalance_config.get("frequency")

            if frequency:
                try:
                    # Create scheduler
                    scheduler = RebalanceScheduler(frequency)

                    # Create optimizer if not using equal weights
                    optimizer = None
                    if self.p.optimization_method and self.p.optimization_method != "equal_weight":
                        try:
                            optimizer = get_optimizer(self.p.optimization_method)
                            logger.info(f"Using optimizer: {self.p.optimization_method}")
                        except ValueError as e:
                            logger.warning(f"Failed to create optimizer: {e}. Using equal weights.")
                            optimizer = None

                    # Create rebalancer with optimizer
                    self.rebalancer = PortfolioRebalancer(
                        scheduler=scheduler,
                        optimizer=optimizer,
                        min_trade_threshold=self.p.rebalance_config.get("min_trade_threshold", 0.01),
                        transaction_cost_pct=self.p.rebalance_config.get("transaction_cost_pct", 0.001),
                    )

                    logger.info("Rebalancer initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize rebalancer: {e}")
                    self.rebalancer = None
            else:
                logger.warning("No rebalance frequency specified")

        # Step 5: Track current target weights (starts with initial weights)
        self.current_weights = dict(zip(self.p.tickers, self.p.initial_weights))

        # Step 6: Track if initial positions have been established
        self.initial_positions_set = False

        # Step 7: Rebalancing event log (for analyzer)
        self.rebalancing_events = []

        logger.info("MultiAssetPortfolioStrategy initialization complete")

    def start(self):
        """Called at the start of the backtest to initialize state."""
        # Generate rebalance dates if rebalancer is configured
        if self.rebalancer:
            # Get the date range from data
            start_date = self.datas[0].datetime.datetime(0)
            # We'll generate dates for the full backtest period
            # The scheduler will handle checking if we're on a rebalance date
            # For now, we'll generate dates on-the-fly in _should_rebalance()
            logger.info("Rebalancing scheduler ready")

    def _create_indicators(
        self, ticker: str, data: bt.feeds.DataBase
    ) -> dict:
        """
        Create default indicators for a single asset.

        Creates standard indicators with default values:
        - SMA (Simple Moving Average): period 20
        - RSI (Relative Strength Index): period 14, oversold 30, overbought 70

        Args:
            ticker: Ticker symbol
            data: Backtrader data feed

        Returns:
            Dictionary of indicators for this asset
        """
        indicators = {}
        created_indicators = []

        # SMA - Simple Moving Average with default period
        sma_period = 20
        indicators["sma"] = bt.indicators.SimpleMovingAverage(
            data.close, period=sma_period
        )
        created_indicators.append(f"SMA({sma_period})")

        # RSI - Relative Strength Index with default values
        rsi_period = 14
        indicators["rsi"] = bt.indicators.RSI(data.close, period=rsi_period)
        created_indicators.append(f"RSI({rsi_period})")

        # Store RSI thresholds for strategy logic
        indicators["rsi_oversold"] = 30
        indicators["rsi_overbought"] = 70

        logger.debug(f"{ticker}: Created indicators: {', '.join(created_indicators)}")

        return indicators

    def prenext(self):
        """Called before minimum period is satisfied for all indicators."""
        # During warmup period, just track returns without trading
        self._update_returns()

    def next(self):
        """
        Main strategy logic called on each bar.

        Handles:
        1. Update rolling returns
        2. Establish initial positions (first bar after warmup)
        3. Check for rebalancing trigger
        4. Execute trades
        """
        # Step 1: Update rolling returns for all assets
        self._update_returns()

        # Step 2: Establish initial positions (buy-and-hold based on initial weights)
        if not self.initial_positions_set:
            self._establish_initial_positions()
            self.initial_positions_set = True
            return

        # Step 3: Check if we should rebalance
        if self.rebalancer and self._should_rebalance():
            logger.info(f"Rebalancing triggered on {self.datetime.date(0)}")
            self._execute_rebalance()

        # Step 4: Execute per-asset trading logic
        # For now, this is just buy-and-hold
        # In Phase 4, we'll add support for custom user strategies per asset
        pass

    def _update_returns(self):
        """
        Update rolling returns for all assets.

        Calculates daily returns and stores them for portfolio optimization
        and correlation analysis.
        """
        for ticker, data in self.ticker_data.items():
            if len(data) < 2:
                # Not enough data to calculate returns
                continue

            current_close = data.close[0]
            prev_close = self.prev_close.get(ticker)

            if prev_close is not None and prev_close > 0:
                daily_return = (current_close - prev_close) / prev_close
                self.returns_history[ticker].append(daily_return)

            self.prev_close[ticker] = current_close

    def _establish_initial_positions(self):
        """
        Establish initial portfolio positions based on initial weights.

        Allocates capital to each asset according to initial_weights,
        buying whole shares based on current prices.
        """
        logger.info(f"Establishing initial positions on {self.datetime.date(0)}")

        total_value = self.broker.getvalue()
        logger.info(f"Total portfolio value: ${total_value:,.2f}")

        for ticker in self.p.tickers:
            target_weight = self.current_weights[ticker]
            data = self.ticker_data[ticker]
            current_price = data.close[0]

            # Calculate target position value
            target_value = total_value * target_weight

            # Calculate number of shares (round down to whole shares)
            target_shares = int(target_value / current_price)

            if target_shares > 0:
                logger.info(
                    f"{ticker}: Buying {target_shares} shares @ ${current_price:.2f} "
                    f"(target: ${target_value:,.2f}, weight: {target_weight:.2%})"
                )
                self.buy(data=data, size=target_shares)
            else:
                logger.warning(
                    f"{ticker}: Skipping buy (target weight {target_weight:.2%} "
                    f"= ${target_value:.2f} too small for 1 share @ ${current_price:.2f})"
                )

    def _should_rebalance(self) -> bool:
        """
        Check if portfolio should be rebalanced on current date.

        Returns:
            True if rebalancing should occur, False otherwise
        """
        if not self.rebalancer:
            return False

        current_date = self.datetime.datetime(0)

        # Generate rebalance dates if not done yet
        if not self.rebalance_dates:
            # We need to know the full date range - use a large window
            # In practice, the scheduler will check dates as we go
            try:
                # Get approximate end date (we don't know the exact end in advance)
                # So we'll check month-by-month
                from datetime import timedelta
                end_date = current_date + timedelta(days=365 * 5)  # 5 years lookahead
                self.rebalance_dates = self.rebalancer.scheduler.generate_rebalance_dates(
                    current_date, end_date
                )
                logger.info(f"Generated {len(self.rebalance_dates)} rebalance dates")
            except Exception as e:
                logger.error(f"Failed to generate rebalance dates: {e}")
                return False

        # Check if today is a rebalance date
        should_rebalance = self.rebalancer.scheduler.should_rebalance(
            current_date, self.rebalance_dates
        )

        if should_rebalance:
            logger.info(f"Rebalancing triggered on {current_date.date()}")

        return should_rebalance

    def _execute_rebalance(self):
        """
        Execute portfolio rebalancing.

        Steps:
        1. Gather current positions and prices
        2. Calculate target weights (via optimizer or equal weights)
        3. Calculate required trades
        4. Execute orders
        5. Log rebalancing event
        """
        current_date = self.datetime.datetime(0)
        logger.info(f"Executing rebalance on {current_date.date()}")

        # Step 1: Gather current state
        current_positions = {
            ticker: self.getposition(data).size
            for ticker, data in self.ticker_data.items()
        }
        current_prices = {
            ticker: data.close[0]
            for ticker, data in self.ticker_data.items()
        }
        pre_rebalance_value = self.broker.getvalue()

        logger.debug(f"Pre-rebalance value: ${pre_rebalance_value:,.2f}")
        logger.debug(f"Current positions: {current_positions}")

        # Step 2: Calculate target weights
        returns_df = self._get_returns_dataframe()
        target_weights = self.rebalancer.calculate_target_weights(
            self.p.tickers, returns_df
        )

        # Step 3: Calculate rebalancing orders
        rebalance_plan = self.rebalancer.calculate_rebalance_orders(
            current_positions,
            current_prices,
            pre_rebalance_value,
            target_weights,
        )

        # Step 4: Execute trades
        orders_executed = {}
        for ticker, delta in rebalance_plan['orders'].items():
            data = self.ticker_data[ticker]

            if delta > 0:
                # Buy
                order = self.buy(data=data, size=abs(delta))
                orders_executed[ticker] = delta
                logger.info(f"BUY {ticker}: {abs(delta)} shares @ ${current_prices[ticker]:.2f}")
            elif delta < 0:
                # Sell
                order = self.sell(data=data, size=abs(delta))
                orders_executed[ticker] = delta
                logger.info(f"SELL {ticker}: {abs(delta)} shares @ ${current_prices[ticker]:.2f}")

        # Note: Post-rebalance value will be calculated after orders execute
        # For now, estimate with transaction costs
        post_rebalance_value = pre_rebalance_value - rebalance_plan['estimated_cost']

        # Step 5: Record the event
        self.rebalancer.record_rebalance_event(
            date=current_date,
            trigger=self.rebalancer.scheduler.frequency,
            pre_value=pre_rebalance_value,
            post_value=post_rebalance_value,
            orders=orders_executed,
            target_weights=target_weights,
            transaction_cost=rebalance_plan['estimated_cost'],
        )

        # Update current target weights
        self.current_weights = target_weights

        # Notify analyzer if available
        if hasattr(self, 'analyzers') and hasattr(self.analyzers, 'rebalancing'):
            try:
                self.analyzers.rebalancing.notify_rebalance(
                    date=current_date.date(),
                    trigger=self.rebalancer.scheduler.frequency,
                    pre_value=pre_rebalance_value,
                    post_value=post_rebalance_value,
                    target_weights=target_weights,
                    orders=orders_executed,
                    transaction_cost=rebalance_plan['estimated_cost'],
                    pre_weights=rebalance_plan.get('pre_rebalance_weights', {}),
                    prices=current_prices,
                )
            except Exception as e:
                logger.warning(f"Failed to notify rebalancing analyzer: {e}")

        logger.info(
            f"Rebalancing complete: {len(orders_executed)} trades, "
            f"cost=${rebalance_plan['estimated_cost']:.2f}"
        )

    def _get_returns_dataframe(self) -> pd.DataFrame:
        """
        Convert rolling returns storage to pandas DataFrame for optimization.

        Returns:
            DataFrame with columns=tickers, rows=dates (most recent N days)
        """
        # Convert deque history to DataFrame
        returns_dict = {
            ticker: list(returns_deque)
            for ticker, returns_deque in self.returns_history.items()
        }

        # Find minimum length to ensure all columns have same length
        min_length = min(len(v) for v in returns_dict.values()) if returns_dict else 0

        if min_length == 0:
            logger.warning("No returns data available for optimization")
            return pd.DataFrame()

        # Truncate all to same length
        returns_dict_aligned = {
            ticker: returns[-min_length:] for ticker, returns in returns_dict.items()
        }

        df = pd.DataFrame(returns_dict_aligned)
        logger.debug(f"Returns DataFrame: {len(df)} days × {len(df.columns)} assets")

        return df

    def notify_order(self, order):
        """Handle order notifications from Backtrader."""
        if order.status in [order.Submitted, order.Accepted]:
            return

        # Get ticker name from data feed
        ticker = order.data._name if hasattr(order.data, '_name') else "UNKNOWN"

        if order.status == order.Completed:
            if order.isbuy():
                logger.debug(
                    f"{ticker} BUY EXECUTED: Price={order.executed.price:.2f}, "
                    f"Size={order.executed.size}, Cost={order.executed.value:.2f}, "
                    f"Comm={order.executed.comm:.2f}"
                )
            elif order.issell():
                logger.debug(
                    f"{ticker} SELL EXECUTED: Price={order.executed.price:.2f}, "
                    f"Size={order.executed.size}, Cost={order.executed.value:.2f}, "
                    f"Comm={order.executed.comm:.2f}"
                )

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            logger.warning(f"{ticker} ORDER {order.status}: {order}")

    def notify_trade(self, trade):
        """Handle trade notifications from Backtrader."""
        if not trade.isclosed:
            return

        ticker = trade.data._name if hasattr(trade.data, '_name') else "UNKNOWN"

        logger.debug(
            f"{ticker} TRADE CLOSED: PnL=${trade.pnl:.2f}, "
            f"Net PnL=${trade.pnlcomm:.2f}"
        )

    def stop(self):
        """Called when backtest ends. Log final statistics."""
        final_value = self.broker.getvalue()
        logger.info(f"Backtest complete. Final portfolio value: ${final_value:,.2f}")

        # Log final positions
        for ticker, data in self.ticker_data.items():
            position = self.getposition(data)
            if position.size > 0:
                current_price = data.close[0]
                position_value = position.size * current_price
                logger.info(
                    f"{ticker}: {position.size} shares @ ${current_price:.2f} "
                    f"= ${position_value:,.2f}"
                )


class BuyAndHoldPortfolioStrategy(MultiAssetPortfolioStrategy):
    """
    Simple buy-and-hold portfolio strategy with optional rebalancing.

    Buys initial positions based on weights and holds until end.
    If rebalance_config is provided, it will periodically rebalance
    to maintain target weights.
    """

    def next(self):
        """
        Main strategy logic - uses parent class for full functionality.
        
        Supports:
        - Initial position establishment
        - Periodic rebalancing (if configured)
        """
        # Use parent class implementation which includes rebalancing
        super().next()
