"""
Unit tests for multi asset strategy wrapper module.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestMultiAssetStrategyWrapperImports:
    """Tests for multi asset strategy wrapper module imports."""

    def test_module_import(self):
        """Test that module can be imported."""
        from src.service import multi_asset_strategy_wrapper
        assert multi_asset_strategy_wrapper is not None

    def test_multi_asset_portfolio_strategy_import(self):
        """Test that MultiAssetPortfolioStrategy class can be imported."""
        from src.service.multi_asset_strategy_wrapper import MultiAssetPortfolioStrategy
        assert MultiAssetPortfolioStrategy is not None

    def test_buy_and_hold_strategy_import(self):
        """Test that BuyAndHoldPortfolioStrategy class can be imported."""
        from src.service.multi_asset_strategy_wrapper import BuyAndHoldPortfolioStrategy
        assert BuyAndHoldPortfolioStrategy is not None


class TestMultiAssetPortfolioStrategy:
    """Tests for MultiAssetPortfolioStrategy class."""

    def test_strategy_is_backtrader_strategy(self):
        """Test that strategy inherits from backtrader Strategy."""
        import backtrader as bt
        from src.service.multi_asset_strategy_wrapper import MultiAssetPortfolioStrategy
        assert issubclass(MultiAssetPortfolioStrategy, bt.Strategy)


class TestBuyAndHoldPortfolioStrategy:
    """Tests for BuyAndHoldPortfolioStrategy class."""

    def test_strategy_is_multi_asset_strategy(self):
        """Test that BuyAndHoldPortfolioStrategy inherits from MultiAssetPortfolioStrategy."""
        from src.service.multi_asset_strategy_wrapper import (
            MultiAssetPortfolioStrategy,
            BuyAndHoldPortfolioStrategy,
        )
        assert issubclass(BuyAndHoldPortfolioStrategy, MultiAssetPortfolioStrategy)
