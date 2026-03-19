import types

import backtrader as bt
import pytest

from src.service import live_engine
from src.service.live_engine import LiveTradingError
from src.service.live_strategy_bridge import wrap_strategy_with_live_gate
from src.db.storage.session import SessionStorage


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


def test_wrapped_strategy_skips_next_until_live():
    calls = []

    class BaseStrategy(bt.Strategy):
        def next(self):
            calls.append("next")

    class DummyDateTime:
        def datetime(self, index=0):
            return "2024-01-01T00:00:00"

    class DummyData:
        def __init__(self):
            self.close = [100.0]
            self.datetime = DummyDateTime()

        def __len__(self):
            return 1

    wrapped = wrap_strategy_with_live_gate(BaseStrategy, lambda *_args: None)
    wrapped.position = property(lambda self: types.SimpleNamespace(size=0))
    strategy = object.__new__(wrapped)
    strategy.__dict__["_log_cb"] = lambda *_args: None
    strategy.__dict__["_data_live"] = False
    strategy.datas = [DummyData()]

    wrapped.next(strategy)
    assert calls == []

    strategy.__dict__["_data_live"] = True
    wrapped.next(strategy)
    assert calls == ["next"]


def test_wrapped_strategy_emits_feed_status_callback():
    statuses = []

    class BaseStrategy(bt.Strategy):
        pass

    class DummyData:
        LIVE = 1
        DELAYED = 2
        _symbol = "BTC/USDT"

        @staticmethod
        def _getstatusname(status):
            return {1: "LIVE", 2: "DELAYED"}[status]

    wrapped = wrap_strategy_with_live_gate(
        BaseStrategy,
        lambda *_args: None,
        lambda status, data: statuses.append((status, data._symbol)),
    )
    strategy = object.__new__(wrapped)
    strategy.__dict__["_log_cb"] = lambda *_args: None
    strategy.__dict__["_data_live"] = False

    wrapped.notify_data(strategy, DummyData(), DummyData.DELAYED)
    wrapped.notify_data(strategy, DummyData(), DummyData.LIVE)

    assert statuses == [("delayed", "BTC/USDT"), ("live", "BTC/USDT")]
    assert strategy.__dict__["_data_live"] is True


def test_wrapped_strategy_logs_signal_when_pending_order_created():
    logs = []

    class BaseStrategy(bt.Strategy):
        def next(self):
            self.order = types.SimpleNamespace(ref=77, isbuy=lambda: True)

    class DummyDateTime:
        def datetime(self, index=0):
            return "2024-01-01T00:00:00"

    class DummyData:
        def __init__(self):
            self.close = [100.0]
            self.datetime = DummyDateTime()

        def __len__(self):
            return 1

    wrapped = wrap_strategy_with_live_gate(BaseStrategy, lambda level, msg: logs.append((level, msg)))
    wrapped.position = property(lambda self: types.SimpleNamespace(size=0))
    strategy = object.__new__(wrapped)
    strategy.__dict__["_log_cb"] = lambda level, msg: logs.append((level, msg))
    strategy.__dict__["_data_live"] = True
    strategy.__dict__["_last_signal_order_ref"] = None
    strategy.order = None
    strategy.datas = [DummyData()]

    wrapped.next(strategy)

    assert any("BUY signal created" in msg for _level, msg in logs)
    assert any(level == "debug" for level, _msg in logs)


def test_wrapped_strategy_logs_submitted_and_accepted_orders():
    logs = []

    class BaseStrategy(bt.Strategy):
        def notify_order(self, order):
            return None

    wrapped = wrap_strategy_with_live_gate(BaseStrategy, lambda level, msg: logs.append((level, msg)))
    strategy = object.__new__(wrapped)
    strategy.__dict__["_log_cb"] = lambda level, msg: logs.append((level, msg))
    strategy.__dict__["_last_signal_order_ref"] = None

    class DummyOrder:
        Submitted = 1
        Accepted = 2
        Completed = 3
        Rejected = 4
        Canceled = 5
        Margin = 6
        Expired = 7

        def __init__(self, status):
            self.status = status
            self.ref = 9
            self.created = types.SimpleNamespace(size=1.23)
            self.executed = types.SimpleNamespace(size=1.23, price=100.0)
            self.info = {}

        def isbuy(self):
            return True

        def getstatusname(self):
            return "Accepted"

    wrapped.notify_order(strategy, DummyOrder(DummyOrder.Submitted))
    wrapped.notify_order(strategy, DummyOrder(DummyOrder.Accepted))

    assert any("submitted" in msg.lower() for _level, msg in logs)
    assert any("accepted" in msg.lower() for _level, msg in logs)


def test_persist_and_update_order_uses_session_scoped_db_key(tmp_path, monkeypatch):
    db_path = (tmp_path / "live_orders.sqlite").as_posix()
    storage = SessionStorage(f"sqlite:///{db_path}")
    monkeypatch.setattr(live_engine, "_session_storage", storage)

    event = {
        'order_id': '1',
        'binance_order_id': 123456,
        'symbol': 'DOGE/USDT',
        'side': 'buy',
        'size': 0.25,
        'price': 0.2,
        'commission': 0.01,
        'cost': 0.05,
    }

    live_engine._persist_order('session-a', event, 'submitted')
    live_engine._persist_order('session-b', event, 'submitted')
    live_engine._update_order_status('session-b', '1', 'filled', event)

    orders_a = storage.get_session_orders('session-a')
    orders_b = storage.get_session_orders('session-b')

    assert orders_a[0]['order_id'] == '1'
    assert orders_a[0]['db_order_id'] == 'session-a:1'
    assert orders_a[0]['status'] == 'submitted'

    assert orders_b[0]['order_id'] == '1'
    assert orders_b[0]['db_order_id'] == 'session-b:1'
    assert orders_b[0]['status'] == 'filled'
    assert orders_b[0]['filled_price'] == 0.2


def test_start_session_passes_strategy_params_to_cerebro(monkeypatch):
    captured = {}

    class StubSession:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            self.status = live_engine.SessionStatus.STARTING
            self.feed_status = "warming_up"
            self.current_pnl = 0.0
            self.total_trades = 0
            self.positions = []
            self.orders = []
            self.error_message = None
            self.end_time = None
            self.ws_token = "token"

        def to_dict(self):
            return {
                "session_id": self.session_id,
                "strategy_name": self.strategy_name,
                "symbol": self.symbol,
                "exchange": self.exchange,
                "mode": self.mode,
                "timeframe": self.timeframe,
                "initial_cash": self.initial_cash,
                "commission": self.commission,
                "status": self.status.value,
                "feed_status": self.feed_status,
                "ws_token": self.ws_token,
            }

    class StubSessionManager:
        def create_session(self, **kwargs):
            return StubSession(**kwargs)

        def remove_session(self, _sid):
            return True

        def update_session(self, *_args, **_kwargs):
            return None

    class StubStore:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self._running = True

        def start(self):
            return None

        def stop(self):
            self._running = False

        def get_account(self):
            return {"balances": [{"asset": "USDT", "free": "123.45"}]}

        def fetch_ohlcv(self, **_kwargs):
            return [[1, 1.0, 1.0, 1.0, 1.0, 1.0]]

        def set_ticker_callback(self, _callback):
            return None

        def start_ticker_stream(self, _symbol):
            return None

    class StubBroker:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def set_event_callback(self, _callback):
            return None

        def set_log_callback(self, _callback):
            return None

    class StubData:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class StubCerebro:
        def addstrategy(self, strategy_cls, **kwargs):
            captured["strategy_cls"] = strategy_cls
            captured["params"] = kwargs

        def adddata(self, data_feed):
            captured["data_feed"] = data_feed

        def setbroker(self, broker):
            self.broker = broker
            captured["broker"] = broker

        def run(self):
            return []

    class DummyStrategy(bt.Strategy):
        pass

    storage_stub = types.SimpleNamespace(save_session=lambda _session: None)

    monkeypatch.setattr(live_engine, "get_session_manager", lambda: StubSessionManager())
    monkeypatch.setattr(live_engine, "load_user_strategy", lambda _name: DummyStrategy)
    monkeypatch.setattr(live_engine, "load_broker_config", lambda: object())
    monkeypatch.setattr(
        live_engine,
        "get_risk_config",
        lambda _cfg: types.SimpleNamespace(
            position_limits=types.SimpleNamespace(max_position_size_usd=1_000, max_positions_count=5),
            order_limits=types.SimpleNamespace(min_order_size_usd=10, max_order_size_usd=1_000),
        ),
    )
    monkeypatch.setattr(live_engine, "get_exchange_config", lambda _exchange, _cfg: types.SimpleNamespace(ccxt_id="binance"))
    monkeypatch.setattr(live_engine, "BinanceStore", StubStore)
    monkeypatch.setattr(live_engine, "BinanceBroker", StubBroker)
    monkeypatch.setattr(live_engine, "BinanceData", StubData)
    monkeypatch.setattr(live_engine.bt, "Cerebro", StubCerebro)
    monkeypatch.setattr(live_engine, "_get_storage", lambda: storage_stub)
    monkeypatch.setattr(live_engine, "_get_ws_manager", lambda: None)

    analyzer_module = types.SimpleNamespace(
        AnalyzerMode=types.SimpleNamespace(LIVE="live"),
        configure_analyzers=lambda *_args, **_kwargs: None,
    )
    monkeypatch.setitem(__import__("sys").modules, "src.service.analyzer_config", analyzer_module)
    monkeypatch.setattr(
        live_engine,
        "wrap_strategy_with_live_gate",
        lambda strategy_cls, *_args: strategy_cls,
    )

    result = live_engine.start_session(
        strategy_name="easy_live_trigger_test",
        symbol="DOGE/USDT",
        mode="paper",
        timeframe="1m",
        params={"target_trade_value_usd": 88, "min_trade_value_usd": 22},
    )

    assert captured["params"] == {"target_trade_value_usd": 88, "min_trade_value_usd": 22}
    assert result["initial_cash"] == 123.45
