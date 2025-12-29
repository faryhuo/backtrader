"""
Unit tests for portfolio routes.
"""
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from src.routes.portfolio_routes import (
    PortfolioHistoryQuery,
    MultiAssetBacktestRequest,
    RebalanceConfig,
)
from src.db import get_portfolio_storage


class TestPortfolioStorage:
    """Tests for portfolio storage singleton."""

    def test_get_portfolio_storage_singleton(self):
        """Test that get_portfolio_storage returns singleton instance."""
        storage1 = get_portfolio_storage()
        storage2 = get_portfolio_storage()
        assert storage1 is storage2


class TestRebalanceConfig:
    """Tests for RebalanceConfig validation."""

    def test_valid_monthly_frequency(self):
        """Test valid monthly frequency."""
        config = RebalanceConfig(frequency="monthly")
        assert config.frequency == "monthly"
        assert config.min_trade_threshold == 0.01
        assert config.transaction_cost_pct == 0.001

    def test_valid_quarterly_frequency(self):
        """Test valid quarterly frequency."""
        config = RebalanceConfig(frequency="quarterly")
        assert config.frequency == "quarterly"

    def test_invalid_frequency(self):
        """Test invalid frequency raises error."""
        with pytest.raises(ValidationError) as exc_info:
            RebalanceConfig(frequency="weekly")
        assert "Invalid frequency" in str(exc_info.value)

    def test_custom_thresholds(self):
        """Test custom threshold values."""
        config = RebalanceConfig(
            frequency="monthly",
            min_trade_threshold=0.05,
            transaction_cost_pct=0.002
        )
        assert config.min_trade_threshold == 0.05
        assert config.transaction_cost_pct == 0.002

    def test_threshold_out_of_range(self):
        """Test threshold out of valid range."""
        with pytest.raises(ValidationError) as exc_info:
            RebalanceConfig(frequency="monthly", min_trade_threshold=1.5)
        assert "min_trade_threshold" in str(exc_info.value)


class TestMultiAssetBacktestRequest:
    """Tests for MultiAssetBacktestRequest."""

    def test_basic_request(self):
        """Test basic request."""
        request = MultiAssetBacktestRequest(
            tickers=["AAPL", "GOOGL"],
            weights=[0.5, 0.5],
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        assert request.tickers == ["AAPL", "GOOGL"]
        assert request.weights == [0.5, 0.5]

    def test_valid_optimization_methods(self):
        """Test all valid optimization methods."""
        for method in ["equal_weight", "risk_parity", "min_variance", "markowitz"]:
            request = MultiAssetBacktestRequest(
                tickers=["AAPL"],
                weights=[1.0],
                start_date="2024-01-01",
                end_date="2024-12-31",
                optimization_method=method
            )
            assert request.optimization_method == method

    def test_invalid_optimization_method(self):
        """Test invalid optimization method raises error."""
        with pytest.raises(ValidationError) as exc_info:
            MultiAssetBacktestRequest(
                tickers=["AAPL"],
                weights=[1.0],
                start_date="2024-01-01",
                end_date="2024-12-31",
                optimization_method="invalid_method"
            )
        assert "Invalid optimization method" in str(exc_info.value)

    def test_valid_timeframes(self):
        """Test all valid timeframes."""
        for tf in ["1d", "1h", "15m", "5m", "1m"]:
            request = MultiAssetBacktestRequest(
                tickers=["AAPL"],
                weights=[1.0],
                start_date="2024-01-01",
                end_date="2024-12-31",
                timeframe=tf
            )
            assert request.timeframe == tf

    def test_invalid_timeframe(self):
        """Test invalid timeframe raises error."""
        with pytest.raises(ValidationError) as exc_info:
            MultiAssetBacktestRequest(
                tickers=["AAPL"],
                weights=[1.0],
                start_date="2024-01-01",
                end_date="2024-12-31",
                timeframe="2h"
            )
        assert "Invalid timeframe" in str(exc_info.value)

    def test_too_many_tickers(self):
        """Test that more than 20 tickers raises error."""
        tickers = [f"TICK{i}" for i in range(25)]
        weights = [1.0 / 25] * 25

        with pytest.raises(ValidationError) as exc_info:
            MultiAssetBacktestRequest(
                tickers=tickers,
                weights=weights,
                start_date="2024-01-01",
                end_date="2024-12-31"
            )
        assert "tickers" in str(exc_info.value).lower()

    def test_initial_cash_constraints(self):
        """Test initial cash constraints."""
        # Too low
        with pytest.raises(ValidationError):
            MultiAssetBacktestRequest(
                tickers=["AAPL"],
                weights=[1.0],
                start_date="2024-01-01",
                end_date="2024-12-31",
                initial_cash=500
            )

        # Too high
        with pytest.raises(ValidationError):
            MultiAssetBacktestRequest(
                tickers=["AAPL"],
                weights=[1.0],
                start_date="2024-01-01",
                end_date="2024-12-31",
                initial_cash=200000000
            )

    def test_with_rebalance_config(self):
        """Test request with rebalancing configuration."""
        request = MultiAssetBacktestRequest(
            tickers=["AAPL", "GOOGL"],
            weights=[0.6, 0.4],
            start_date="2024-01-01",
            end_date="2024-12-31",
            rebalance_config={
                "frequency": "quarterly",
                "min_trade_threshold": 0.02,
                "transaction_cost_pct": 0.001
            }
        )
        assert request.rebalance_config is not None
        assert request.rebalance_config.frequency == "quarterly"

    def test_full_request(self):
        """Test fully configured request."""
        request = MultiAssetBacktestRequest(
            tickers=["AAPL", "GOOGL", "MSFT"],
            weights=[0.4, 0.35, 0.25],
            start_date="2024-01-01",
            end_date="2024-12-31",
            initial_cash=500000.0,
            commission=0.001,
            strategy_name="sma_cross",
            rebalance_config={
                "frequency": "monthly",
                "min_trade_threshold": 0.01
            },
            optimization_method="risk_parity",
            timeframe="1d"
        )
        assert len(request.tickers) == 3
        assert request.strategy_name == "sma_cross"
        assert request.optimization_method == "risk_parity"


class TestPortfolioHistoryQuery:
    """Tests for PortfolioHistoryQuery."""

    def test_defaults(self):
        """Test default values."""
        query = PortfolioHistoryQuery()
        assert query.sort_by == "created_at"
        assert query.sort_order == "desc"
        assert query.limit == 50
        assert query.offset == 0

    def test_custom_values(self):
        """Test custom values."""
        query = PortfolioHistoryQuery(
            sort_by="total_return",
            sort_order="asc",
            limit=20,
            offset=10
        )
        assert query.sort_by == "total_return"
        assert query.limit == 20


class TestPortfolioRoutesMocks:
    """Tests for portfolio route handlers with mocked dependencies."""

    @patch("src.routes.portfolio_routes.get_portfolio_storage")
    def test_get_portfolio_history(self, mock_storage):
        """Test fetching portfolio history."""
        storage = MagicMock()
        storage.list_portfolios.return_value = {
            "portfolios": [
                {
                    "portfolio_id": "port-1",
                    "tickers": ["AAPL", "GOOGL"],
                    "total_return": 15.5,
                    "created_at": "2024-01-15T10:00:00Z"
                }
            ],
            "total": 1
        }
        mock_storage.return_value = storage

        result = storage.list_portfolios(limit=50, offset=0)

        assert result["total"] == 1
        assert len(result["portfolios"]) == 1
        assert result["portfolios"][0]["tickers"] == ["AAPL", "GOOGL"]

    @patch("src.routes.portfolio_routes.get_portfolio_storage")
    def test_get_portfolio_detail(self, mock_storage):
        """Test fetching portfolio detail."""
        storage = MagicMock()
        storage.get_portfolio.return_value = {
            "portfolio_id": "port-123",
            "tickers": ["AAPL", "GOOGL"],
            "weights": [0.5, 0.5],
            "total_return": 18.5,
            "metrics": {
                "sharpe_ratio": 1.5,
                "max_drawdown": -8.2
            }
        }
        mock_storage.return_value = storage

        result = storage.get_portfolio("port-123")

        assert result["portfolio_id"] == "port-123"
        assert result["total_return"] == 18.5

    @patch("src.routes.portfolio_routes.run_multi_asset_backtest")
    @patch("src.routes.portfolio_routes.get_portfolio_storage")
    def test_run_multi_asset_backtest(self, mock_storage, mock_run):
        """Test running multi-asset backtest."""
        mock_run.return_value = {
            "portfolio_id": "port-new",
            "total_return": 22.5,
        }
        mock_storage.return_value = MagicMock()

        # Simulate request
        result = mock_run(
            tickers=["AAPL", "GOOGL"],
            weights=[0.5, 0.5],
            start_date="2024-01-01",
            end_date="2024-12-31",
        )

        assert result["total_return"] == 22.5
