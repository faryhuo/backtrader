import backtrader as bt
import pytest

from src.service import backtest_engine


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
    monkeypatch.setattr(backtest_engine, "STRATEGY_DIR", tmp_path)
    monkeypatch.setattr(backtest_engine, "ensure_resource_files", lambda: None)

    code = "import backtrader as bt\n\nclass UserStrategy(bt.Strategy):\n    pass\n"
    backtest_engine.save_user_strategy_code("my_strategy", code)
    assert backtest_engine.get_user_strategy_code("my_strategy") == code
    assert "my_strategy" in backtest_engine.list_strategies()


def test_load_user_strategy_from_sandbox(tmp_path, monkeypatch):
    monkeypatch.setattr(backtest_engine, "STRATEGY_DIR", tmp_path)
    monkeypatch.setattr(backtest_engine, "ensure_resource_files", lambda: None)

    code = "import backtrader as bt\n\nclass UserStrategy(bt.Strategy):\n    pass\n"
    backtest_engine.save_user_strategy_code("ok", code)

    cls = backtest_engine.load_user_strategy("ok")
    assert issubclass(cls, bt.Strategy)

