/**
 * useWebSocketBase - Generic WebSocket hook with reconnection and heartbeat.
 *
 * Provides a reusable base for WebSocket connections with:
 * - Auto-reconnection with configurable retry policy
 * - Heartbeat ping/pong for keep-alive
 * - Connection lifecycle callbacks
 */

import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * Build WebSocket URL based on current environment.
 *
 * @param {string} path - WebSocket path (e.g., '/ws/tasks' or '/ws/live/session-id')
 * @returns {string} Full WebSocket URL
 */
export function buildWebSocketUrl(path) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const isDevelopment = import.meta.env.DEV;
    const host = isDevelopment ? 'localhost:8000' : window.location.host;
    return `${protocol}//${host}${path}`;
}

/**
 * Generic WebSocket hook with reconnection and heartbeat support.
 *
 * @param {Object} options - Configuration options
 * @param {function} options.buildUrl - Function that returns WebSocket URL, or null to skip connection
 * @param {boolean} options.autoConnect - Auto-connect on mount (default: true)
 * @param {number} options.reconnectInterval - Reconnect delay in ms (default: 3000)
 * @param {number} options.maxReconnectAttempts - Max reconnect attempts (default: 5)
 * @param {number} options.heartbeatInterval - Heartbeat interval in ms (default: 30000)
 * @param {function} options.onOpen - Callback when connection opens
 * @param {function} options.onClose - Callback when connection closes
 * @param {function} options.onError - Callback when error occurs
 * @param {function} options.onMessage - Callback for parsed messages (excludes pong)
 * @returns {Object} WebSocket state and methods
 */
export function useWebSocketBase(options = {}) {
    const {
        buildUrl,
        autoConnect = true,
        reconnectInterval = 3000,
        maxReconnectAttempts = 5,
        heartbeatInterval = 30000,
        onOpen = null,
        onClose = null,
        onError = null,
        onMessage = null,
    } = options;

    const [readyState, setReadyState] = useState('CLOSED');
    const [lastMessage, setLastMessage] = useState(null);
    const [reconnectAttempts, setReconnectAttempts] = useState(0);

    const wsRef = useRef(null);
    const heartbeatRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const shouldReconnectRef = useRef(true);

    // Stable reference for callbacks
    const onOpenRef = useRef(onOpen);
    const onCloseRef = useRef(onClose);
    const onErrorRef = useRef(onError);
    const onMessageRef = useRef(onMessage);
    const buildUrlRef = useRef(buildUrl);

    // Update refs when callbacks change
    useEffect(() => {
        onOpenRef.current = onOpen;
        onCloseRef.current = onClose;
        onErrorRef.current = onError;
        onMessageRef.current = onMessage;
        buildUrlRef.current = buildUrl;
    }, [onOpen, onClose, onError, onMessage, buildUrl]);

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
        heartbeatRef.current = setInterval(sendPing, heartbeatInterval);
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
        const url = buildUrlRef.current?.();

        if (!url) {
            console.warn('Cannot connect: buildUrl returned null or undefined');
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
                console.log('WebSocket connected');
                setReadyState('OPEN');
                setReconnectAttempts(0);
                startHeartbeat();
                onOpenRef.current?.(event);
            };

            ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    setLastMessage(message);

                    // Handle pong response silently
                    if (message.type === 'pong') {
                        return;
                    }

                    onMessageRef.current?.(message);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };

            ws.onerror = (event) => {
                console.error('WebSocket error:', event);
                setReadyState('ERROR');
                onErrorRef.current?.(event);
            };

            ws.onclose = (event) => {
                console.log('WebSocket closed:', event.code, event.reason);
                setReadyState('CLOSED');
                stopHeartbeat();
                onCloseRef.current?.(event);

                // Attempt reconnection if enabled
                if (shouldReconnectRef.current) {
                    setReconnectAttempts(prev => {
                        if (prev < maxReconnectAttempts) {
                            console.log(`Reconnecting in ${reconnectInterval}ms... (attempt ${prev + 1}/${maxReconnectAttempts})`);
                            reconnectTimeoutRef.current = setTimeout(() => {
                                connect();
                            }, reconnectInterval);
                            return prev + 1;
                        } else {
                            console.error('Max reconnection attempts reached');
                            return prev;
                        }
                    });
                }
            };

            wsRef.current = ws;
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            setReadyState('ERROR');
        }
    }, [startHeartbeat, stopHeartbeat, reconnectInterval, maxReconnectAttempts]);

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

    // Reset reconnect attempts (useful when manually reconnecting)
    const resetReconnect = useCallback(() => {
        shouldReconnectRef.current = true;
        setReconnectAttempts(0);
    }, []);

    // Auto-connect on mount if enabled
    useEffect(() => {
        if (autoConnect && buildUrlRef.current?.()) {
            shouldReconnectRef.current = true;
            connect();
        }

        // Cleanup on unmount
        return () => {
            disconnect();
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [autoConnect]);

    return {
        // State
        readyState,
        lastMessage,
        reconnectAttempts,

        // Computed state
        isOpen: readyState === 'OPEN',
        isConnecting: readyState === 'CONNECTING',
        isClosed: readyState === 'CLOSED',
        isConnected: readyState === 'OPEN',

        // Methods
        connect,
        disconnect,
        sendMessage,
        resetReconnect,
    };
}

export default useWebSocketBase;
