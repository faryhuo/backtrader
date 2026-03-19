from datetime import datetime

from src.db.models import OrderModel, OrderStatusEnum
from src.db.storage.session import SessionStorage
from src.service.session_manager import SessionStatus, TradingSession


def test_save_load_list_delete_session(tmp_path):
    db_path = (tmp_path / "sessions.sqlite").as_posix()
    storage = SessionStorage(f"sqlite:///{db_path}")

    session = TradingSession(
        session_id="s1",
        strategy_name="strat",
        symbol="BTC/USDT",
        exchange="binance",
        mode="paper",
        timeframe="1m",
        initial_cash=10000.0,
        commission=0.001,
        status=SessionStatus.RUNNING,
        start_time=datetime.utcnow(),
    )
    storage.save_session(session)

    loaded = storage.load_session("s1")
    assert loaded is not None
    assert loaded.session_id == "s1"
    assert loaded.status == SessionStatus.RUNNING

    listed = storage.list_sessions()
    assert len(listed) == 1

    assert storage.delete_session("s1") is True
    assert storage.load_session("s1") is None


def test_save_order_uses_session_scoped_primary_key(tmp_path):
    db_path = (tmp_path / "orders.sqlite").as_posix()
    storage = SessionStorage(f"sqlite:///{db_path}")

    storage.save_order({
        'order_id': '1',
        'session_id': 'session-a',
        'symbol': 'DOGE/USDT',
        'side': 'buy',
        'type': 'market',
        'size': 1.0,
        'status': 'submitted',
    })
    storage.save_order({
        'order_id': '1',
        'session_id': 'session-b',
        'symbol': 'DOGE/USDT',
        'side': 'sell',
        'type': 'market',
        'size': 2.0,
        'status': 'submitted',
    })

    orders_a = storage.get_session_orders('session-a')
    orders_b = storage.get_session_orders('session-b')

    assert orders_a[0]['order_id'] == '1'
    assert orders_b[0]['order_id'] == '1'
    assert orders_a[0]['db_order_id'] == 'session-a:1'
    assert orders_b[0]['db_order_id'] == 'session-b:1'

    with storage.managed_session(commit_on_success=False) as db:
        stored = db.query(OrderModel).order_by(OrderModel.order_id).all()
        assert [order.order_id for order in stored] == ['session-a:1', 'session-b:1']
        assert [order.metadata_json['client_order_id'] for order in stored] == ['1', '1']


def test_get_session_orders_returns_original_client_order_id(tmp_path):
    db_path = (tmp_path / "orders_client_id.sqlite").as_posix()
    storage = SessionStorage(f"sqlite:///{db_path}")

    storage.save_order({
        'order_id': '42',
        'session_id': 'session-a',
        'symbol': 'BTC/USDT',
        'side': 'buy',
        'type': 'market',
        'size': 0.1,
        'status': 'submitted',
    })

    with storage.managed_session() as db:
        order = db.query(OrderModel).filter(OrderModel.order_id == 'session-a:42').first()
        order.status = OrderStatusEnum.FILLED
        order.filled_size = 0.1
        order.filled_price = 123.45

    orders = storage.get_session_orders('session-a')
    assert len(orders) == 1
    assert orders[0]['order_id'] == '42'
    assert orders[0]['db_order_id'] == 'session-a:42'
    assert orders[0]['status'] == 'filled'
    assert orders[0]['filled_size'] == 0.1
    assert orders[0]['filled_price'] == 123.45
    assert isinstance(orders[0]['created_at'], str)

