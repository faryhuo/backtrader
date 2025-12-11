import sys
import types
import unittest
import uuid

from auto_test.test_support import (
    ensure_backend_on_path,
    reset_session_manager,
)

# Prevent heavy ccxt imports during testing by installing a lightweight stub
# before the application modules load.
ccxt_async = types.ModuleType("ccxt.async_support")


class _DummyExchange:
    id = "dummy"

    def __init__(self, config=None):
        self.config = config or {}

    async def fetch_status(self):
        return {"status": "ok"}

    async def load_markets(self):
        return {"BTC/USDT": {}}

    async def close(self):
        return None


ccxt_async.Exchange = _DummyExchange
ccxt_async.NetworkError = Exception
ccxt_async.binance = _DummyExchange
ccxt_async.okx = _DummyExchange
ccxt_async.bybit = _DummyExchange

ccxt_root = types.ModuleType("ccxt")
ccxt_root.async_support = ccxt_async
ccxt_root.Exchange = _DummyExchange
ccxt_root.NetworkError = Exception
ccxt_root.binance = _DummyExchange
ccxt_root.okx = _DummyExchange
ccxt_root.bybit = _DummyExchange

sys.modules.setdefault("ccxt", ccxt_root)
sys.modules.setdefault("ccxt.async_support", ccxt_async)

ensure_backend_on_path()

from fastapi.testclient import TestClient

from src.service.app import app
from src.service.session_manager import SessionStatus, get_session_manager


class LiveRoutesTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def setUp(self) -> None:
        self.manager = reset_session_manager()

    def tearDown(self) -> None:
        reset_session_manager()

    def test_health_reports_enabled_exchanges(self) -> None:
        response = self.client.get("/api/live/health")

        self.assertEqual(200, response.status_code)
        payload = response.json()

        self.assertEqual("healthy", payload.get("status"))
        self.assertIn("binance", payload.get("enabled_exchanges", []))
        self.assertIn("session_counts", payload)

    def test_start_rejected_when_live_disabled(self) -> None:
        response = self.client.post(
            "/api/live/start",
            json={
                "strategy_name": "sma_cross",
                "symbol": "BTC/USDT",
                "exchange": "binance",
                "mode": "paper",
                "timeframe": "1m",
                "initial_cash": 10000,
                "commission": 0.001,
            },
        )

        self.assertEqual(403, response.status_code)
        self.assertIn("Live trading is disabled", response.json().get("detail", ""))

    def test_list_sessions_returns_seeded_session(self) -> None:
        session_id = str(uuid.uuid4())
        session = self.manager.create_session(
            session_id=session_id,
            strategy_name="sma_cross",
            symbol="BTC/USDT",
        )

        response = self.client.get("/api/live/sessions")

        self.assertEqual(200, response.status_code)
        payload = response.json()

        self.assertIsInstance(payload, list)
        self.assertEqual(1, len(payload))

        item = payload[0]
        self.assertEqual(session.session_id, item["session_id"])
        self.assertEqual(session.status.value, item["status"])
        self.assertEqual(session.symbol, item["symbol"])
        self.assertEqual(session.exchange, item["exchange"])
        self.assertEqual(session.timeframe, item["timeframe"])
        self.assertEqual(session.initial_cash, item["initial_cash"])
        self.assertEqual(session.mode, item["mode"])
        self.assertEqual(session.strategy_name, item["strategy_name"])
        self.assertEqual(SessionStatus.STARTING.value, item["status"])


if __name__ == "__main__":
    unittest.main()
