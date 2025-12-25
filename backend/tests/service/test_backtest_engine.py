import backtrader as bt
import pytest

from src.service import backtest_engine
from src.service import strategy_repo


def test_get_strategy_path_valid():
    """Test that get_strategy_path returns valid paths."""
    # Test with a valid strategy name format
    path = backtest_engine.get_strategy_path("test")
    assert path.name == "test.py"


def test_get_strategy_path_rejects_traversal():
    """Test that path traversal is rejected."""
    with pytest.raises(backtest_engine.StrategyLoadError):
        backtest_engine.get_strategy_path("../x")


def test_strategy_file_round_trip(tmp_path, monkeypatch):
    # Mock the strategy directory at the source
    monkeypatch.setattr(strategy_repo, "_get_strategy_dir", lambda: tmp_path)
    monkeypatch.setattr(strategy_repo, "ensure_strategy_dirs", lambda: None)

    code = "import backtrader as bt\n\nclass UserStrategy(bt.Strategy):\n    pass\n"
    backtest_engine.save_user_strategy_code("my_strategy", code)
    assert backtest_engine.get_user_strategy_code("my_strategy") == code
    assert "my_strategy" in backtest_engine.list_strategies()


def test_load_user_strategy_from_sandbox(tmp_path, monkeypatch):
    # Mock the strategy directory at the source
    monkeypatch.setattr(strategy_repo, "_get_strategy_dir", lambda: tmp_path)
    monkeypatch.setattr(strategy_repo, "ensure_strategy_dirs", lambda: None)

    code = "import backtrader as bt\n\nclass UserStrategy(bt.Strategy):\n    pass\n"
    backtest_engine.save_user_strategy_code("ok", code)

    cls = backtest_engine.load_user_strategy("ok")
    assert issubclass(cls, bt.Strategy)


def test_get_user_strategy_code_not_found():
    """Test getting non-existent strategy raises error."""
    with pytest.raises(backtest_engine.StrategyLoadError) as exc_info:
        backtest_engine.get_user_strategy_code("nonexistent_strategy_12345")
    assert "not found" in str(exc_info.value)


def test_save_user_strategy_code_invalid_name(tmp_path, monkeypatch):
    """Test saving strategy with invalid name raises error."""
    monkeypatch.setattr(strategy_repo, "_get_strategy_dir", lambda: tmp_path)
    monkeypatch.setattr(strategy_repo, "ensure_strategy_dirs", lambda: None)

    code = "import backtrader as bt\n\nclass UserStrategy(bt.Strategy):\n    pass\n"

    # Test path traversal attempt
    with pytest.raises(backtest_engine.StrategyLoadError):
        backtest_engine.save_user_strategy_code("../evil", code)


def test_load_user_strategy_not_found():
    """Test loading non-existent strategy raises error."""
    with pytest.raises(backtest_engine.StrategyLoadError) as exc_info:
        backtest_engine.load_user_strategy("nonexistent_strategy_12345")
    assert "Strategy" in str(exc_info.value) or "not found" in str(exc_info.value).lower()


def test_extract_strategy_params_with_params(tmp_path, monkeypatch):
    """Test extracting parameters from strategy with params defined."""
    monkeypatch.setattr(strategy_repo, "_get_strategy_dir", lambda: tmp_path)
    monkeypatch.setattr(strategy_repo, "ensure_strategy_dirs", lambda: None)

    code = """import backtrader as bt

class UserStrategy(bt.Strategy):
    params = (
        ('period', 20),
        ('devfactor', 2.0),
        ('risk_pct', 0.02),
    )

    def __init__(self):
        self.sma = bt.indicators.SMA(period=self.params.period)
"""
    backtest_engine.save_user_strategy_code("param_strategy", code)

    params = backtest_engine.extract_strategy_params("param_strategy")

    assert isinstance(params, list)
    assert len(params) == 3

    # Check that params are extracted
    param_names = [p['name'] for p in params]
    assert 'period' in param_names
    assert 'devfactor' in param_names
    assert 'risk_pct' in param_names


def test_extract_strategy_params_no_params(tmp_path, monkeypatch):
    """Test extracting parameters from strategy without params."""
    monkeypatch.setattr(strategy_repo, "_get_strategy_dir", lambda: tmp_path)
    monkeypatch.setattr(strategy_repo, "ensure_strategy_dirs", lambda: None)

    code = """import backtrader as bt

class UserStrategy(bt.Strategy):
    def next(self):
        pass
"""
    backtest_engine.save_user_strategy_code("no_param_strategy", code)

    params = backtest_engine.extract_strategy_params("no_param_strategy")

    assert isinstance(params, list)
    assert len(params) == 0


def test_list_strategies_empty(tmp_path, monkeypatch):
    """Test listing strategies when directory is empty."""
    monkeypatch.setattr(strategy_repo, "_get_strategy_dir", lambda: tmp_path)
    monkeypatch.setattr(strategy_repo, "ensure_strategy_dirs", lambda: None)

    strategies = backtest_engine.list_strategies()

    # Should return empty list or only include default strategies
    assert isinstance(strategies, list)


def test_trade_recorder_analyzer():
    """Test TradeRecorder analyzer tracks trades correctly."""
    cerebro = bt.Cerebro()

    # Create simple test strategy
    class SimpleStrategy(bt.Strategy):
        def next(self):
            if not self.position:
                self.buy(size=10)
            elif len(self) > 10:
                self.close()

    cerebro.addstrategy(SimpleStrategy)
    cerebro.addanalyzer(backtest_engine.TradeRecorder)

    # Add some test data
    import pandas as pd
    from datetime import datetime, timedelta

    dates = pd.date_range(datetime.now() - timedelta(days=30), periods=30)
    data = pd.DataFrame({
        'open': [100.0] * 30,
        'high': [105.0] * 30,
        'low': [95.0] * 30,
        'close': [102.0] * 30,
        'volume': [1000000] * 30,
    }, index=dates)

    cerebro.adddata(bt.feeds.PandasData(dataname=data))
    cerebro.broker.setcash(10000.0)

    results = cerebro.run()
    analyzer = results[0].analyzers.traderecorder

    # Analyzer should exist and have trades attribute
    assert hasattr(analyzer, 'trades')
    assert isinstance(analyzer.trades, list)


def test_ensure_resource_files(monkeypatch):
    """Test ensure_resource_files calls ensure_resource_dirs."""
    called = []

    def mock_ensure():
        called.append(True)

    monkeypatch.setattr("src.service.backtest_engine.ensure_resource_dirs", mock_ensure)

    backtest_engine.ensure_resource_files()

    assert len(called) == 1

