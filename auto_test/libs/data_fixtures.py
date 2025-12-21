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
        days_back: int = 365,
        initial_cash: float = 100000.0,
    ) -> Dict[str, Any]:
        """
        Generate portfolio backtest configuration.

        Args:
            tickers: List of ticker symbols
            days_back: Number of days to backtest
            initial_cash: Initial cash amount

        Returns:
            Portfolio configuration dictionary
        """
        if tickers is None:
            tickers = ["AAPL", "MSFT", "GOOGL"]
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        return {
            "tickers": tickers,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "initial_cash": initial_cash,
            "commission": 0.001,
        }

    @staticmethod
    def walkforward_config(
        ticker: str = "AAPL",
        strategy_name: str = "TestStrategy",
    ) -> Dict[str, Any]:
        """
        Generate walk-forward optimization configuration.

        Args:
            ticker: Stock ticker symbol
            strategy_name: Strategy name

        Returns:
            Walk-forward configuration dictionary
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)  # 2 years
        
        return {
            "ticker": ticker,
            "strategy_name": strategy_name,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "initial_cash": 10000.0,
            "commission": 0.001,
            "param_ranges": {
                "period": {"start": 10, "end": 50, "step": 10},
                "threshold": {"start": 0.01, "end": 0.05, "step": 0.01},
            },
            "train_period_days": 180,
            "test_period_days": 90,
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
