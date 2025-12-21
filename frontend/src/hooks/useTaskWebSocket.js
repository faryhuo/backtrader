/**
 * useTaskWebSocket - Hook for real-time task updates via WebSocket.
 *
 * Connects to /ws/tasks endpoint and provides real-time updates
 * for task status changes.
 */

import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * WebSocket hook for task updates.
 *
 * @param {Object} options - Configuration options
 * @param {boolean} options.autoConnect - Auto-connect on mount (default: true)
 * @param {number} options.reconnectInterval - Reconnect delay in ms (default: 3000)
 * @param {number} options.maxReconnectAttempts - Max reconnect attempts (default: 5)
 * @param {function} options.onTaskUpdate - Callback for task updates
 * @param {function} options.onError - Callback for errors
 * @returns {Object} WebSocket state and methods
 */
export function useTaskWebSocket(options = {}) {
    const {
        autoConnect = true,
        reconnectInterval = 3000,
        maxReconnectAttempts = 5,
        heartbeatInterval = 30000,
        onTaskUpdate = null,
        onError = null,
    } = options;

    const [isConnected, setIsConnected] = useState(false);
    const [lastMessage, setLastMessage] = useState(null);
    const [reconnectAttempts, setReconnectAttempts] = useState(0);

    const wsRef = useRef(null);
    const heartbeatRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const shouldReconnectRef = useRef(true);

    // Get WebSocket URL
    const getWebSocketUrl = useCallback(() => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const isDevelopment = import.meta.env.DEV;
        const host = isDevelopment ? 'localhost:8000' : window.location.host;
        return `${protocol}//${host}/ws/tasks`;
    }, []);

    // Send ping for keep-alive
    const sendPing = useCallback(() => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'ping' }));
        }
    }, []);

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
        const url = getWebSocketUrl();

        if (wsRef.current) {
            wsRef.current.close();
        }

        console.log(`Connecting to task WebSocket: ${url}`);

        try {
            const ws = new WebSocket(url);

            ws.onopen = () => {
                console.log('Task WebSocket connected');
                setIsConnected(true);
                setReconnectAttempts(0);
                startHeartbeat();
            };

            ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    setLastMessage(message);

                    // Handle pong response
                    if (message.type === 'pong') {
                        return;
                    }

                    // Handle task events
                    if (message.type && message.type.startsWith('task_')) {
                        if (onTaskUpdate) {
                            onTaskUpdate(message);
                        }
                    }
                } catch (error) {
                    console.error('Failed to parse task WebSocket message:', error);
                }
            };

            ws.onerror = (event) => {
                console.error('Task WebSocket error:', event);
                if (onError) {
                    onError(event);
                }
            };

            ws.onclose = (event) => {
                console.log('Task WebSocket closed:', event.code, event.reason);
                setIsConnected(false);
                stopHeartbeat();

                // Attempt reconnection
                if (shouldReconnectRef.current && reconnectAttempts < maxReconnectAttempts) {
                    console.log(`Reconnecting in ${reconnectInterval}ms... (attempt ${reconnectAttempts + 1}/${maxReconnectAttempts})`);
                    reconnectTimeoutRef.current = setTimeout(() => {
                        setReconnectAttempts(prev => prev + 1);
                        connect();
                    }, reconnectInterval);
                }
            };

            wsRef.current = ws;
        } catch (error) {
            console.error('Failed to create task WebSocket connection:', error);
        }
    }, [
        getWebSocketUrl,
        reconnectAttempts,
        maxReconnectAttempts,
        reconnectInterval,
        startHeartbeat,
        stopHeartbeat,
        onTaskUpdate,
        onError,
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

        setIsConnected(false);
    }, [stopHeartbeat]);

    // Auto-connect on mount
    useEffect(() => {
        if (autoConnect) {
            shouldReconnectRef.current = true;
            connect();
        }

        return () => {
            disconnect();
        };
    }, [autoConnect, connect, disconnect]);

    return {
        isConnected,
        lastMessage,
        connect,
        disconnect,
        reconnectAttempts,
    };
}

/**
 * Task event type constants
 */
export const TASK_EVENT_TYPES = {
    CREATED: 'task_created',
    STARTED: 'task_started',
    PROGRESS: 'task_progress',
    COMPLETED: 'task_completed',
    FAILED: 'task_failed',
    CANCELLED: 'task_cancelled',
};

export default useTaskWebSocket;
