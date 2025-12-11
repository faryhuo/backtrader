/**
 * WebSocket Client Hook for Live Trading Updates
 *
 * Provides a React hook for connecting to live trading WebSocket
 * and receiving real-time updates.
 */

import { useEffect, useRef, useState, useCallback } from 'react';

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
    onOpen = null,
    onClose = null,
    onError = null,
    onMessage = null,
  } = options;

  const [lastMessage, setLastMessage] = useState(null);
  const [readyState, setReadyState] = useState('CLOSED');
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  const wsRef = useRef(null);
  const heartbeatRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const shouldReconnectRef = useRef(true);

  // Get WebSocket URL
  const getWebSocketUrl = useCallback((sessionId) => {
    if (!sessionId) return null;

    // Determine protocol (ws or wss)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

    // In development, connect to backend server
    const isDevelopment = import.meta.env.DEV;
    const host = isDevelopment ? 'localhost:8000' : window.location.host;

    return `${protocol}//${host}/ws/live/${sessionId}`;
  }, []);

  // Send message to WebSocket
  const sendMessage = useCallback((message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const data = typeof message === 'string' ? message : JSON.stringify(message);
      wsRef.current.send(data);
      return true;
    }
    console.warn('WebSocket is not open. Cannot send message:', message);
    return false;
  }, []);

  // Send ping for keep-alive
  const sendPing = useCallback(() => {
    sendMessage({ type: 'ping' });
  }, [sendMessage]);

  // Start heartbeat
  const startHeartbeat = useCallback(() => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
    }

    heartbeatRef.current = setInterval(() => {
      sendPing();
    }, heartbeatInterval);
  }, [heartbeatInterval, sendPing]);

  // Stop heartbeat
  const stopHeartbeat = useCallback(() => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
      heartbeatRef.current = null;
    }
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!sessionId) {
      console.warn('Cannot connect: no session ID provided');
      return;
    }

    const url = getWebSocketUrl(sessionId);
    if (!url) {
      console.warn('Cannot connect: invalid WebSocket URL');
      return;
    }

    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    console.log(`Connecting to WebSocket: ${url}`);
    setReadyState('CONNECTING');

    try {
      const ws = new WebSocket(url);

      ws.onopen = (event) => {
        console.log('WebSocket connected:', sessionId);
        setReadyState('OPEN');
        setReconnectAttempts(0);
        startHeartbeat();

        if (onOpen) {
          onOpen(event);
        }
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          setLastMessage(message);

          if (onMessage) {
            onMessage(message);
          }

          // Handle pong response
          if (message.type === 'pong') {
            // Heartbeat acknowledged
            return;
          }

        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setReadyState('ERROR');

        if (onError) {
          onError(event);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setReadyState('CLOSED');
        stopHeartbeat();

        if (onClose) {
          onClose(event);
        }

        // Attempt reconnection if enabled
        if (shouldReconnectRef.current && reconnectAttempts < maxReconnectAttempts) {
          console.log(`Reconnecting in ${reconnectInterval}ms... (attempt ${reconnectAttempts + 1}/${maxReconnectAttempts})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts(prev => prev + 1);
            connect();
          }, reconnectInterval);
        } else if (reconnectAttempts >= maxReconnectAttempts) {
          console.error('Max reconnection attempts reached');
        }
      };

      wsRef.current = ws;

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setReadyState('ERROR');
    }
  }, [
    sessionId,
    getWebSocketUrl,
    reconnectAttempts,
    maxReconnectAttempts,
    reconnectInterval,
    startHeartbeat,
    stopHeartbeat,
    onOpen,
    onClose,
    onError,
    onMessage
  ]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    stopHeartbeat();

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setReadyState('CLOSED');
  }, [stopHeartbeat]);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect && sessionId) {
      shouldReconnectRef.current = true;
      connect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [sessionId, autoConnect, connect, disconnect]);

  return {
    lastMessage,
    sendMessage,
    readyState,
    connect,
    disconnect,
    isOpen: readyState === 'OPEN',
    isConnecting: readyState === 'CONNECTING',
    isClosed: readyState === 'CLOSED',
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
