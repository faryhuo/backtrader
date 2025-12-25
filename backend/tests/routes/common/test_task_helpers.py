"""
Unit tests for task_helpers module.

Tests for common task management utilities including:
- User ID extraction
- Task name generation
- Task config creation
- Exception mapping to HTTP errors
"""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from pydantic import BaseModel

from src.contracts.exceptions import StrategyLoadError, DataLoadError
from src.routes.common.task_helpers import (
    get_user_id,
    generate_task_name,
    create_task_config,
    map_exception_to_http,
)


class TestGetUserId:
    """Tests for get_user_id function."""

    def test_get_user_id_with_valid_user(self):
        """Test extracting user ID from authenticated user dict."""
        user = {"sub": "user_123", "name": "Test User"}
        assert get_user_id(user) == "user_123"

    def test_get_user_id_with_none(self):
        """Test extracting user ID when user is None."""
        assert get_user_id(None) is None

    def test_get_user_id_with_empty_dict(self):
        """Test extracting user ID from empty user dict."""
        user = {}
        assert get_user_id(user) is None

    def test_get_user_id_with_missing_sub(self):
        """Test extracting user ID when 'sub' key is missing."""
        user = {"name": "Test User", "email": "test@example.com"}
        assert get_user_id(user) is None


class TestGenerateTaskName:
    """Tests for generate_task_name function."""

    def test_backtest_task_name(self):
        """Test generating name for backtest task."""
        config = {
            "ticker": "AAPL",
            "strategy_name": "SMA_Cross"
        }
        result = generate_task_name("backtest", config)
        assert result == "Backtest AAPL - SMA_Cross"

    def test_backtest_task_name_with_defaults(self):
        """Test backtest name with missing ticker/strategy."""
        config = {}
        result = generate_task_name("backtest", config)
        assert result == "Backtest Unknown - Default"

    def test_portfolio_task_name_empty(self):
        """Test portfolio name with empty tickers list."""
        config = {"tickers": []}
        result = generate_task_name("portfolio", config)
        assert result == "Portfolio Backtest"

    def test_portfolio_task_name_single_ticker(self):
        """Test portfolio name with single ticker."""
        config = {"tickers": ["AAPL"]}
        result = generate_task_name("portfolio", config)
        assert result == "Portfolio Backtest: AAPL"

    def test_portfolio_task_name_three_tickers(self):
        """Test portfolio name with three tickers."""
        config = {"tickers": ["AAPL", "MSFT", "GOOGL"]}
        result = generate_task_name("portfolio", config)
        assert result == "Portfolio Backtest: AAPL, MSFT, GOOGL"

    def test_portfolio_task_name_many_tickers(self):
        """Test portfolio name with more than 3 tickers shows +N."""
        config = {"tickers": ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]}
        result = generate_task_name("portfolio", config)
        assert result == "Portfolio Backtest: AAPL, MSFT, GOOGL +2"

    def test_walkforward_task_name(self):
        """Test generating name for walk-forward task."""
        config = {
            "strategy_name": "RSI_Strategy",
            "ticker": "SPY"
        }
        result = generate_task_name("walkforward", config)
        assert result == "Walk-Forward: RSI_Strategy on SPY"

    def test_walkforward_task_name_with_defaults(self):
        """Test walk-forward name with missing fields."""
        config = {}
        result = generate_task_name("walkforward", config)
        assert result == "Walk-Forward: Unknown on Unknown"

    def test_deep_analysis_task_name(self):
        """Test generating name for deep analysis task."""
        config = {"backtest_id": "bt_12345"}
        result = generate_task_name("deep_analysis", config)
        assert result == "Deep Analysis: bt_12345"

    def test_deep_analysis_task_name_with_default(self):
        """Test deep analysis name with missing backtest_id."""
        config = {}
        result = generate_task_name("deep_analysis", config)
        assert result == "Deep Analysis: Unknown"

    def test_unknown_task_type(self):
        """Test generating name for unknown task type."""
        config = {"some_field": "value"}
        result = generate_task_name("custom_task", config)
        assert result == "Task: custom_task"


class TestCreateTaskConfig:
    """Tests for create_task_config function."""

    def test_backtest_config_extraction(self):
        """Test extracting backtest config from request."""
        class BacktestRequest(BaseModel):
            ticker: str
            start_date: str
            end_date: str
            initial_cash: float
            commission: float
            stake: int
            strategy_name: str
            params: dict
            extra_field: str = "ignored"

        request = BacktestRequest(
            ticker="AAPL",
            start_date="2024-01-01",
            end_date="2024-12-31",
            initial_cash=100000.0,
            commission=0.001,
            stake=100,
            strategy_name="SMA",
            params={"period": 20},
            extra_field="should_not_appear"
        )

        config = create_task_config(request, "backtest")

        assert config["ticker"] == "AAPL"
        assert config["start_date"] == "2024-01-01"
        assert config["end_date"] == "2024-12-31"
        assert config["initial_cash"] == 100000.0
        assert config["commission"] == 0.001
        assert config["stake"] == 100
        assert config["strategy_name"] == "SMA"
        assert config["params"] == {"period": 20}
        assert "extra_field" not in config

    def test_portfolio_config_extraction(self):
        """Test extracting portfolio config from request."""
        class PortfolioRequest(BaseModel):
            tickers: list
            weights: list
            start_date: str
            end_date: str
            initial_cash: float
            commission: float
            stake: int
            strategy_name: str
            params: dict

        request = PortfolioRequest(
            tickers=["AAPL", "MSFT"],
            weights=[0.5, 0.5],
            start_date="2024-01-01",
            end_date="2024-12-31",
            initial_cash=100000.0,
            commission=0.001,
            stake=100,
            strategy_name="EqualWeight",
            params={}
        )

        config = create_task_config(request, "portfolio")

        assert config["tickers"] == ["AAPL", "MSFT"]
        assert config["weights"] == [0.5, 0.5]
        assert config["start_date"] == "2024-01-01"
        assert config["strategy_name"] == "EqualWeight"

    def test_walkforward_config_extraction(self):
        """Test extracting walk-forward config from request."""
        class WalkforwardRequest(BaseModel):
            strategy_name: str
            ticker: str
            start_date: str
            end_date: str
            param_grid: dict
            train_period_days: int
            test_period_days: int
            anchored: bool
            optimization_metric: str
            initial_cash: float
            commission: float
            stake: int

        request = WalkforwardRequest(
            strategy_name="RSI",
            ticker="SPY",
            start_date="2024-01-01",
            end_date="2024-12-31",
            param_grid={"period": [14, 21, 28]},
            train_period_days=180,
            test_period_days=30,
            anchored=False,
            optimization_metric="sharpe_ratio",
            initial_cash=100000.0,
            commission=0.001,
            stake=100
        )

        config = create_task_config(request, "walkforward")

        assert config["strategy_name"] == "RSI"
        assert config["ticker"] == "SPY"
        assert config["param_grid"] == {"period": [14, 21, 28]}
        assert config["train_period_days"] == 180
        assert config["test_period_days"] == 30
        assert config["anchored"] is False
        assert config["optimization_metric"] == "sharpe_ratio"

    def test_unknown_task_type_returns_all_fields(self):
        """Test that unknown task types return all fields."""
        class CustomRequest(BaseModel):
            field1: str
            field2: int
            field3: bool

        request = CustomRequest(
            field1="value1",
            field2=42,
            field3=True
        )

        config = create_task_config(request, "unknown_type")

        assert config["field1"] == "value1"
        assert config["field2"] == 42
        assert config["field3"] is True


class TestMapExceptionToHttp:
    """Tests for map_exception_to_http function."""

    def test_strategy_load_error_returns_400(self):
        """Test StrategyLoadError maps to 400 Bad Request."""
        exc = StrategyLoadError("Strategy file not found")
        http_exc = map_exception_to_http(exc)

        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 400
        assert http_exc.detail == "Strategy file not found"

    def test_data_load_error_returns_502(self):
        """Test DataLoadError maps to 502 Bad Gateway."""
        exc = DataLoadError("Failed to fetch data from Yahoo Finance")
        http_exc = map_exception_to_http(exc)

        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 502
        assert http_exc.detail == "Failed to fetch data from Yahoo Finance"

    def test_value_error_returns_400(self):
        """Test ValueError maps to 400 Bad Request."""
        exc = ValueError("Invalid parameter value")
        http_exc = map_exception_to_http(exc)

        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 400
        assert http_exc.detail == "Invalid parameter value"

    def test_file_not_found_error_returns_404(self):
        """Test FileNotFoundError maps to 404 Not Found."""
        exc = FileNotFoundError("File does not exist")
        http_exc = map_exception_to_http(exc)

        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 404
        assert http_exc.detail == "File does not exist"

    def test_http_exception_returns_as_is(self):
        """Test HTTPException is returned unchanged."""
        exc = HTTPException(status_code=403, detail="Forbidden")
        http_exc = map_exception_to_http(exc)

        assert http_exc is exc
        assert http_exc.status_code == 403
        assert http_exc.detail == "Forbidden"

    def test_unknown_exception_returns_500(self):
        """Test unknown exceptions map to 500 Internal Server Error."""
        exc = RuntimeError("Unexpected error occurred")
        http_exc = map_exception_to_http(exc)

        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 500
        assert http_exc.detail == "Unexpected error occurred"

    def test_exception_with_no_message_returns_500(self):
        """Test exception with no message still returns 500."""
        exc = Exception()
        http_exc = map_exception_to_http(exc)

        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 500
