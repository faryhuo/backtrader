import asyncio

import pytest

from src.service.websocket_manager import WebSocketManager


class StubWebSocket:
    def __init__(self, *, fail_send: bool = False):
        self.accepted = False
        self.sent = []
        self.fail_send = fail_send

    async def accept(self):
        self.accepted = True

    async def send_json(self, message):
        if self.fail_send:
            raise RuntimeError("send failed")
        self.sent.append(message)


def run(coro):
    return asyncio.run(coro)


def test_connect_sends_welcome_message():
    manager = WebSocketManager()
    ws = StubWebSocket()

    run(manager.connect(ws, "s1"))

    assert ws.accepted is True
    assert manager.get_connection_count("s1") == 1
    assert ws.sent[0]["type"] == "connected"
    assert ws.sent[0]["session_id"] == "s1"


def test_disconnect_removes_session_when_last_connection():
    manager = WebSocketManager()
    ws = StubWebSocket()

    run(manager.connect(ws, "s1"))
    run(manager.disconnect(ws, "s1"))

    assert manager.get_connection_count("s1") == 0
    assert "s1" not in manager.get_connected_sessions()


def test_broadcast_to_multiple_clients_and_cleanup_dead_connections():
    manager = WebSocketManager()
    good = StubWebSocket()
    bad = StubWebSocket()

    run(manager.connect(good, "s1"))
    run(manager.connect(bad, "s1"))
    bad.fail_send = True

    sent = run(manager.broadcast("s1", {"type": "log", "data": {"message": "hi"}}))

    assert sent == 1
    assert manager.get_connection_count("s1") == 1
    assert good.sent[-1]["type"] == "log"


def test_broadcast_returns_zero_when_no_session():
    manager = WebSocketManager()
    assert run(manager.broadcast("missing", {"type": "x"})) == 0
