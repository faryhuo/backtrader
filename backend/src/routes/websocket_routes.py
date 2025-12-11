"""
WebSocket Routes - Real-time updates for live trading.

This module provides WebSocket endpoint for streaming real-time
updates to the frontend dashboard.
"""

import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException

from src.service.websocket_manager import get_websocket_manager
from src.service.session_manager import get_session_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/live/{session_id}")
async def websocket_live_updates(
    websocket: WebSocket,
    session_id: str,
    token: Optional[str] = Query(None, description="Authentication token (optional for Phase 3)")
):
    """
    WebSocket endpoint for real-time trading updates.

    **Connection:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/live/{session_id}');
    ```

    **Message Types Received:**

    1. **Connected**
    ```json
    {
      "type": "connected",
      "session_id": "abc123",
      "message": "Connected to live trading session"
    }
    ```

    2. **Position Update**
    ```json
    {
      "type": "position",
      "data": {
        "symbol": "BTC/USDT",
        "size": 0.1,
        "avg_price": 95000,
        "current_price": 95500,
        "pnl": 50,
        "pnl_percent": 0.53
      }
    }
    ```

    3. **Order Update**
    ```json
    {
      "type": "order",
      "data": {
        "order_id": "12345",
        "symbol": "BTC/USDT",
        "side": "buy",
        "size": 0.1,
        "price": 95000,
        "status": "filled",
        "filled_size": 0.1,
        "filled_price": 95000
      }
    }
    ```

    4. **P&L Update**
    ```json
    {
      "type": "pnl",
      "data": {
        "current_pnl": 150.5,
        "total_pnl_percent": 1.5,
        "cash": 9850,
        "portfolio_value": 10150.5
      }
    }
    ```

    5. **Trade Executed**
    ```json
    {
      "type": "trade",
      "data": {
        "symbol": "BTC/USDT",
        "side": "buy",
        "size": 0.1,
        "price": 95000,
        "commission": 9.5,
        "pnl": null
      }
    }
    ```

    6. **Log Message**
    ```json
    {
      "type": "log",
      "data": {
        "level": "info",
        "message": "Strategy bought BTC/USDT @ 95000",
        "timestamp": 1702345678.123
      }
    }
    ```

    7. **Error**
    ```json
    {
      "type": "error",
      "data": {
        "message": "Order rejected: insufficient balance",
        "code": "INSUFFICIENT_BALANCE"
      }
    }
    ```

    8. **Status Change**
    ```json
    {
      "type": "status",
      "data": {
        "old_status": "running",
        "new_status": "stopped"
      }
    }
    ```

    **Client Messages (send to server):**

    - Ping (keep-alive):
    ```json
    {"type": "ping"}
    ```

    Server responds with:
    ```json
    {"type": "pong"}
    ```
    """
    ws_manager = get_websocket_manager()
    session_manager = get_session_manager()

    # TODO: Phase 6 - Implement authentication
    # For now, authentication is optional
    if token:
        logger.debug(f"WebSocket connection with token: {token[:10]}...")

    # Verify session exists
    session = session_manager.get_session(session_id)
    if not session:
        logger.warning(f"WebSocket connection attempted for non-existent session: {session_id}")
        await websocket.close(code=1008, reason="Session not found")
        return

    # Connect WebSocket
    await ws_manager.connect(websocket, session_id)

    try:
        # Keep connection alive and handle client messages
        while True:
            # Receive message from client
            message = await websocket.receive_text()

            # Handle ping/pong for keep-alive
            if message == "ping" or message == '{"type":"ping"}':
                await websocket.send_json({"type": "pong"})
                continue

            # Handle other client messages (future expansion)
            try:
                import json
                data = json.loads(message)
                msg_type = data.get('type')

                if msg_type == 'ping':
                    await websocket.send_json({"type": "pong"})

                elif msg_type == 'subscribe':
                    # Future: Subscribe to specific events
                    logger.debug(f"Subscribe request: {data}")

                elif msg_type == 'unsubscribe':
                    # Future: Unsubscribe from events
                    logger.debug(f"Unsubscribe request: {data}")

                else:
                    logger.warning(f"Unknown message type from client: {msg_type}")

            except json.JSONDecodeError:
                # Not JSON, ignore
                logger.debug(f"Non-JSON message received: {message}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected from session {session_id}")

    except Exception as e:
        logger.exception(f"WebSocket error for session {session_id}: {e}")

    finally:
        # Cleanup connection
        await ws_manager.disconnect(websocket, session_id)


@router.get("/ws/info", tags=["WebSocket"])
async def websocket_info():
    """
    Get WebSocket connection information.

    **Returns:**
    - Active connection count
    - Connected sessions
    - WebSocket endpoint URL
    """
    ws_manager = get_websocket_manager()

    return {
        'endpoint': '/ws/live/{session_id}',
        'protocol': 'ws' if not hasattr(router, 'https') else 'wss',
        'active_connections': ws_manager.get_connection_count(),
        'connected_sessions': ws_manager.get_connected_sessions(),
        'message_types': [
            'connected', 'position', 'order', 'pnl', 'trade', 'log', 'error', 'status'
        ],
        'client_messages': ['ping'],
        'description': 'Real-time updates for live trading sessions'
    }
