import types

import pytest

from src.brokers.ccxt_adapter.ccxt_broker import CCXTBroker, BrokerEvent


class StubStore:
    """Minimal store stub for broker tests."""
    mode = "paper"

    def get_exchange(self):
        return types.SimpleNamespace(
            cancel_order=lambda *a, **kw: None,
            fetch_order=lambda *a, **kw: {},
        )


def test_ccxt_broker_notification_queue():
    broker = CCXTBroker(store=StubStore(), cash=100, commission=0.0)
    assert broker.get_notification() is None

    marker = object()
    broker.notify(marker)
    assert broker.get_notification() is marker


def test_ccxt_broker_initial_cash():
    broker = CCXTBroker(store=StubStore(), cash=5000, commission=0.002)
    assert broker.getcash() == pytest.approx(5000.0)
    assert broker.getvalue() == pytest.approx(5000.0)


def test_ccxt_broker_event_callback():
    events = []

    def callback(event_type, data):
        events.append((event_type, data))

    broker = CCXTBroker(store=StubStore(), cash=1000, commission=0.0)
    broker.set_event_callback(callback)
    broker._emit(BrokerEvent.ORDER_SUBMITTED, {"order_id": 1})

    assert len(events) == 1
    assert events[0][0] == BrokerEvent.ORDER_SUBMITTED
    assert events[0][1]["order_id"] == 1


def test_ccxt_broker_emit_without_callback():
    """Emit should not raise if no callback is set."""
    broker = CCXTBroker(store=StubStore(), cash=1000, commission=0.0)
    broker._emit(BrokerEvent.ORDER_FILLED, {"order_id": 2})


def test_ccxt_broker_event_callback_error_handling():
    """Callback errors should be caught, not propagated."""
    def bad_callback(event_type, data):
        raise ValueError("test error")

    broker = CCXTBroker(store=StubStore(), cash=1000, commission=0.0)
    broker.set_event_callback(bad_callback)
    # Should not raise
    broker._emit(BrokerEvent.PNL_UPDATE, {"pnl": 0})


def test_broker_event_types():
    """Verify all expected event types exist."""
    assert BrokerEvent.ORDER_SUBMITTED == 'order_submitted'
    assert BrokerEvent.ORDER_FILLED == 'order_filled'
    assert BrokerEvent.ORDER_PARTIAL == 'order_partial'
    assert BrokerEvent.ORDER_CANCELLED == 'order_cancelled'
    assert BrokerEvent.ORDER_REJECTED == 'order_rejected'
    assert BrokerEvent.TRADE_EXECUTED == 'trade_executed'
    assert BrokerEvent.POSITION_UPDATE == 'position_update'
    assert BrokerEvent.PNL_UPDATE == 'pnl_update'
