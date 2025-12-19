import types

from src.brokers.ccxt_adapter.ccxt_broker import CCXTBroker


def test_ccxt_broker_notification_queue():
    class StubStore:
        mode = "paper"

        def get_exchange(self):
            return types.SimpleNamespace()

    broker = CCXTBroker(store=StubStore(), cash=100, commission=0.0, leverage=1)
    assert broker.get_notification() is None

    marker = object()
    broker.notify(marker)
    assert broker.get_notification() is marker

