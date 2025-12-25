/**
 * WebSocket Client Hook for Live Trading Updates
 *
 * Provides a React hook for connecting to live trading WebSocket
 * and receiving real-time updates.
 *
 * Uses useWebSocketBase for connection management.
 */

import { useCallback } from 'react';
import { useWebSocketBase, buildWebSocketUrl } from '../hooks/useWebSocketBase';

/**
 * WebSocket connection hook for live trading sessions
 *
 * @param {string|null} sessionId - Session ID to connect to
 * @param {object} options - Connection options
 * @returns {object} WebSocket state and methods
 *
 * @example
 * const {
 *   lastMessage,
 *   sendMessage,
 *   readyState,
 *   connect,
 *   disconnect
 * } = useWebSocket(sessionId);
 */
export function useWebSocket(sessionId, options = {}) {
  const {
    autoConnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    heartbeatInterval = 30000,
    token = null,  // ws_token for authentication
    onOpen = null,
    onClose = null,
    onError = null,
    onMessage = null,
  } = options;

  // Build live session WebSocket URL
  const buildUrl = useCallback(() => {
    if (!sessionId) return null;

    // Include token as query parameter for authentication
    const tokenParam = token ? `?token=${encodeURIComponent(token)}` : '';
    return buildWebSocketUrl(`/ws/live/${sessionId}${tokenParam}`);
  }, [sessionId, token]);

  // Use the base WebSocket hook
  const {
    readyState,
    lastMessage,
    reconnectAttempts,
    isOpen,
    isConnecting,
    isClosed,
    connect: baseConnect,
    disconnect,
    sendMessage,
  } = useWebSocketBase({
    buildUrl,
    autoConnect: autoConnect && !!sessionId,
    reconnectInterval,
    maxReconnectAttempts,
    heartbeatInterval,
    onOpen,
    onClose,
    onError,
    onMessage,
  });

  // Extended connect that allows overriding sessionId/token
  const connect = useCallback((overrideSessionId = null, overrideToken = null) => {
    // If override parameters provided, we need to rebuild URL
    // For now, just use base connect - the buildUrl callback will use current sessionId/token
    if (overrideSessionId || overrideToken) {
      console.warn('Override sessionId/token in connect() is deprecated. Update the hook props instead.');
    }
    baseConnect();
  }, [baseConnect]);

  return {
    lastMessage,
    sendMessage,
    readyState,
    connect,
    disconnect,
    isOpen,
    isConnecting,
    isClosed,
    reconnectAttempts,
  };
}

/**
 * Parse WebSocket message by type
 *
 * @param {object} message - WebSocket message
 * @returns {object} Parsed message with type-specific data
 */
export function parseWebSocketMessage(message) {
  if (!message || !message.type) {
    return null;
  }

  return {
    type: message.type,
    data: message.data || {},
    timestamp: Date.now(),
  };
}

/**
 * WebSocket message type constants
 */
export const WS_MESSAGE_TYPES = {
  CONNECTED: 'connected',
  POSITION: 'position',
  ORDER: 'order',
  PNL: 'pnl',
  TRADE: 'trade',
  LOG: 'log',
  ERROR: 'error',
  STATUS: 'status',
  PONG: 'pong',
};

export default useWebSocket;
