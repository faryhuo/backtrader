/**
 * Unit tests for useWebSocketBase hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useWebSocketBase, buildWebSocketUrl } from '../useWebSocketBase'

// Mock WebSocket
class MockWebSocket {
    static CONNECTING = 0
    static OPEN = 1
    static CLOSING = 2
    static CLOSED = 3

    constructor(url) {
        this.url = url
        this.readyState = MockWebSocket.CONNECTING
        this.onopen = null
        this.onclose = null
        this.onerror = null
        this.onmessage = null
        this.sentMessages = []
        MockWebSocket.instances.push(this)
    }

    send(data) {
        this.sentMessages.push(data)
    }

    close() {
        this.readyState = MockWebSocket.CLOSED
        if (this.onclose) {
            this.onclose({ code: 1000, reason: 'Normal closure' })
        }
    }

    // Test helpers
    simulateOpen() {
        this.readyState = MockWebSocket.OPEN
        if (this.onopen) {
            this.onopen({})
        }
    }

    simulateMessage(data) {
        if (this.onmessage) {
            this.onmessage({ data: JSON.stringify(data) })
        }
    }

    simulateError(error) {
        if (this.onerror) {
            this.onerror(error)
        }
    }

    simulateClose(code = 1000, reason = '') {
        this.readyState = MockWebSocket.CLOSED
        if (this.onclose) {
            this.onclose({ code, reason })
        }
    }
}

MockWebSocket.instances = []

describe('buildWebSocketUrl', () => {
    beforeEach(() => {
        // Mock import.meta.env
        vi.stubGlobal('import.meta', { env: { DEV: true } })
    })

    afterEach(() => {
        vi.unstubAllGlobals()
    })

    it('should build URL with ws protocol in development', () => {
        Object.defineProperty(window, 'location', {
            value: { protocol: 'http:', host: 'localhost:5173' },
            writable: true
        })

        const url = buildWebSocketUrl('/ws/tasks')
        expect(url).toContain('ws://')
        expect(url).toContain('/ws/tasks')
    })

    it('should build URL with wss protocol for https', () => {
        Object.defineProperty(window, 'location', {
            value: { protocol: 'https:', host: 'example.com' },
            writable: true
        })

        const url = buildWebSocketUrl('/ws/tasks')
        expect(url).toContain('wss://')
    })
})

describe('useWebSocketBase', () => {
    let originalWebSocket

    beforeEach(() => {
        vi.useFakeTimers()
        MockWebSocket.instances = []
        originalWebSocket = window.WebSocket
        window.WebSocket = MockWebSocket
    })

    afterEach(() => {
        vi.useRealTimers()
        vi.clearAllMocks()
        window.WebSocket = originalWebSocket
    })

    describe('initial state', () => {
        it('should have closed state initially', () => {
            const { result } = renderHook(() =>
                useWebSocketBase({
                    buildUrl: () => 'ws://test',
                    autoConnect: false
                })
            )

            expect(result.current.readyState).toBe('CLOSED')
            expect(result.current.isConnected).toBe(false)
            expect(result.current.lastMessage).toBe(null)
        })

        it('should provide all required methods', () => {
            const { result } = renderHook(() =>
                useWebSocketBase({
                    buildUrl: () => 'ws://test',
                    autoConnect: false
                })
            )

            expect(typeof result.current.connect).toBe('function')
            expect(typeof result.current.disconnect).toBe('function')
            expect(typeof result.current.sendMessage).toBe('function')
        })
    })

    describe('connection', () => {
        it('should connect when connect() is called', async () => {
            const { result } = renderHook(() =>
                useWebSocketBase({
                    buildUrl: () => 'ws://test',
                    autoConnect: false
                })
            )

            act(() => {
                result.current.connect()
            })

            expect(MockWebSocket.instances.length).toBe(1)
            expect(result.current.readyState).toBe('CONNECTING')
        })

        it('should update state when connection opens', async () => {
            const onOpen = vi.fn()
            const { result } = renderHook(() =>
                useWebSocketBase({
                    buildUrl: () => 'ws://test',
                    autoConnect: false,
                    onOpen
                })
            )

            act(() => {
                result.current.connect()
            })

            act(() => {
                MockWebSocket.instances[0].simulateOpen()
            })

            expect(result.current.readyState).toBe('OPEN')
            expect(result.current.isConnected).toBe(true)
            expect(onOpen).toHaveBeenCalled()
        })

        it('should not connect if buildUrl returns null', () => {
            const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => { })
            const { result } = renderHook(() =>
                useWebSocketBase({
                    buildUrl: () => null,
                    autoConnect: false
                })
            )

            act(() => {
                result.current.connect()
            })

            expect(MockWebSocket.instances.length).toBe(0)
            expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('buildUrl returned null'))
            consoleSpy.mockRestore()
        })
    })

    describe('messages', () => {
        it('should handle incoming messages', async () => {
            const onMessage = vi.fn()
            const { result } = renderHook(() =>
                useWebSocketBase({
                    buildUrl: () => 'ws://test',
                    autoConnect: false,
                    onMessage
                })
            )

            act(() => {
                result.current.connect()
                MockWebSocket.instances[0].simulateOpen()
            })

            act(() => {
                MockWebSocket.instances[0].simulateMessage({ type: 'test', data: 'hello' })
            })

            expect(result.current.lastMessage).toEqual({ type: 'test', data: 'hello' })
            expect(onMessage).toHaveBeenCalledWith({ type: 'test', data: 'hello' })
        })

        it('should not call onMessage for pong messages', async () => {
            const onMessage = vi.fn()
            const { result } = renderHook(() =>
                useWebSocketBase({
                    buildUrl: () => 'ws://test',
                    autoConnect: false,
                    onMessage
                })
            )

            act(() => {
                result.current.connect()
                MockWebSocket.instances[0].simulateOpen()
            })

            act(() => {
                MockWebSocket.instances[0].simulateMessage({ type: 'pong' })
            })

            expect(onMessage).not.toHaveBeenCalled()
        })

        it('should send messages when connected', () => {
            const { result } = renderHook(() =>
                useWebSocketBase({
                    buildUrl: () => 'ws://test',
                    autoConnect: false
                })
            )

            act(() => {
                result.current.connect()
                MockWebSocket.instances[0].simulateOpen()
            })

            act(() => {
                result.current.sendMessage({ type: 'test' })
            })

            expect(MockWebSocket.instances[0].sentMessages).toContain('{"type":"test"}')
        })
    })

    describe('heartbeat', () => {
        it('should send ping at heartbeat interval', async () => {
            const { result } = renderHook(() =>
                useWebSocketBase({
                    buildUrl: () => 'ws://test',
                    autoConnect: false,
                    heartbeatInterval: 1000
                })
            )

            act(() => {
                result.current.connect()
                MockWebSocket.instances[0].simulateOpen()
            })

            act(() => {
                vi.advanceTimersByTime(1000)
            })

            expect(MockWebSocket.instances[0].sentMessages).toContain('{"type":"ping"}')
        })
    })

    describe('disconnect', () => {
        it('should close connection on disconnect', () => {
            const { result } = renderHook(() =>
                useWebSocketBase({
                    buildUrl: () => 'ws://test',
                    autoConnect: false
                })
            )

            act(() => {
                result.current.connect()
                MockWebSocket.instances[0].simulateOpen()
            })

            act(() => {
                result.current.disconnect()
            })

            expect(result.current.readyState).toBe('CLOSED')
            expect(result.current.isConnected).toBe(false)
        })
    })
})
