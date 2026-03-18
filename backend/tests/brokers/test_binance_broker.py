"""Tests for BinanceBroker behaviour and emitted events."""

from datetime import datetime

import backtrader as bt

from src.brokers.binance_adapter.binance_broker import BinanceBroker


class DummyStore:
    def __init__(self, order_result=None, should_fail=False):
        self.order_result = order_result or {
            'orderId': 99,
            'status': 'FILLED',
            'executedQty': '2',
            'price': '100',
        }
        self.should_fail = should_fail
        self.create_order_calls = []

    def is_paper_mode(self):
        return True

    def create_order(self, **kwargs):
        self.create_order_calls.append(kwargs)
        if self.should_fail:
            raise RuntimeError('boom')
        return self.order_result

    def get_account(self):
        return {'balances': []}


class DummyDateTimeLine:
    def __getitem__(self, index):
        return 0.0

    def datetime(self, index=0):
        return datetime(2024, 1, 1)

    def date(self, index=0):
        return self.datetime(index).date()


class DummyData:
    def __init__(self, symbol='BTCUSDT', close=100.0):
        self._symbol = symbol
        self.close = [close]
        self.datetime = DummyDateTimeLine()

    def __len__(self):
        return 1


class TestBinanceBroker:
    def test_submit_filled_order_updates_state_and_emits_events(self):
        store = DummyStore()
        broker = BinanceBroker(store=store, cash=1000.0, commission=0.001)
        events = []
        broker.set_event_callback(lambda event_type, payload: events.append((event_type, payload)))

        order = broker._create_order(
            owner=None,
            data=DummyData(),
            size=2,
            price=100.0,
            plimit=None,
            exectype=bt.Order.Market,
            valid=None,
            tradeid=0,
            ordtype=bt.Order.Buy,
        )

        result = broker.submit(order)

        assert result.status == bt.Order.Completed
        assert broker.get_cash() == 799.8
        assert broker.getposition(order.data).size == 2
        event_names = [name for name, _ in events]
        assert event_names == ['order_submitted', 'order_filled', 'trade_executed', 'position_update', 'pnl_update']
        assert events[0][1]['symbol'] == 'BTCUSDT'
        assert events[2][1]['size'] == 2

    def test_submit_failure_rejects_order_and_emits_rejected(self):
        store = DummyStore(should_fail=True)
        broker = BinanceBroker(store=store, cash=1000.0)
        events = []
        broker.set_event_callback(lambda event_type, payload: events.append((event_type, payload)))

        order = broker._create_order(
            owner=None,
            data=DummyData(),
            size=1,
            price=100.0,
            plimit=None,
            exectype=bt.Order.Market,
            valid=None,
            tradeid=0,
            ordtype=bt.Order.Buy,
        )

        result = broker.submit(order)

        assert result.status == bt.Order.Rejected
        assert list(broker._open_orders.values()) == []
        assert events == [('order_rejected', {'order_id': '1', 'symbol': 'BTCUSDT', 'reason': 'boom'})]

    def test_insufficient_cash_rejects_without_store_call(self):
        store = DummyStore()
        broker = BinanceBroker(store=store, cash=50.0)

        order = broker._create_order(
            owner=None,
            data=DummyData(close=100.0),
            size=1,
            price=100.0,
            plimit=None,
            exectype=bt.Order.Market,
            valid=None,
            tradeid=0,
            ordtype=bt.Order.Buy,
        )

        result = broker.submit(order)

        assert result.status == bt.Order.Rejected
        assert broker.get_cash() == 50.0
        assert store.create_order_calls == []

    def test_buy_order_respects_min_order_size_limit(self):
        store = DummyStore()
        broker = BinanceBroker(store=store, cash=1000.0, min_order_size_usd=200.0)

        order = broker._create_order(
            owner=None,
            data=DummyData(close=100.0),
            size=1,
            price=100.0,
            plimit=None,
            exectype=bt.Order.Market,
            valid=None,
            tradeid=0,
            ordtype=bt.Order.Buy,
        )

        result = broker.submit(order)

        assert result.status == bt.Order.Rejected
        assert store.create_order_calls == []

    def test_buy_order_respects_max_positions_count(self):
        store = DummyStore()
        broker = BinanceBroker(store=store, cash=5000.0, max_positions_count=1)
        broker._positions[DummyData(symbol='ETHUSDT')].update(1, 50.0)

        order = broker._create_order(
            owner=None,
            data=DummyData(symbol='BTCUSDT', close=100.0),
            size=1,
            price=100.0,
            plimit=None,
            exectype=bt.Order.Market,
            valid=None,
            tradeid=0,
            ordtype=bt.Order.Buy,
        )

        result = broker.submit(order)

        assert result.status == bt.Order.Rejected
        assert store.create_order_calls == []

    def test_sell_order_requires_existing_position(self):
        store = DummyStore()
        broker = BinanceBroker(store=store, cash=1000.0)

        order = broker._create_order(
            owner=None,
            data=DummyData(close=100.0),
            size=1,
            price=100.0,
            plimit=None,
            exectype=bt.Order.Market,
            valid=None,
            tradeid=0,
            ordtype=bt.Order.Sell,
        )

        result = broker.submit(order)

        assert result.status == bt.Order.Rejected
        assert store.create_order_calls == []

    def test_market_fill_price_uses_fills_when_price_is_zero(self):
        store = DummyStore(order_result={
            'orderId': 99,
            'status': 'FILLED',
            'executedQty': '2',
            'price': '0',
            'fills': [
                {'price': '100', 'qty': '1'},
                {'price': '110', 'qty': '1'},
            ],
        })
        broker = BinanceBroker(store=store, cash=1000.0, commission=0.001)

        order = broker._create_order(
            owner=None,
            data=DummyData(close=105.0),
            size=2,
            price=None,
            plimit=None,
            exectype=bt.Order.Market,
            valid=None,
            tradeid=0,
            ordtype=bt.Order.Buy,
        )

        result = broker.submit(order)

        assert result.status == bt.Order.Completed
        assert result.executed.price == 105.0
        assert broker.get_cash() == 789.79
