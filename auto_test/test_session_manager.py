import unittest
import uuid

from auto_test.test_support import ensure_backend_on_path, reset_session_manager

ensure_backend_on_path()

from src.service.session_manager import SessionStatus, get_session_manager


class SessionManagerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = reset_session_manager()

    def tearDown(self) -> None:
        reset_session_manager()

    def test_create_and_get_session(self) -> None:
        session_id = str(uuid.uuid4())
        session = self.manager.create_session(
            session_id=session_id,
            strategy_name="sma_cross",
            symbol="BTC/USDT",
        )

        fetched = self.manager.get_session(session_id)

        self.assertIsNotNone(fetched)
        self.assertEqual(session.session_id, fetched.session_id)
        self.assertEqual(SessionStatus.STARTING, fetched.status)
        self.assertTrue(fetched.is_active())

    def test_stop_session_marks_session_stopped(self) -> None:
        session_id = str(uuid.uuid4())
        self.manager.create_session(
            session_id=session_id,
            strategy_name="sma_cross",
            symbol="BTC/USDT",
        )

        result = self.manager.stop_session(session_id, timeout=0.1)

        self.assertTrue(result)
        stopped = self.manager.get_session(session_id)
        self.assertIsNotNone(stopped)
        self.assertEqual(SessionStatus.STOPPED, stopped.status)
        self.assertIsNotNone(stopped.end_time)
        self.assertTrue(stopped.is_stopped())

    def test_stop_all_sessions_handles_multiple(self) -> None:
        session_ids = [str(uuid.uuid4()) for _ in range(2)]
        for session_id in session_ids:
            self.manager.create_session(
                session_id=session_id,
                strategy_name="sma_cross",
                symbol="BTC/USDT",
            )

        results = self.manager.stop_all_sessions(timeout=0.1)

        self.assertEqual(set(session_ids), set(results.keys()))
        self.assertTrue(all(results.values()))

        statuses = {s.session_id: s.status for s in self.manager.list_sessions()}
        for session_id in session_ids:
            self.assertEqual(SessionStatus.STOPPED, statuses[session_id])


if __name__ == "__main__":
    unittest.main()
