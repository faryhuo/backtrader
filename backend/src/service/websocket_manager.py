"""
WebSocket Manager - Manage WebSocket connections for real-time updates.

This module provides centralized WebSocket connection management,
broadcasting events to connected clients for live trading monitoring.
"""

import asyncio
import json
import logging
from typing import Dict, List, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections for live trading updates.

    This class:
    - Maintains connection pool per session
    - Broadcasts events to all connected clients
    - Handles connection/disconnection gracefully
    - Supports multiple sessions simultaneously

    Message Types:
        - position: Position update
        - order: Order execution
        - pnl: P&L update
        - trade: Trade executed
        - log: Strategy log message
        - error: Error notification
        - status: Session status change
    """

    def __init__(self):
        """Initialize WebSocket manager."""
        # session_id -> Set[WebSocket]
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
        logger.info("WebSocketManager initialized")

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        """
        Accept and register new WebSocket connection.

        Args:
            websocket: WebSocket connection
            session_id: Trading session ID
        """
        await websocket.accept()

        async with self._lock:
            if session_id not in self._connections:
                self._connections[session_id] = set()

            self._connections[session_id].add(websocket)

        logger.info(
            f"WebSocket connected for session {session_id}. "
            f"Total connections: {len(self._connections[session_id])}"
        )

        # Send welcome message
        await self._send_to_client(websocket, {
            'type': 'connected',
            'session_id': session_id,
            'message': 'Connected to live trading session'
        })

    async def disconnect(self, websocket: WebSocket, session_id: str) -> None:
        """
        Disconnect and remove WebSocket connection.

        Args:
            websocket: WebSocket connection
            session_id: Trading session ID
        """
        async with self._lock:
            if session_id in self._connections:
                self._connections[session_id].discard(websocket)

                # Remove session if no more connections
                if not self._connections[session_id]:
                    del self._connections[session_id]

        logger.info(f"WebSocket disconnected for session {session_id}")

    async def broadcast(self, session_id: str, message: dict) -> int:
        """
        Broadcast message to all clients connected to session.

        Args:
            session_id: Session to broadcast to
            message: Message dictionary (will be JSON serialized)

        Returns:
            Number of clients that received the message
        """
        logger.info(f"[BROADCAST] Session {session_id}, type={message.get('type', 'unknown')}, connections={len(self._connections.get(session_id, []))}")

        if session_id not in self._connections:
            logger.warning(f"[BROADCAST] No WebSocket connections for session {session_id}")
            return 0

        # Get copy of connections to avoid modification during iteration
        async with self._lock:
            connections = self._connections.get(session_id, set()).copy()

        if not connections:
            return 0

        # Track dead connections
        dead_connections = []
        sent_count = 0

        # Broadcast to all clients
        for websocket in connections:
            try:
                await self._send_to_client(websocket, message)
                sent_count += 1

            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                dead_connections.append(websocket)

        # Clean up dead connections
        if dead_connections:
            async with self._lock:
                if session_id in self._connections:
                    for ws in dead_connections:
                        self._connections[session_id].discard(ws)

                    # Remove session if no more connections
                    if not self._connections[session_id]:
                        del self._connections[session_id]

            logger.info(
                f"Cleaned up {len(dead_connections)} dead connections "
                f"for session {session_id}"
            )

        logger.debug(
            f"Broadcast to {sent_count} clients for session {session_id}: "
            f"{message.get('type', 'unknown')}"
        )

        return sent_count

    async def broadcast_position_update(
        self,
        session_id: str,
        symbol: str,
        size: float,
        avg_price: float,
        current_price: float,
        pnl: float
    ) -> None:
        """
        Broadcast position update.

        Args:
            session_id: Session ID
            symbol: Trading pair
            size: Position size
            avg_price: Average entry price
            current_price: Current market price
            pnl: Unrealized P&L
        """
        await self.broadcast(session_id, {
            'type': 'position',
            'data': {
                'symbol': symbol,
                'size': size,
                'avg_price': avg_price,
                'current_price': current_price,
                'pnl': pnl,
                'pnl_percent': (pnl / (abs(size) * avg_price) * 100) if size != 0 else 0
            }
        })

    async def broadcast_order_update(
        self,
        session_id: str,
        order_id: str,
        symbol: str,
        side: str,
        size: float,
        price: float,
        status: str,
        filled_size: float = 0,
        filled_price: float = 0
    ) -> None:
        """
        Broadcast order update.

        Args:
            session_id: Session ID
            order_id: Order identifier
            symbol: Trading pair
            side: 'buy' or 'sell'
            size: Order size
            price: Order price
            status: Order status
            filled_size: Filled size
            filled_price: Average fill price
        """
        await self.broadcast(session_id, {
            'type': 'order',
            'data': {
                'order_id': order_id,
                'symbol': symbol,
                'side': side,
                'size': size,
                'price': price,
                'status': status,
                'filled_size': filled_size,
                'filled_price': filled_price
            }
        })

    async def broadcast_pnl_update(
        self,
        session_id: str,
        current_pnl: float,
        total_pnl_percent: float,
        cash: float,
        portfolio_value: float
    ) -> None:
        """
        Broadcast P&L update.

        Args:
            session_id: Session ID
            current_pnl: Current P&L
            total_pnl_percent: Total P&L percentage
            cash: Current cash balance
            portfolio_value: Total portfolio value
        """
        await self.broadcast(session_id, {
            'type': 'pnl',
            'data': {
                'current_pnl': current_pnl,
                'total_pnl_percent': total_pnl_percent,
                'cash': cash,
                'portfolio_value': portfolio_value
            }
        })

    async def broadcast_trade_executed(
        self,
        session_id: str,
        symbol: str,
        side: str,
        size: float,
        price: float,
        commission: float,
        pnl: float = None
    ) -> None:
        """
        Broadcast trade execution.

        Args:
            session_id: Session ID
            symbol: Trading pair
            side: 'buy' or 'sell'
            size: Trade size
            price: Execution price
            commission: Commission paid
            pnl: P&L (for closing trades)
        """
        await self.broadcast(session_id, {
            'type': 'trade',
            'data': {
                'symbol': symbol,
                'side': side,
                'size': size,
                'price': price,
                'commission': commission,
                'pnl': pnl
            }
        })

    async def broadcast_log(
        self,
        session_id: str,
        level: str,
        message: str
    ) -> None:
        """
        Broadcast log message.

        Args:
            session_id: Session ID
            level: Log level (info, warning, error)
            message: Log message
        """
        await self.broadcast(session_id, {
            'type': 'log',
            'data': {
                'level': level,
                'message': message,
                'timestamp': asyncio.get_event_loop().time()
            }
        })

    async def broadcast_error(
        self,
        session_id: str,
        error_message: str,
        error_code: str = None
    ) -> None:
        """
        Broadcast error notification.

        Args:
            session_id: Session ID
            error_message: Error description
            error_code: Optional error code
        """
        await self.broadcast(session_id, {
            'type': 'error',
            'data': {
                'message': error_message,
                'code': error_code
            }
        })

    async def broadcast_status_change(
        self,
        session_id: str,
        old_status: str,
        new_status: str
    ) -> None:
        """
        Broadcast session status change.

        Args:
            session_id: Session ID
            old_status: Previous status
            new_status: New status
        """
        await self.broadcast(session_id, {
            'type': 'status',
            'data': {
                'old_status': old_status,
                'new_status': new_status
            }
        })

    async def broadcast_feed_status(
        self,
        session_id: str,
        status: str,
        symbol: str = ''
    ) -> None:
        """Broadcast feed warmup/live status to the frontend."""
        await self.broadcast(session_id, {
            'type': 'feed_status',
            'data': {
                'status': status,
                'symbol': symbol
            }
        })

    async def broadcast_ticker(
        self,
        session_id: str,
        symbol: str,
        last_price: float,
        bid: float,
        ask: float,
        timestamp: int
    ) -> None:
        """
        Broadcast real-time ticker price update.

        Args:
            session_id: Session ID
            symbol: Trading pair
            last_price: Last traded price
            bid: Best bid price
            ask: Best ask price
            timestamp: Exchange timestamp (ms)
        """
        await self.broadcast(session_id, {
            'type': 'ticker',
            'data': {
                'symbol': symbol,
                'last': last_price,
                'bid': bid,
                'ask': ask,
                'timestamp': timestamp
            }
        })

    async def broadcast_ohlcv(
        self,
        session_id: str,
        symbol: str,
        ohlcv_list: list
    ) -> None:
        """
        Broadcast historical OHLCV data (for chart initialization).

        Args:
            session_id: Session ID
            symbol: Trading pair
            ohlcv_list: List of [timestamp, open, high, low, close, volume]
        """
        # Convert to chart-friendly format
        bars = []
        for bar in ohlcv_list:
            bars.append({
                'time': bar[0] // 1000,  # Convert ms to seconds
                'open': bar[1],
                'high': bar[2],
                'low': bar[3],
                'close': bar[4],
                'volume': bar[5],
            })

        await self.broadcast(session_id, {
            'type': 'ohlcv',
            'data': {
                'symbol': symbol,
                'bars': bars
            }
        })

    async def broadcast_task_update(
        self,
        task_id: str,
        status: str,
        progress: int,
        message: str = None,
        error: str = None,
        result_id: str = None,
    ) -> None:
        """
        Broadcast task status/progress update.

        Args:
            task_id: Task identifier
            status: Task status (pending, running, completed, failed, cancelled)
            progress: Progress percentage (0-100)
            message: Optional progress message
            error: Optional error message for failed tasks
            result_id: Optional link to result record
        """
        await self.broadcast("tasks", {
            'type': 'task_update',
            'data': {
                'task_id': task_id,
                'status': status,
                'progress': progress,
                'message': message,
                'error': error,
                'result_id': result_id,
            }
        })

    async def broadcast_task_event(
        self,
        task_id: str,
        event_type: str,
        data: dict = None,
    ) -> None:
        """
        Broadcast task lifecycle event.

        Args:
            task_id: Task identifier
            event_type: Event type (created, started, progress, completed, failed, cancelled)
            data: Additional event data
        """
        await self.broadcast("tasks", {
            'type': f'task_{event_type}',
            'task_id': task_id,
            'data': data or {},
        })

    async def _send_to_client(self, websocket: WebSocket, message: dict) -> None:
        """
        Send message to single WebSocket client.

        Args:
            websocket: WebSocket connection
            message: Message dictionary

        Raises:
            Exception: If send fails
        """
        await websocket.send_json(message)

    def get_connection_count(self, session_id: str = None) -> int:
        """
        Get count of WebSocket connections.

        Args:
            session_id: Optional session ID filter

        Returns:
            Connection count
        """
        if session_id:
            return len(self._connections.get(session_id, set()))
        else:
            return sum(len(conns) for conns in self._connections.values())

    def get_connected_sessions(self) -> List[str]:
        """
        Get list of session IDs with active connections.

        Returns:
            List of session IDs
        """
        return list(self._connections.keys())


# Global WebSocket manager instance
_ws_manager = WebSocketManager()


def get_websocket_manager() -> WebSocketManager:
    """
    Get the global WebSocket manager instance.

    Returns:
        WebSocketManager: Global manager
    """
    return _ws_manager
