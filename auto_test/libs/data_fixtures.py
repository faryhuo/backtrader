"""
Test Data Fixtures and Factories

Provides reusable test data generators for:
- Strategy code templates
- Backtest configurations
- Market data
- User data
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class DataFixtures:
    """Test data generator for common test scenarios."""

    @staticmethod
    def simple_strategy_code(strategy_name: str = "TestStrategy") -> str:
        """
        Generate a simple valid strategy code.

        Args:
            strategy_name: Name of the strategy class

        Returns:
            Python code as string
        """
        return f'''import backtrader as bt

class {strategy_name}(bt.Strategy):
    """Simple test strategy."""
    
    params = (
        ('period', 20),
        ('threshold', 0.02),
    )
    
    def __init__(self):
        self.sma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.period
        )
    
    def next(self):
        if not self.position:
            if self.data.close[0] > self.sma[0] * (1 + self.params.threshold):
                self.buy()
        else:
            if self.data.close[0] < self.sma[0] * (1 - self.params.threshold):
                self.sell()
'''

    @staticmethod
    def invalid_strategy_code() -> str:
        """Generate invalid strategy code for error testing."""
        return '''import backtrader as bt

class BrokenStrategy(bt.Strategy):
    def __init__(self):
        # This will cause a syntax error
        self.value = 
'''

    @staticmethod
    def strategy_with_params() -> str:
        """Generate strategy with multiple parameters."""
        return '''import backtrader as bt

class ParamStrategy(bt.Strategy):
    params = (
        ('fast_period', 10),
        ('slow_period', 30),
        ('stop_loss', 0.05),
        ('take_profit', 0.10),
        ('max_positions', 3),
    )
    
    def __init__(self):
        self.fast_ma = bt.indicators.SMA(self.data.close, period=self.params.fast_period)
        self.slow_ma = bt.indicators.SMA(self.data.close, period=self.params.slow_period)
    
    def next(self):
        if self.fast_ma[0] > self.slow_ma[0]:
            if not self.position:
                self.buy()
        elif self.fast_ma[0] < self.slow_ma[0]:
            if self.position:
                self.sell()
'''

    @staticmethod
    def backtest_config(
        ticker: str = "AAPL",
        days_back: int = 365,
        initial_cash: float = 10000.0,
        commission: float = 0.001,
        strategy_name: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate backtest configuration.

        Args:
            ticker: Stock ticker symbol
            days_back: Number of days to backtest
            initial_cash: Initial cash amount
            commission: Commission rate
            strategy_name: Strategy name
            params: Strategy parameters

        Returns:
            Backtest configuration dictionary
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        config = {
            "ticker": ticker,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "initial_cash": initial_cash,
            "commission": commission,
            "stake": 100,
        }
        
        if strategy_name:
            config["strategy_name"] = strategy_name
        
        if params:
            config["params"] = params
        
        return config

    @staticmethod
    def portfolio_config(
        tickers: Optional[List[str]] = None,
        weights: Optional[List[float]] = None,
        days_back: int = 365,
        initial_cash: float = 100000.0,
        strategy_name: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate portfolio backtest configuration.

        Args:
            tickers: List of ticker symbols
            weights: Portfolio weights (normalized to sum to 1)
            days_back: Number of days to backtest
            initial_cash: Initial cash amount
            strategy_name: Optional strategy name
            params: Optional strategy parameters

        Returns:
            Portfolio configuration dictionary
        """
        if tickers is None:
            tickers = ["AAPL", "MSFT", "GOOGL"]

        if weights is None:
            # Equal weights by default
            weights = [1.0 / len(tickers)] * len(tickers)

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        config = {
            "tickers": tickers,
            "weights": weights,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "initial_cash": initial_cash,
            "commission": 0.0005,
            "stake": 100,
        }

        if strategy_name:
            config["strategy_name"] = strategy_name

        if params:
            config["params"] = params

        return config

    @staticmethod
    def walkforward_config(
        ticker: str = "AAPL",
        strategy_name: str = "TestStrategy",
        days_back: int = 730,
    ) -> Dict[str, Any]:
        """
        Generate walk-forward optimization configuration.

        Args:
            ticker: Stock ticker symbol
            strategy_name: Strategy name
            days_back: Number of days of data to use

        Returns:
            Walk-forward configuration dictionary
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        return {
            "ticker": ticker,
            "strategy_name": strategy_name,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "initial_cash": 100000.0,
            "commission": 0.0005,
            "stake": 100,
            "param_grid": {
                "period": [10, 20, 30],
            },
            "train_period_days": 365,
            "test_period_days": 90,
            "anchored": False,
            "optimization_metric": "sharpe_ratio",
        }

    @staticmethod
    def live_trading_config(
        strategy_name: str = "TestStrategy",
        symbol: str = "BTC/USDT",
        exchange: str = "binance",
        mode: str = "paper",
    ) -> Dict[str, Any]:
        """
        Generate live trading configuration.

        Args:
            strategy_name: Strategy name
            symbol: Trading pair symbol
            exchange: Exchange name
            mode: Trading mode (paper or live)

        Returns:
            Live trading configuration dictionary
        """
        return {
            "strategy_name": strategy_name,
            "symbol": symbol,
            "exchange": exchange,
            "mode": mode,
            "timeframe": "1m",
            "initial_cash": 10000.0,
            "commission": 0.001,
        }

    @staticmethod
    def mock_user_data(user_id: str = "test_user_123") -> Dict[str, Any]:
        """
        Generate mock user data.

        Args:
            user_id: User ID

        Returns:
            User data dictionary
        """
        return {
            "sub": user_id,
            "username": f"user_{user_id}",
            "email": f"test_{user_id}@example.com",
        }

    @staticmethod
    def mock_backtest_metrics() -> Dict[str, Any]:
        """
        Generate mock backtest metrics for testing.

        Returns:
            Metrics dictionary
        """
        return {
            "total_return": 15.5,
            "sharpe_ratio": 1.35,
            "max_drawdown": -8.2,
            "total_trades": 42,
            "win_rate": 58.5,
            "profit_factor": 1.45,
            "annual_return": 12.3,
            "volatility": 9.1,
        }

    @staticmethod
    def ticker_list() -> List[str]:
        """Get list of common test tickers."""
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA"]

    @staticmethod
    def date_range(days_back: int = 365) -> tuple[str, str]:
        """
        Get date range for testing.

        Args:
            days_back: Number of days back from today

        Returns:
            Tuple of (start_date, end_date) as strings
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        return (
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
        )

    @staticmethod
    def settings_config(
        selected_models: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate user settings configuration.

        Args:
            selected_models: List of AI model names

        Returns:
            Settings configuration dictionary
        """
        if selected_models is None:
            selected_models = ["gpt-4o", "gpt-4o-mini"]

        return {
            "selected_models": selected_models,
            "code_analysis_prompt": "Analyze this trading strategy code and provide insights.",
            "code_rewrite_prompt": "Rewrite this code to improve performance.",
            "full_strategy_analysis_prompt": "Provide a comprehensive analysis of the strategy.",
        }

    @staticmethod
    def data_source_config(
        priority: Optional[List[str]] = None,
        eodhd_api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate data source configuration.

        Args:
            priority: List of data sources in priority order
            eodhd_api_key: Optional EODHD API key

        Returns:
            Data source configuration dictionary
        """
        config = {}
        if priority is not None:
            config["data_source_priority"] = priority
        if eodhd_api_key is not None:
            config["eodhd_api_key"] = eodhd_api_key
        return config

    @staticmethod
    def market_data_request(
        ticker: str = "AAPL",
        days_back: int = 30,
    ) -> Dict[str, Any]:
        """
        Generate market data request configuration.

        Args:
            ticker: Stock ticker symbol
            days_back: Number of days to fetch

        Returns:
            Market data request dictionary
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        return {
            "ticker": ticker,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }

    @staticmethod
    def resample_request(
        ticker: str = "AAPL",
        target_timeframe: str = "1d",
        days_back: int = 30,
    ) -> Dict[str, Any]:
        """
        Generate resample request configuration.

        Args:
            ticker: Stock ticker symbol
            target_timeframe: Target timeframe for resampling
            days_back: Number of days to fetch

        Returns:
            Resample request dictionary
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        return {
            "ticker": ticker,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "target_timeframe": target_timeframe,
            "include_incomplete": False,
        }

    @staticmethod
    def warmup_request(
        tickers: Optional[List[str]] = None,
        days_back: int = 30,
    ) -> Dict[str, Any]:
        """
        Generate cache warmup request configuration.

        Args:
            tickers: List of tickers to warmup
            days_back: Number of days to fetch

        Returns:
            Warmup request dictionary
        """
        if tickers is None:
            tickers = ["AAPL", "MSFT"]

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        return {
            "tickers": tickers,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }
