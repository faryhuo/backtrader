import types

import pytest

from src.service import live_engine
from src.service.live_engine import LiveTradingError


def test_live_trading_error():
    """Test LiveTradingError can be raised with message."""
    with pytest.raises(LiveTradingError, match="test error"):
        raise LiveTradingError("test error")


def test_get_storage_returns_session_storage(monkeypatch):
    """Test lazy storage initialisation."""
    # Reset module-level cache
    monkeypatch.setattr(live_engine, "_session_storage", None)

    from src.config.settings import ensure_database_dir
    storage = live_engine._get_storage()
    assert storage is not None
    # Second call should return same instance
    assert live_engine._get_storage() is storage


def test_start_session_rejects_missing_strategy(monkeypatch):
    """start_session should raise LiveTradingError for unknown strategy."""
    class StubSessionManager:
        def create_session(self, **kwargs):
            return types.SimpleNamespace(
                session_id=kwargs["session_id"],
                status="starting",
                cerebro=None,
                store=None,
                thread=None,
            )

        def remove_session(self, sid):
            pass  # cleanup stub

    broker_cfg = types.SimpleNamespace(
        risk_management=types.SimpleNamespace(
            position_limits=types.SimpleNamespace(
                max_position_size_usd=5000, max_positions_count=5
            ),
            order_limits=types.SimpleNamespace(
                min_order_size_usd=10, max_order_size_usd=5000
            ),
        )
    )

    monkeypatch.setattr(live_engine, "get_session_manager", lambda: StubSessionManager())
    monkeypatch.setattr(live_engine, "load_broker_config", lambda: broker_cfg)
    monkeypatch.setattr(live_engine, "get_risk_config", lambda cfg: cfg.risk_management)
    monkeypatch.setattr(live_engine, "get_exchange_config", lambda ex, cfg: types.SimpleNamespace(
        ccxt_id="binance",
    ))

    # load_user_strategy raises FileNotFoundError for unknown strategy
    def raise_not_found(name):
        raise FileNotFoundError(f"Strategy '{name}' not found")

    monkeypatch.setattr(live_engine, "load_user_strategy", raise_not_found)

    with pytest.raises(LiveTradingError, match="Failed to start session"):
        live_engine.start_session(
            strategy_name="nonexistent_strategy",
            symbol="BTC/USDT",
            mode="paper",
        )


def test_safe_returns_stop_handles_zero_division(monkeypatch):
    """SafeReturns.stop should handle ZeroDivisionError gracefully."""
    from src.service.analyzer_config import SafeReturns
    import backtrader as bt

    def raise_zero(self):
        raise ZeroDivisionError()

    monkeypatch.setattr(bt.analyzers.Returns, "stop", raise_zero)
    analyzer = object.__new__(SafeReturns)
    analyzer.rets = {}
    SafeReturns.stop(analyzer)
    assert analyzer.rets["rnorm100"] == pytest.approx(0.0)
