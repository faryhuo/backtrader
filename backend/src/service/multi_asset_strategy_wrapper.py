"""
Multi-Asset Strategy Wrapper - Portfolio-level strategy managing multiple data feeds.

This module provides the MultiAssetPortfolioStrategy class which wraps around
user strategies to enable:
- Managing multiple data feeds (self.datas[0], self.datas[1], ...)
- Per-asset strategy parameter configuration
- Rolling returns tracking for portfolio optimization

The strategy acts as a portfolio manager that delegates to per-asset logic
while maintaining portfolio-level control.
"""

import logging
from collections import deque
from datetime import datetime, timedelta
from typing import Optional

import backtrader as bt
import pandas as pd

from src.service.portfolio.trade_recorder import TradeRecorder, TradeTrigger
from src.service.portfolio.events import PortfolioEventBus, PortfolioEventType
from src.utils.backtrader_helpers import get_data_name

logger = logging.getLogger(__name__)


class MultiAssetPortfolioStrategy(bt.Strategy):
    """
    Portfolio-level strategy managing multiple data feeds.

    This strategy wraps around user-defined logic to provide portfolio-level
    features like equity curve tracking.

    Parameters:
        tickers (list): List of ticker symbols matching data feed order
        initial_weights (list): Initial allocation weights
        returns_lookback (int): Number of days to track for rolling returns (default: 252)
    """

    params = (
        ("tickers", []),
        ("initial_weights", []),
        ("returns_lookback", 252),
    )

    def __init__(self):
        """
        Initialize the multi-asset portfolio strategy.

        Sets up:
        - Ticker to data feed mapping
        - Per-asset indicators with custom parameters
        - Rolling returns storage
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

        # Step 4: Track current target weights (starts with initial weights)
        self.current_weights = dict(zip(self.p.tickers, self.p.initial_weights))

        # Step 5: Track if initial positions have been established
        self.initial_positions_set = False

        # Step 6: Initialize TradeRecorder for centralized trade recording
        self.trade_recorder = TradeRecorder()

        # Step 7: Initialize EventBus for loose coupling with analyzers
        self.event_bus = PortfolioEventBus()

        logger.info("MultiAssetPortfolioStrategy initialization complete")

    def start(self):
        """Called at the start of the backtest to initialize state."""
        pass  # No additional initialization needed

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
        3. Execute trades
        """
        # Step 1: Update rolling returns for all assets
        self._update_returns()

        # Step 2: Establish initial positions (buy-and-hold based on initial weights)
        if not self.initial_positions_set:
            self._establish_initial_positions()
            self.initial_positions_set = True
            return

        # Step 3: Execute per-asset trading logic
        # For now, this is just buy-and-hold
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
        available_cash = self.broker.getcash()
        logger.info(f"Total portfolio value: ${total_value:,.2f}, Available cash: ${available_cash:,.2f}")

        # First pass: calculate all target shares and total required value
        order_plan = {}
        total_required = 0.0
        
        for ticker in self.p.tickers:
            target_weight = self.current_weights[ticker]
            data = self.ticker_data[ticker]
            
            # Check if data is valid
            if len(data) == 0:
                logger.error(f"{ticker}: No data available! Cannot establish position.")
                continue
                
            current_price = data.close[0]
            
            # Validate price
            if current_price is None or current_price <= 0:
                logger.error(f"{ticker}: Invalid price ({current_price})! Cannot establish position.")
                continue

            # Calculate target position value based on AVAILABLE CASH, not total value
            # This ensures we don't try to spend more than we have
            target_value = available_cash * target_weight

            # Calculate number of shares (round down to whole shares)
            target_shares = int(target_value / current_price)
            required_value = target_shares * current_price

            if target_shares > 0:
                order_plan[ticker] = {
                    'data': data,
                    'shares': target_shares,
                    'price': current_price,
                    'value': required_value,
                    'weight': target_weight,
                }
                total_required += required_value
                
            logger.info(
                f"{ticker}: price=${current_price:.2f}, target_weight={target_weight:.2%}, "
                f"target_value=${target_value:,.2f}, target_shares={target_shares}, "
                f"required_value=${required_value:,.2f}"
            )

        # Safety check: if total required exceeds available cash, scale down proportionally
        if total_required > available_cash * 0.99:  # Leave 1% buffer
            scale_factor = (available_cash * 0.98) / total_required
            logger.warning(
                f"Total required (${total_required:,.2f}) exceeds available cash (${available_cash:,.2f}). "
                f"Scaling down by factor {scale_factor:.4f}"
            )
            for ticker in order_plan:
                old_shares = order_plan[ticker]['shares']
                new_shares = int(old_shares * scale_factor)
                order_plan[ticker]['shares'] = new_shares
                order_plan[ticker]['value'] = new_shares * order_plan[ticker]['price']
                logger.info(f"{ticker}: Reduced shares from {old_shares} to {new_shares}")

        # Second pass: place orders and record trades
        orders_placed = []
        current_date = self.datetime.date(0)

        for ticker, plan in order_plan.items():
            if plan['shares'] > 0:
                logger.info(
                    f"{ticker}: Buying {plan['shares']} shares @ ${plan['price']:.2f} "
                    f"(value: ${plan['value']:,.2f}, weight: {plan['weight']:.2%})"
                )
                order = self.buy(data=plan['data'], size=plan['shares'])
                if order:
                    orders_placed.append((ticker, plan['shares'], order))
                    logger.info(f"{ticker}: Order placed successfully, order ref: {order.ref}")

                    # Record the trade using TradeRecorder
                    self.trade_recorder.record_buy(
                        trade_date=current_date,
                        ticker=ticker,
                        shares=plan['shares'],
                        price=plan['price'],
                        trigger=TradeTrigger.INITIAL_POSITION,
                        value=plan['value'],
                    )
                else:
                    logger.error(f"{ticker}: Buy order returned None!")

        logger.info(f"Initial positions: {len(orders_placed)} orders placed for {len(self.p.tickers)} tickers")
        logger.info(f"All trades recorded so far: {self.trade_recorder.trade_count} trades")
    def notify_order(self, order):
        """Handle order notifications from Backtrader."""
        if order.status in [order.Submitted, order.Accepted]:
            return

        # Get ticker name using helper function
        ticker = get_data_name(order.data)

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

        ticker = get_data_name(trade.data)

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

    @property
    def all_trades(self) -> list:
        """
        Get all trades recorded by this strategy.

        Delegates to TradeRecorder for centralized trade management.

        Returns:
            List of trade dictionaries
        """
        return self.trade_recorder.get_all_trades()


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
