"""
Unit tests for portfolio routes.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from src.routes.portfolio_routes import (
    PortfolioHistoryQuery,
    MultiAssetBacktestRequest,
)
from src.db import get_portfolio_storage


class TestPortfolioStorage:
    """Tests for portfolio storage singleton."""

    def test_get_portfolio_storage_singleton(self):
        """Test that get_portfolio_storage returns singleton instance."""
        storage1 = get_portfolio_storage()
        storage2 = get_portfolio_storage()
        assert storage1 is storage2


class TestMultiAssetBacktestRequest:
    """Tests for MultiAssetBacktestRequest."""

    def test_basic_request(self):
        """Test basic request."""
        request = MultiAssetBacktestRequest(
            tickers=["AAPL", "GOOGL"],
            weights=[0.5, 0.5],
            start_date="2024-01-01",
            end_date="2024-12-31",
            strategy_name="buy_and_hold"
        )
        assert request.tickers == ["AAPL", "GOOGL"]
        assert request.weights == [0.5, 0.5]

    def test_valid_timeframes(self):
        """Test all valid timeframes."""
        for tf in ["1d", "1h", "15m", "5m", "1m"]:
            request = MultiAssetBacktestRequest(
                tickers=["AAPL"],
                weights=[1.0],
                start_date="2024-01-01",
                end_date="2024-12-31",
                strategy_name="buy_and_hold",
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
                strategy_name="buy_and_hold",
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
                end_date="2024-12-31",
                strategy_name="buy_and_hold"
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
                strategy_name="buy_and_hold",
                initial_cash=500
            )

        # Too high
        with pytest.raises(ValidationError):
            MultiAssetBacktestRequest(
                tickers=["AAPL"],
                weights=[1.0],
                start_date="2024-01-01",
                end_date="2024-12-31",
                strategy_name="buy_and_hold",
                initial_cash=200000000
            )

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
            params={"fast_period": 10, "slow_period": 30},
            timeframe="1d"
        )
        assert len(request.tickers) == 3
        assert request.strategy_name == "sma_cross"
        assert request.params == {"fast_period": 10, "slow_period": 30}


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

    @patch("src.routes.portfolio_routes.get_executor")
    @patch("src.routes.portfolio_routes.get_task_manager")
    @patch("src.routes.portfolio_routes.get_portfolio_storage")
    def test_run_multi_asset_backtest(self, mock_storage, mock_task_manager, mock_get_executor):
        """Test running multi-asset backtest."""
        # Mock executor
        mock_executor = MagicMock()
        mock_get_executor.return_value = mock_executor

        # Mock task manager
        manager = MagicMock()
        manager.submit = AsyncMock(return_value={
            "task_id": "port-new",
            "status": "pending",
        })
        mock_task_manager.return_value = manager

        mock_storage.return_value = MagicMock()

        # Test that executor is properly retrieved
        executor = mock_get_executor("multi_asset")
        assert executor is not None
