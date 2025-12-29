"""
Cerebro Builder - Fluent builder for Backtrader Cerebro instances.

This module provides a fluent API for constructing Cerebro instances,
separating the construction logic from backtest execution.

Usage:
    cerebro = (CerebroBuilder(config)
        .with_broker_settings()
        .with_data_feeds(aligned_feeds)
        .with_strategy(strategy_cls)
        .with_portfolio_analyzers()
        .build())
"""

from typing import Dict, List, Optional, Type, Any
import logging

import backtrader as bt

from .backtest_config import BacktestConfig

logger = logging.getLogger(__name__)


class CerebroBuilder:
    """
    Fluent builder for Backtrader Cerebro instances.

    Encapsulates the construction of a Cerebro instance with all necessary
    components (broker, data feeds, strategy, analyzers) configured according
    to the provided BacktestConfig.

    The builder pattern provides:
    - Clear, readable configuration code
    - Separation of construction from execution
    - Easy testing (can verify each step independently)
    - Flexible composition of components
    """

    def __init__(self, config: BacktestConfig):
        """
        Initialize the builder with a configuration.

        Args:
            config: Validated BacktestConfig instance
        """
        self.config = config
        self.cerebro = bt.Cerebro()
        self._data_feeds: Dict[str, bt.feeds.DataBase] = {}
        self._strategy_added = False
        self._analyzers_added = False

        logger.debug(f"CerebroBuilder initialized for {len(config.tickers)} tickers")

    def with_broker_settings(self) -> "CerebroBuilder":
        """
        Configure the broker with cash and commission settings.

        Returns:
            Self for method chaining
        """
        self.cerebro.broker.setcash(self.config.initial_cash)
        self.cerebro.broker.setcommission(commission=self.config.commission)

        logger.info(
            f"Broker configured: ${self.config.initial_cash:,.2f} cash, "
            f"{self.config.commission:.4%} commission"
        )

        return self

    def with_data_feeds(
        self,
        feeds: Dict[str, bt.feeds.DataBase]
    ) -> "CerebroBuilder":
        """
        Add aligned data feeds to Cerebro.

        Data feeds are added in the order specified by config.tickers
        to ensure consistent indexing via strategy.datas[i].

        Args:
            feeds: Dictionary mapping ticker symbols to data feeds

        Returns:
            Self for method chaining

        Raises:
            ValueError: If any configured ticker is missing from feeds
        """
        missing_tickers = set(self.config.tickers) - set(feeds.keys())
        if missing_tickers:
            raise ValueError(f"Missing data feeds for tickers: {missing_tickers}")

        for ticker in self.config.tickers:
            feed = feeds[ticker]
            self.cerebro.adddata(feed, name=ticker)
            self._data_feeds[ticker] = feed
            logger.debug(f"Added data feed: {ticker}")

        logger.info(f"Added {len(self.config.tickers)} data feeds to Cerebro")

        return self

    def with_strategy(
        self,
        strategy_cls: Type[bt.Strategy],
        extra_params: Optional[Dict[str, Any]] = None
    ) -> "CerebroBuilder":
        """
        Add the user strategy to Cerebro.

        Merges config.params with any extra_params, with extra_params taking
        precedence in case of conflicts.

        Args:
            strategy_cls: Strategy class (subclass of bt.Strategy)
            extra_params: Additional parameters to pass to strategy

        Returns:
            Self for method chaining

        Raises:
            ValueError: If strategy has already been added
        """
        if self._strategy_added:
            raise ValueError("Strategy has already been added to Cerebro")

        # Merge parameters
        params = dict(self.config.params or {})
        if extra_params:
            params.update(extra_params)

        # Add portfolio-specific params
        params.update({
            "tickers": self.config.tickers,
            "initial_weights": self.config.weights,
        })

        self.cerebro.addstrategy(strategy_cls, **params)
        self._strategy_added = True

        logger.info(f"Added strategy: {strategy_cls.__name__}")
        if params:
            logger.debug(f"Strategy params: {params}")

        return self

    def with_wrapper_strategy(
        self,
        wrapper_cls: Type[bt.Strategy],
        user_strategy_cls: Type[bt.Strategy],
        extra_params: Optional[Dict[str, Any]] = None
    ) -> "CerebroBuilder":
        """
        Add a wrapper strategy that wraps the user strategy.

        This is used for the MultiAssetPortfolioStrategy which wraps
        user strategies to provide portfolio management features.

        Args:
            wrapper_cls: Wrapper strategy class
            user_strategy_cls: User's strategy class to wrap
            extra_params: Additional parameters

        Returns:
            Self for method chaining
        """
        if self._strategy_added:
            raise ValueError("Strategy has already been added to Cerebro")

        # Merge parameters
        params = dict(self.config.params or {})
        if extra_params:
            params.update(extra_params)

        # Add portfolio-specific params
        params.update({
            "tickers": self.config.tickers,
            "initial_weights": self.config.weights,
            "user_strategy_cls": user_strategy_cls,
        })

        self.cerebro.addstrategy(wrapper_cls, **params)
        self._strategy_added = True

        logger.info(f"Added wrapper strategy: {wrapper_cls.__name__}")
        logger.debug(f"Wrapping user strategy: {user_strategy_cls.__name__}")

        return self

    def with_standard_analyzers(self) -> "CerebroBuilder":
        """
        Add standard Backtrader analyzers.

        Adds:
        - SharpeRatio
        - DrawDown
        - Returns
        - TradeAnalyzer

        Returns:
            Self for method chaining
        """
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

        logger.debug("Added standard analyzers (SharpeRatio, DrawDown, Returns, TradeAnalyzer)")

        return self

    def with_portfolio_analyzers(self) -> "CerebroBuilder":
        """
        Add portfolio-specific analyzers.

        Adds custom analyzers for portfolio tracking:
        - PortfolioValueAnalyzer
        - AssetContributionAnalyzer
        - PortfolioMetricsAnalyzer
        - PortfolioTradeRecorder

        Returns:
            Self for method chaining
        """
        if self._analyzers_added:
            logger.warning("Analyzers already added, skipping")
            return self

        # Import here to avoid circular imports
        from src.service.portfolio_analyzers import (
            PortfolioValueAnalyzer,
            AssetContributionAnalyzer,
            PortfolioMetricsAnalyzer,
            PortfolioTradeRecorder,
        )

        self.cerebro.addanalyzer(
            PortfolioValueAnalyzer,
            _name="portfolio_value"
        )
        self.cerebro.addanalyzer(
            AssetContributionAnalyzer,
            _name="contributions",
            tickers=self.config.tickers,
            initial_weights=self.config.weights
        )
        self.cerebro.addanalyzer(
            PortfolioMetricsAnalyzer,
            _name="portfolio_metrics"
        )
        self.cerebro.addanalyzer(
            PortfolioTradeRecorder,
            _name="trade_recorder"
        )

        self._analyzers_added = True

        logger.info("Added portfolio analyzers")

        return self

    def with_sizer(
        self,
        sizer_cls: Type[bt.Sizer],
        **kwargs
    ) -> "CerebroBuilder":
        """
        Add a position sizer.

        Args:
            sizer_cls: Sizer class
            **kwargs: Sizer parameters

        Returns:
            Self for method chaining
        """
        self.cerebro.addsizer(sizer_cls, **kwargs)

        logger.debug(f"Added sizer: {sizer_cls.__name__}")

        return self

    def with_observer(
        self,
        observer_cls: Type[bt.Observer],
        **kwargs
    ) -> "CerebroBuilder":
        """
        Add an observer.

        Args:
            observer_cls: Observer class
            **kwargs: Observer parameters

        Returns:
            Self for method chaining
        """
        self.cerebro.addobserver(observer_cls, **kwargs)

        logger.debug(f"Added observer: {observer_cls.__name__}")

        return self

    def build(self) -> bt.Cerebro:
        """
        Build and return the configured Cerebro instance.

        Returns:
            Fully configured Cerebro instance ready for running

        Raises:
            ValueError: If required components are missing
        """
        if not self._data_feeds:
            raise ValueError("No data feeds added. Call with_data_feeds() first.")

        if not self._strategy_added:
            raise ValueError("No strategy added. Call with_strategy() first.")

        logger.info(
            f"Built Cerebro: {len(self._data_feeds)} feeds, "
            f"analyzers={self._analyzers_added}"
        )

        return self.cerebro

    def get_data_feeds(self) -> Dict[str, bt.feeds.DataBase]:
        """Get the added data feeds."""
        return self._data_feeds.copy()

    def __repr__(self) -> str:
        return (
            f"CerebroBuilder(tickers={len(self.config.tickers)}, "
            f"feeds={len(self._data_feeds)}, "
            f"strategy={self._strategy_added}, "
            f"analyzers={self._analyzers_added})"
        )


__all__ = ["CerebroBuilder"]
