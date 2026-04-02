/**
 * Unit tests for NotificationProvider
 */
import { describe, it, expect, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { NotificationProvider, useHeaderNotification } from '../NotificationProvider'

describe('NotificationProvider', () => {
    const wrapper = ({ children }) => (
        <NotificationProvider>{children}</NotificationProvider>
    )

    describe('initial state', () => {
        it('should have empty notifications and zero unread count', () => {
            const { result } = renderHook(() => useHeaderNotification(), { wrapper })

            expect(result.current.notifications).toEqual([])
            expect(result.current.unreadCount).toBe(0)
        })

        it('should provide all required methods', () => {
            const { result } = renderHook(() => useHeaderNotification(), { wrapper })

            expect(typeof result.current.addNotification).toBe('function')
            expect(typeof result.current.markAsRead).toBe('function')
            expect(typeof result.current.markAllAsRead).toBe('function')
            expect(typeof result.current.clearAll).toBe('function')
        })
    })

    describe('addNotification', () => {
        it('should add a notification with default type', () => {
            const { result } = renderHook(() => useHeaderNotification(), { wrapper })

            act(() => {
                result.current.addNotification('Test message')
            })

            expect(result.current.notifications).toHaveLength(1)
            expect(result.current.notifications[0]).toMatchObject({
                message: 'Test message',
                type: 'info',
                read: false
            })
            expect(result.current.notifications[0].id).toBeDefined()
            expect(result.current.notifications[0].timestamp).toBeInstanceOf(Date)
            expect(result.current.unreadCount).toBe(1)
        })

        it('should add notification with specified type', () => {
            const { result } = renderHook(() => useHeaderNotification(), { wrapper })

            act(() => {
                result.current.addNotification('Error occurred', 'error')
            })

            expect(result.current.notifications[0]).toMatchObject({
                message: 'Error occurred',
                type: 'error'
            })
        })

        it('should add multiple notifications in correct order (newest first)', () => {
            const { result } = renderHook(() => useHeaderNotification(), { wrapper })

            act(() => {
                result.current.addNotification('First message')
            })

            act(() => {
                result.current.addNotification('Second message')
            })

            act(() => {
                result.current.addNotification('Third message')
            })

            expect(result.current.notifications).toHaveLength(3)
            expect(result.current.notifications[0].message).toBe('Third message')
            expect(result.current.notifications[1].message).toBe('Second message')
            expect(result.current.notifications[2].message).toBe('First message')
            expect(result.current.unreadCount).toBe(3)
        })

        it('should generate unique IDs for each notification', () => {
            const { result } = renderHook(() => useHeaderNotification(), { wrapper })

            act(() => {
                result.current.addNotification('First')
                result.current.addNotification('Second')
            })

            const ids = result.current.notifications.map(n => n.id)
            expect(new Set(ids).size).toBe(2) // All IDs should be unique
        })

        it('should support different notification types', () => {
            const { result } = renderHook(() => useHeaderNotification(), { wrapper })

            const types = ['info', 'success', 'warning', 'error']

            act(() => {
                types.forEach(type => {
                    result.current.addNotification(`${type} message`, type)
                })
            })

            expect(result.current.notifications).toHaveLength(4)
            types.reverse().forEach((type, index) => {
                expect(result.current.notifications[index].type).toBe(type)
            })
        })
    })

    describe('markAsRead', () => {
        it('should mark a notification as read', () => {
            const { result } = renderHook(() => useHeaderNotification(), { wrapper })

            let notificationId

            act(() => {
                result.current.addNotification('Test message')
                notificationId = result.current.notifications[0].id
            })

            expect(result.current.unreadCount).toBe(1)

            act(() => {
                result.current.markAsRead(notificationId)
            })

            expect(result.current.notifications[0].read).toBe(true)
            expect(result.current.unreadCount).toBe(0)
        })

        it('should only mark the specific notification', () => {
            const { result } = renderHook(() => useHeaderNotification(), { wrapper })

            let secondId

            act(() => {
                result.current.addNotification('First')
                result.current.addNotification('Second')
                result.current.addNotification('Third')
                secondId = result.current.notifications[1].id
            })

            act(() => {
                result.current.markAsRead(secondId)
            })

            expect(result.current.notifications[0].read).toBe(false)
            expect(result.current.notifications[1].read).toBe(true)
            expect(result.current.notifications[2].read).toBe(false)
            expect(result.current.unreadCount).toBe(2)
        })

        it('should not decrease unread count below zero', () => {
            const { result } = renderHook(() => useHeaderNotification(), { wrapper })

            let notificationId

            act(() => {
                result.current.addNotification('Test')
                notificationId = result.current.notifications[0].id
            })

            act(() => {
                result.current.markAsRead(notificationId)
            })

            expect(result.current.unreadCount).toBe(0)

            // Mark as read again
            act(() => {
                result.current.markAsRead(notificationId)
            })

            expect(result.current.unreadCount).toBe(0) // Should not go negative
        })

        it('should handle marking non-existent notification', () => {
            const { result } = renderHook(() => useHeaderNotification(), { wrapper })

            act(() => {
                result.current.addNotification('Test')
            })

            // Should not throw error
            act(() => {
                result.current.markAsRead(999999)
            })

            expect(result.current.notifications[0].read).toBe(false)
            expect(result.current.unreadCount).toBe(1)
        })
    })

    describe('markAllAsRead', () => {
        it('should mark all notifications as read', () => {
            const { result } = renderHook(() => useHeaderNotification(), { wrapper })

            act(() => {
                result.current.addNotification('First')
                result.current.addNotification('Second')
                result.current.addNotification('Third')
            })

            expect(result.current.unreadCount).toBe(3)

            act(() => {
                result.current.markAllAsRead()
            })

            expect(result.current.notifications.every(n => n.read)).toBe(true)
            expect(result.current.unreadCount).toBe(0)
        })

        it('should work with empty notifications', () => {
            const { result } = renderHook(() => useHeaderNotification(), { wrapper })

            act(() => {
                result.current.markAllAsRead()
            })

            expect(result.current.notifications).toEqual([])
            expect(result.current.unreadCount).toBe(0)
        })

        it('should work when some notifications are already read', () => {
            const { result } = renderHook(() => useHeaderNotification(), { wrapper })

            let firstId

            act(() => {
                result.current.addNotification('First')
                result.current.addNotification('Second')
                result.current.addNotification('Third')
                firstId = result.current.notifications[0].id
            })

            act(() => {
                result.current.markAsRead(firstId)
            })

            expect(result.current.unreadCount).toBe(2)

            act(() => {
                result.current.markAllAsRead()
            })

            expect(result.current.notifications.every(n => n.read)).toBe(true)
            expect(result.current.unreadCount).toBe(0)
        })
    })

    describe('clearAll', () => {
        it('should clear all notifications', () => {
            const { result } = renderHook(() => useHeaderNotification(), { wrapper })

            act(() => {
                result.current.addNotification('First')
                result.current.addNotification('Second')
                result.current.addNotification('Third')
            })

            expect(result.current.notifications).toHaveLength(3)
            expect(result.current.unreadCount).toBe(3)

            act(() => {
                result.current.clearAll()
            })

            expect(result.current.notifications).toEqual([])
            expect(result.current.unreadCount).toBe(0)
        })

        it('should work with empty notifications', () => {
            const { result } = renderHook(() => useHeaderNotification(), { wrapper })

            act(() => {
                result.current.clearAll()
            })

            expect(result.current.notifications).toEqual([])
            expect(result.current.unreadCount).toBe(0)
        })

        it('should reset state after clearing', () => {
            const { result } = renderHook(() => useHeaderNotification(), { wrapper })

            act(() => {
                result.current.addNotification('Test')
                result.current.clearAll()
            })

            // Add notification after clearing
            act(() => {
                result.current.addNotification('New message')
            })

            expect(result.current.notifications).toHaveLength(1)
            expect(result.current.unreadCount).toBe(1)
        })
    })

    describe('useHeaderNotification hook error handling', () => {
        it('should throw error when used outside provider', () => {
            // Suppress console.error for this test
            const consoleError = vi.spyOn(console, 'error').mockImplementation(() => { })

            expect(() => {
                renderHook(() => useHeaderNotification())
            }).toThrow('useHeaderNotification must be used within a NotificationProvider')

            consoleError.mockRestore()
        })
    })
})
