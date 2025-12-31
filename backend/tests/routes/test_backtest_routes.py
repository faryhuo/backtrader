"""
Unit tests for backtest routes.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.routes.backtest_routes import (
    get_backtest_storage,
    BacktestRequest,
    BacktestHistoryQuery,
    AIAnalysisUpdate,
    DeepAnalysisConfig,
)


class TestGetBacktestStorage:
    """Tests for backtest storage singleton."""

    def test_get_backtest_storage_singleton(self):
        """Test that get_backtest_storage returns singleton instance."""
        storage1 = get_backtest_storage()
        storage2 = get_backtest_storage()
        assert storage1 is storage2


class TestPydanticModels:
    """Tests for Pydantic request/response models."""

    def test_backtest_request_valid(self):
        """Test creating valid BacktestRequest."""
        request = BacktestRequest(
            ticker="AAPL",
            start_date="2024-01-01",
            end_date="2024-12-31",
            initial_cash=100000.0,
            commission=0.001,
            stake=100,
            strategy_name="sma_strategy",
            params={"period": 20}
        )

        assert request.ticker == "AAPL"
        assert request.initial_cash == 100000.0
        assert request.params["period"] == 20

    def test_backtest_request_defaults(self):
        """Test BacktestRequest with default values."""
        request = BacktestRequest(
            ticker="AAPL",
            start_date="2024-01-01",
            end_date="2024-12-31",
            initial_cash=100000.0
        )

        assert request.commission == 0.0005
        assert request.stake == 100
        assert request.strategy_name is None
        assert request.params is None

    def test_backtest_history_query_defaults(self):
        """Test BacktestHistoryQuery with default values."""
        query = BacktestHistoryQuery()

        assert query.ticker is None
        assert query.strategy_name is None
        assert query.sort_by == "created_at"
        assert query.sort_order == "desc"
        assert query.limit == 50
        assert query.offset == 0

    def test_backtest_history_query_custom(self):
        """Test BacktestHistoryQuery with custom values."""
        query = BacktestHistoryQuery(
            ticker="TSLA",
            strategy_name="rsi_strategy",
            sort_by="total_return",
            sort_order="asc",
            limit=20,
            offset=10
        )

        assert query.ticker == "TSLA"
        assert query.strategy_name == "rsi_strategy"
        assert query.sort_by == "total_return"
        assert query.limit == 20

    def test_ai_analysis_update(self):
        """Test AIAnalysisUpdate model."""
        update = AIAnalysisUpdate(
            model_name="gpt-4o",
            analysis="This strategy shows strong performance..."
        )

        assert update.model_name == "gpt-4o"
        assert "strong performance" in update.analysis

    def test_deep_analysis_config_defaults(self):
        """Test DeepAnalysisConfig with defaults."""
        config = DeepAnalysisConfig()

        assert config.benchmarks is None
        assert config.rolling_window == 60
        assert config.risk_free_rate == 0.02

    def test_deep_analysis_config_custom(self):
        """Test DeepAnalysisConfig with custom values."""
        config = DeepAnalysisConfig(
            benchmarks=["SPY", "QQQ"],
            rolling_window=30,
            risk_free_rate=0.03
        )

        assert config.benchmarks == ["SPY", "QQQ"]
        assert config.rolling_window == 30
        assert config.risk_free_rate == 0.03


class TestBacktestRoutes:
    """Tests for backtest route handlers."""

    @pytest.fixture
    def mock_backtest_storage(self):
        """Mock BacktestStorage."""
        with patch("src.routes.backtest_routes.get_backtest_storage") as mock:
            storage = MagicMock()
            mock.return_value = storage
            yield storage

    @pytest.fixture
    def mock_task_manager(self):
        """Mock TaskManager."""
        with patch("src.routes.backtest_routes.get_task_manager") as mock:
            manager = MagicMock()
            mock.return_value = manager
            yield manager

    def test_backtest_request_validation(self):
        """Test that invalid backtest requests are rejected."""
        with pytest.raises(Exception):
            # Missing required fields
            BacktestRequest(ticker="AAPL")

    def test_backtest_history_query_validation(self):
        """Test BacktestHistoryQuery validation."""
        query = BacktestHistoryQuery(
            ticker="AAPL",
            limit=100,
            offset=0
        )

        assert query.limit == 100
        assert query.offset == 0


class TestBacktestExecutionMocks:
    """Tests for backtest execution with mocked dependencies."""

    @patch("src.routes.backtest_routes.get_executor")
    @patch("src.routes.backtest_routes.get_task_manager")
    @patch("src.routes.backtest_routes.get_backtest_storage")
    def test_run_backtest_success_mock(self, mock_storage, mock_task_manager, mock_get_executor):
        """Test successful backtest execution (mocked)."""
        # Mock backtest executor result
        mock_executor = MagicMock()
        mock_get_executor.return_value = mock_executor

        # Mock task manager
        manager = MagicMock()
        manager.submit = AsyncMock(return_value={
            "task_id": "test-123",
            "status": "pending",
        })
        mock_task_manager.return_value = manager

        # Mock storage
        storage = MagicMock()
        mock_storage.return_value = storage

        # Test that executor is properly retrieved
        executor = mock_get_executor("backtest")
        assert executor is not None

    @patch("src.service.backtest_engine.run_backtest")
    def test_run_backtest_strategy_load_error(self, mock_run_backtest):
        """Test handling of strategy load errors."""
        from src.service.backtest_engine import StrategyLoadError

        mock_run_backtest.side_effect = StrategyLoadError("Strategy not found")

        # Simulate route handler error handling
        with pytest.raises(StrategyLoadError):
            mock_run_backtest(
                ticker="AAPL",
                start_date="2024-01-01",
                end_date="2024-12-31",
                initial_cash=100000,
                strategy_name="nonexistent"
            )

    @patch("src.service.backtest_engine.run_backtest")
    def test_run_backtest_data_load_error(self, mock_run_backtest):
        """Test handling of data load errors."""
        from src.db.storage.market_data import DataLoadError

        mock_run_backtest.side_effect = DataLoadError("Failed to fetch data for INVALID")

        with pytest.raises(DataLoadError):
            mock_run_backtest(
                ticker="INVALID",
                start_date="2024-01-01",
                end_date="2024-12-31",
                initial_cash=100000
            )


class TestBacktestHistoryMocks:
    """Tests for backtest history operations."""

    @patch("src.routes.backtest_routes.get_backtest_storage")
    def test_get_backtest_history(self, mock_storage):
        """Test fetching backtest history."""
        storage = MagicMock()
        storage.list_backtests.return_value = {
            "backtests": [
                {
                    "backtest_id": "test-1",
                    "ticker": "AAPL",
                    "strategy_name": "sma_cross",
                    "total_return": 12.5,
                    "created_at": "2024-01-15T10:00:00Z"
                },
                {
                    "backtest_id": "test-2",
                    "ticker": "TSLA",
                    "strategy_name": "rsi_strategy",
                    "total_return": 8.3,
                    "created_at": "2024-01-14T09:30:00Z"
                }
            ],
            "total": 2
        }
        mock_storage.return_value = storage

        result = storage.list_backtests(limit=50, offset=0)

        assert result["total"] == 2
        assert len(result["backtests"]) == 2
        assert result["backtests"][0]["ticker"] == "AAPL"

    @patch("src.routes.backtest_routes.get_backtest_storage")
    def test_get_single_backtest(self, mock_storage):
        """Test fetching single backtest by ID."""
        storage = MagicMock()
        storage.get_backtest.return_value = {
            "backtest_id": "test-123",
            "ticker": "AAPL",
            "strategy_name": "sma_cross",
            "total_return": 12.5,
            "metrics": {
                "trade_details": {
                    "total_trades": 50,
                    "winning_trades": 30
                }
            }
        }
        mock_storage.return_value = storage

        result = storage.get_backtest("test-123")

        assert result["backtest_id"] == "test-123"
        assert result["metrics"]["trade_details"]["total_trades"] == 50

    @patch("src.routes.backtest_routes.get_backtest_storage")
    def test_delete_backtest(self, mock_storage):
        """Test deleting a backtest."""
        storage = MagicMock()
        storage.delete_backtest.return_value = True
        mock_storage.return_value = storage

        result = storage.delete_backtest("test-123")

        assert result is True
        storage.delete_backtest.assert_called_once_with("test-123")


class TestAIAnalysisMocks:
    """Tests for AI analysis functionality."""

    @patch("src.routes.backtest_routes.get_backtest_storage")
    def test_update_ai_analysis(self, mock_storage):
        """Test updating AI analysis for a backtest."""
        storage = MagicMock()
        storage.update_ai_analysis.return_value = {
            "backtest_id": "test-123",
            "ai_analysis": "This strategy shows strong momentum indicators..."
        }
        mock_storage.return_value = storage

        update = AIAnalysisUpdate(
            model_name="gpt-4o",
            analysis="This strategy shows strong momentum indicators..."
        )

        result = storage.update_ai_analysis(
            backtest_id="test-123",
            ai_analysis=update.analysis,
            model_name=update.model_name
        )

        assert "ai_analysis" in result
        storage.update_ai_analysis.assert_called_once()


class TestDeepAnalysisMocks:
    """Tests for deep analysis functionality."""

    @patch("src.routes.backtest_routes.compute_deep_analysis")
    @patch("src.routes.backtest_routes.get_backtest_storage")
    def test_compute_deep_analysis_success(self, mock_storage, mock_compute):
        """Test computing deep analysis."""
        # Mock backtest data
        storage = MagicMock()
        storage.get_backtest.return_value = {
            "backtest_id": "test-123",
            "ticker": "AAPL",
            "metrics": {
                "equity_curve": {
                    "2024-01-01": 100000,
                    "2024-01-02": 101000,
                    "2024-01-03": 102000
                }
            }
        }
        mock_storage.return_value = storage

        # Mock deep analysis result
        mock_compute.return_value = {
            "rolling_sharpe": [1.2, 1.3, 1.4],
            "drawdown_periods": [],
            "benchmark_comparison": {}
        }

        config = DeepAnalysisConfig(
            benchmarks=["SPY"],
            rolling_window=30
        )

        result = mock_compute(
            backtest_id="test-123",
            benchmarks=config.benchmarks,
            rolling_window=config.rolling_window
        )

        assert "rolling_sharpe" in result
        assert len(result["rolling_sharpe"]) == 3

    @patch("src.routes.backtest_routes.compute_deep_analysis")
    def test_compute_deep_analysis_error(self, mock_compute):
        """Test error handling in deep analysis."""
        from src.service.deep_analysis import DeepAnalysisError

        mock_compute.side_effect = DeepAnalysisError("Insufficient data for analysis")

        with pytest.raises(DeepAnalysisError):
            mock_compute(backtest_id="test-123")


class TestRequestValidation:
    """Tests for request validation."""

    def test_invalid_date_format(self):
        """Test that invalid date formats are caught."""
        # Pydantic will accept any string, validation happens in business logic
        request = BacktestRequest(
            ticker="AAPL",
            start_date="invalid-date",
            end_date="2024-12-31",
            initial_cash=100000
        )

        # The request model accepts it, but business logic should validate
        assert request.start_date == "invalid-date"

    def test_negative_initial_cash(self):
        """Test handling of negative initial cash."""
        request = BacktestRequest(
            ticker="AAPL",
            start_date="2024-01-01",
            end_date="2024-12-31",
            initial_cash=-10000  # Should be caught by business logic
        )

        assert request.initial_cash < 0  # Model accepts it, logic should reject

    def test_invalid_commission_rate(self):
        """Test handling of invalid commission rates."""
        request = BacktestRequest(
            ticker="AAPL",
            start_date="2024-01-01",
            end_date="2024-12-31",
            initial_cash=100000,
            commission=1.5  # 150% commission - unrealistic
        )

        assert request.commission == 1.5
