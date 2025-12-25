/**
 * useTaskWebSocket - Hook for real-time task updates via WebSocket.
 *
 * Connects to /ws/tasks endpoint and provides real-time updates
 * for task status changes.
 *
 * Uses useWebSocketBase for connection management.
 */

import { useCallback } from 'react';
import { useWebSocketBase, buildWebSocketUrl } from './useWebSocketBase';

/**
 * WebSocket hook for task updates.
 *
 * @param {Object} options - Configuration options
 * @param {boolean} options.autoConnect - Auto-connect on mount (default: true)
 * @param {number} options.reconnectInterval - Reconnect delay in ms (default: 3000)
 * @param {number} options.maxReconnectAttempts - Max reconnect attempts (default: 5)
 * @param {number} options.heartbeatInterval - Heartbeat interval in ms (default: 30000)
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

    // Build task WebSocket URL
    const buildUrl = useCallback(() => {
        return buildWebSocketUrl('/ws/tasks');
    }, []);

    // Handle incoming messages
    const handleMessage = useCallback((message) => {
        // Handle task events
        if (message.type && message.type.startsWith('task_')) {
            onTaskUpdate?.(message);
        }
    }, [onTaskUpdate]);

    // Use the base WebSocket hook
    const {
        readyState,
        lastMessage,
        reconnectAttempts,
        isConnected,
        connect,
        disconnect,
        sendMessage,
    } = useWebSocketBase({
        buildUrl,
        autoConnect,
        reconnectInterval,
        maxReconnectAttempts,
        heartbeatInterval,
        onError,
        onMessage: handleMessage,
    });

    return {
        isConnected,
        lastMessage,
        connect,
        disconnect,
        sendMessage,
        reconnectAttempts,
        readyState,
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
