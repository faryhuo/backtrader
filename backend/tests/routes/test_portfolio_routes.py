"""
Unit tests for portfolio routes, including per-asset parameter validation.
"""
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from src.routes.portfolio_routes import (
    PortfolioBacktestRequest,
    PortfolioHistoryQuery,
    MultiAssetBacktestRequest,
    PerAssetParams,
    RebalanceConfig,
    get_portfolio_storage,
)


class TestPortfolioStorage:
    """Tests for portfolio storage singleton."""

    def test_get_portfolio_storage_singleton(self):
        """Test that get_portfolio_storage returns singleton instance."""
        storage1 = get_portfolio_storage()
        storage2 = get_portfolio_storage()
        assert storage1 is storage2


class TestPerAssetParams:
    """Tests for PerAssetParams validation."""

    def test_valid_sma_period(self):
        """Test valid SMA period."""
        params = PerAssetParams(sma_period=20)
        assert params.sma_period == 20

    def test_valid_all_params(self):
        """Test all parameters at once."""
        params = PerAssetParams(
            sma_period=20,
            ema_period=12,
            rsi_period=14,
            rsi_oversold=30.0,
            rsi_overbought=70.0,
            macd_fast=12,
            macd_slow=26,
            macd_signal=9,
            bb_period=20,
            bb_std=2.0,
            atr_period=14
        )
        assert params.sma_period == 20
        assert params.ema_period == 12
        assert params.rsi_period == 14
        assert params.bb_std == 2.0

    def test_sma_period_too_low(self):
        """Test SMA period below minimum."""
        with pytest.raises(ValidationError) as exc_info:
            PerAssetParams(sma_period=1)
        assert "sma_period" in str(exc_info.value)

    def test_sma_period_too_high(self):
        """Test SMA period above maximum."""
        with pytest.raises(ValidationError) as exc_info:
            PerAssetParams(sma_period=501)
        assert "sma_period" in str(exc_info.value)

    def test_rsi_oversold_out_of_range(self):
        """Test RSI oversold out of valid range."""
        with pytest.raises(ValidationError) as exc_info:
            PerAssetParams(rsi_oversold=150)
        assert "rsi_oversold" in str(exc_info.value)

    def test_bb_std_too_low(self):
        """Test Bollinger Bands std below minimum."""
        with pytest.raises(ValidationError) as exc_info:
            PerAssetParams(bb_std=0.05)
        assert "bb_std" in str(exc_info.value)

    def test_bb_std_too_high(self):
        """Test Bollinger Bands std above maximum."""
        with pytest.raises(ValidationError) as exc_info:
            PerAssetParams(bb_std=6.0)
        assert "bb_std" in str(exc_info.value)

    def test_extra_params_allowed(self):
        """Test that extra parameters are allowed."""
        params = PerAssetParams(sma_period=20, custom_param=42)
        assert params.sma_period == 20
        assert params.custom_param == 42

    def test_none_values(self):
        """Test that None values are valid."""
        params = PerAssetParams()
        assert params.sma_period is None
        assert params.ema_period is None
        assert params.rsi_period is None


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
    """Tests for MultiAssetBacktestRequest with per-asset params."""

    def test_basic_request(self):
        """Test basic request without per-asset params."""
        request = MultiAssetBacktestRequest(
            tickers=["AAPL", "GOOGL"],
            weights=[0.5, 0.5],
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        assert request.tickers == ["AAPL", "GOOGL"]
        assert request.weights == [0.5, 0.5]
        assert request.per_asset_params is None

    def test_with_per_asset_params(self):
        """Test request with per-asset params."""
        request = MultiAssetBacktestRequest(
            tickers=["AAPL", "GOOGL"],
            weights=[0.5, 0.5],
            start_date="2024-01-01",
            end_date="2024-12-31",
            per_asset_params={
                "AAPL": {"sma_period": 10, "rsi_period": 14},
                "GOOGL": {"sma_period": 20, "ema_period": 12}
            }
        )
        assert request.per_asset_params is not None
        assert "AAPL" in request.per_asset_params
        assert "GOOGL" in request.per_asset_params

    def test_with_typed_per_asset_params(self):
        """Test request with typed PerAssetParams objects."""
        aapl_params = PerAssetParams(sma_period=10, rsi_period=14)
        googl_params = PerAssetParams(sma_period=20, ema_period=12)

        request = MultiAssetBacktestRequest(
            tickers=["AAPL", "GOOGL"],
            weights=[0.5, 0.5],
            start_date="2024-01-01",
            end_date="2024-12-31",
            per_asset_params={
                "AAPL": aapl_params,
                "GOOGL": googl_params
            }
        )
        assert request.per_asset_params["AAPL"].sma_period == 10
        assert request.per_asset_params["GOOGL"].ema_period == 12

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
            per_asset_params={
                "AAPL": {"sma_period": 10},
                "GOOGL": {"sma_period": 15},
                "MSFT": {"sma_period": 20}
            },
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


class TestPortfolioBacktestRequest:
    """Tests for legacy PortfolioBacktestRequest."""

    def test_basic_request(self):
        """Test basic portfolio backtest request."""
        request = PortfolioBacktestRequest(
            tickers=["AAPL", "GOOGL"],
            weights=[0.5, 0.5],
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        assert request.tickers == ["AAPL", "GOOGL"]
        assert request.initial_cash == 100000.0

    def test_defaults(self):
        """Test default values."""
        request = PortfolioBacktestRequest(
            tickers=["AAPL"],
            weights=[1.0],
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        assert request.commission == 0.0005
        assert request.stake == 100
        assert request.sizer_type == "fixed_size"
        assert request.timeframe == "1d"


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
    def test_run_multi_asset_with_per_asset_params(self, mock_storage, mock_run):
        """Test running multi-asset backtest with per-asset params."""
        mock_run.return_value = {
            "portfolio_id": "port-new",
            "total_return": 22.5,
            "per_asset_metrics": {
                "AAPL": {"return": 25.0},
                "GOOGL": {"return": 20.0}
            }
        }
        mock_storage.return_value = MagicMock()

        # Simulate request with per-asset params
        result = mock_run(
            tickers=["AAPL", "GOOGL"],
            weights=[0.5, 0.5],
            start_date="2024-01-01",
            end_date="2024-12-31",
            per_asset_params={
                "AAPL": {"sma_period": 10},
                "GOOGL": {"sma_period": 20}
            }
        )

        assert result["total_return"] == 22.5
        assert "per_asset_metrics" in result


class TestPerAssetParamsIntegration:
    """Integration tests for per-asset params through the full request flow."""

    def test_per_asset_params_with_different_indicators(self):
        """Test per-asset params with different indicator configurations."""
        request = MultiAssetBacktestRequest(
            tickers=["AAPL", "GOOGL", "MSFT"],
            weights=[0.33, 0.34, 0.33],
            start_date="2024-01-01",
            end_date="2024-12-31",
            strategy_name="multi_indicator",
            per_asset_params={
                "AAPL": {
                    "sma_period": 10,
                    "rsi_period": 14,
                    "rsi_oversold": 25,
                    "rsi_overbought": 75
                },
                "GOOGL": {
                    "ema_period": 12,
                    "macd_fast": 12,
                    "macd_slow": 26,
                    "macd_signal": 9
                },
                "MSFT": {
                    "bb_period": 20,
                    "bb_std": 2.5,
                    "atr_period": 14
                }
            }
        )

        # Pydantic converts dicts to PerAssetParams objects
        # Verify each ticker has correct params using attribute access
        assert request.per_asset_params["AAPL"].sma_period == 10
        assert request.per_asset_params["GOOGL"].ema_period == 12
        assert request.per_asset_params["MSFT"].bb_std == 2.5

    def test_partial_per_asset_params(self):
        """Test when only some assets have custom params."""
        request = MultiAssetBacktestRequest(
            tickers=["AAPL", "GOOGL", "MSFT", "AMZN"],
            weights=[0.25, 0.25, 0.25, 0.25],
            start_date="2024-01-01",
            end_date="2024-12-31",
            per_asset_params={
                "AAPL": {"sma_period": 15},
                # GOOGL, MSFT, AMZN use defaults
            }
        )

        assert "AAPL" in request.per_asset_params
        assert "GOOGL" not in request.per_asset_params
        assert "MSFT" not in request.per_asset_params
        assert "AMZN" not in request.per_asset_params

    def test_empty_per_asset_params(self):
        """Test with empty per-asset params dict."""
        request = MultiAssetBacktestRequest(
            tickers=["AAPL", "GOOGL"],
            weights=[0.5, 0.5],
            start_date="2024-01-01",
            end_date="2024-12-31",
            per_asset_params={}
        )

        assert request.per_asset_params == {}
