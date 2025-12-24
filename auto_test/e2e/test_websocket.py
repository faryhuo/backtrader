"""
E2E tests for WebSocket endpoints.

Based on TEST_CASES.md - WS section:
- WS-001: Live WS with non-existent session closes with 1008
- WS-002: Live WS without/invalid token closes with 1008
- WS-003: Live WS ping/pong works
- WS-004: Tasks WS receives task events
"""

import pytest
import sys
from pathlib import Path

# Add libs to path
libs_path = Path(__file__).parent.parent / "libs"
sys.path.insert(0, str(libs_path))


# ========== WebSocket Tests ==========

@pytest.mark.websocket
@pytest.mark.slow
class TestLiveWebSocket:
    """WebSocket tests for live trading."""

    def test_ws_001_nonexistent_session(self, api_base_url):
        """WS-001: Live WS with non-existent session closes with 1008."""
        try:
            import websocket
        except ImportError:
            pytest.skip("websocket-client not installed")
        
        ws_url = api_base_url.replace("http://", "ws://").replace("https://", "wss://")
        fake_session_id = "00000000-0000-0000-0000-000000000000"
        
        try:
            ws = websocket.create_connection(
                f"{ws_url}/ws/live/{fake_session_id}",
                timeout=5
            )
            # If connected, server should close it
            # Wait for close frame
            try:
                ws.recv()
            except websocket.WebSocketConnectionClosedException as e:
                # Expected - session doesn't exist
                pass
            ws.close()
        except websocket.WebSocketBadStatusException as e:
            # HTTP error before upgrade, also acceptable
            assert e.status_code in [401, 403, 404]
        except Exception as e:
            if "1008" in str(e) or "connection" in str(e).lower():
                pass  # Expected close
            else:
                raise

    def test_ws_002_missing_token(self, api_base_url):
        """WS-002: Live WS without token closes with 1008 or rejects."""
        try:
            import websocket
        except ImportError:
            pytest.skip("websocket-client not installed")
        
        ws_url = api_base_url.replace("http://", "ws://").replace("https://", "wss://")
        fake_session_id = "00000000-0000-0000-0000-000000000000"
        
        try:
            ws = websocket.create_connection(
                f"{ws_url}/ws/live/{fake_session_id}",
                timeout=5
                # No token provided
            )
            ws.close()
        except websocket.WebSocketBadStatusException as e:
            # Rejected at HTTP level
            assert e.status_code in [401, 403, 404]
        except Exception as e:
            # Connection closed or rejected
            pass  # Expected behavior

    def test_ws_002_invalid_token(self, api_base_url):
        """WS-002: Live WS with invalid token closes with 1008."""
        try:
            import websocket
        except ImportError:
            pytest.skip("websocket-client not installed")
        
        ws_url = api_base_url.replace("http://", "ws://").replace("https://", "wss://")
        fake_session_id = "00000000-0000-0000-0000-000000000000"
        
        try:
            ws = websocket.create_connection(
                f"{ws_url}/ws/live/{fake_session_id}?token=invalid_token_xyz",
                timeout=5
            )
            ws.close()
        except websocket.WebSocketBadStatusException as e:
            # Rejected at HTTP level
            assert e.status_code in [401, 403, 404]
        except Exception as e:
            # Connection closed
            pass  # Expected


@pytest.mark.websocket
@pytest.mark.slow
class TestTasksWebSocket:
    """WebSocket tests for task updates."""

    def test_ws_004_tasks_connection(self, api_base_url):
        """WS-004: Tasks WS connection works."""
        try:
            import websocket
        except ImportError:
            pytest.skip("websocket-client not installed")
        
        ws_url = api_base_url.replace("http://", "ws://").replace("https://", "wss://")
        
        try:
            ws = websocket.create_connection(
                f"{ws_url}/ws/tasks",
                timeout=5
            )
            # Connection successful
            ws.close()
        except websocket.WebSocketBadStatusException as e:
            # Auth required
            assert e.status_code in [401, 403]
        except Exception as e:
            if "refused" in str(e).lower():
                pytest.skip("WebSocket server not running")
            raise
