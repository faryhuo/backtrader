/**
 * Unit tests for LogtoConfigContext
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { LogtoConfigProvider, useLogtoConfig } from '../LogtoConfigContext'

// Mock the settingsApi module
vi.mock('../../services/settingsApi', () => ({
    settingsApi: {
        getLogtoConfig: vi.fn()
    }
}))

// Import after mocking
import { settingsApi } from '../../services/settingsApi'

describe('LogtoConfigContext', () => {
    const mockConfig = {
        status: 'ok',
        config: {
            endpoint: 'https://logto.example.com',
            appId: 'test-app-id',
            redirectUri: 'http://localhost:5173/callback',
            postLogoutRedirectUri: 'http://localhost:5173',
            enableLogin: true
        }
    }

    const disabledConfig = {
        endpoint: null,
        appId: null,
        redirectUri: null,
        postLogoutRedirectUri: null,
        enableLogin: false
    }

    const wrapper = ({ children }) => (
        <LogtoConfigProvider>{children}</LogtoConfigProvider>
    )

    beforeEach(() => {
        vi.clearAllMocks()
    })

    afterEach(() => {
        vi.restoreAllMocks()
    })

    describe('initial state', () => {
        it('should start with loading state', () => {
            settingsApi.getLogtoConfig.mockImplementation(() => new Promise(() => { }))

            const { result } = renderHook(() => useLogtoConfig(), { wrapper })

            expect(result.current.loading).toBe(true)
            expect(result.current.config).toBeNull()
            expect(result.current.error).toBeNull()
        })
    })

    describe('successful config loading', () => {
        it('should load config from API successfully', async () => {
            settingsApi.getLogtoConfig.mockResolvedValue(mockConfig)

            const { result } = renderHook(() => useLogtoConfig(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(result.current.config).toEqual(mockConfig.config)
            expect(result.current.error).toBeNull()
            expect(settingsApi.getLogtoConfig).toHaveBeenCalledTimes(1)
        })

        it('should handle config with all fields populated', async () => {
            settingsApi.getLogtoConfig.mockResolvedValue(mockConfig)

            const { result } = renderHook(() => useLogtoConfig(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(result.current.config.endpoint).toBe('https://logto.example.com')
            expect(result.current.config.appId).toBe('test-app-id')
            expect(result.current.config.redirectUri).toBe('http://localhost:5173/callback')
            expect(result.current.config.postLogoutRedirectUri).toBe('http://localhost:5173')
            expect(result.current.config.enableLogin).toBe(true)
        })
    })

    describe('error handling', () => {
        it('should handle API error and set default disabled config', async () => {
            const consoleError = vi.spyOn(console, 'error').mockImplementation(() => { })
            settingsApi.getLogtoConfig.mockRejectedValue(new Error('API Error'))

            const { result } = renderHook(() => useLogtoConfig(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(result.current.config).toEqual(disabledConfig)
            expect(result.current.error).toBeInstanceOf(Error)
            expect(result.current.error.message).toBe('API Error')

            consoleError.mockRestore()
        })

        it('should handle response with invalid status', async () => {
            const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => { })
            settingsApi.getLogtoConfig.mockResolvedValue({ status: 'error' })

            const { result } = renderHook(() => useLogtoConfig(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(result.current.config).toEqual(disabledConfig)
            expect(result.current.error).toBeInstanceOf(Error)
            expect(consoleWarn).toHaveBeenCalledWith(expect.stringContaining('Failed to fetch Logto config'))

            consoleWarn.mockRestore()
        })
    })

    describe('useLogtoConfig hook error handling', () => {
        it('should throw error when used outside provider', () => {
            const consoleError = vi.spyOn(console, 'error').mockImplementation(() => { })

            expect(() => {
                renderHook(() => useLogtoConfig())
            }).toThrow('useLogtoConfig must be used within LogtoConfigProvider')

            consoleError.mockRestore()
        })
    })
})
