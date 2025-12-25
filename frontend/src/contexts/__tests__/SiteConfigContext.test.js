/**
 * Unit tests for SiteConfigContext
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { SiteConfigProvider, useSiteConfig } from '../SiteConfigContext'

// Mock the siteApi module
vi.mock('../../services/siteApi', () => ({
    getSiteConfig: vi.fn()
}))

// Import after mocking
import { getSiteConfig } from '../../services/siteApi'

describe('SiteConfigContext', () => {
    const defaultConfig = {
        site: {
            title: 'Backtrader Pro',
            description: 'Professional quantitative trading platform'
        },
        links: {
            docs: '',
            github: '',
            twitter: '',
            email: ''
        },
        stats: {
            strategies: '50+',
            backtests: '10K+',
            users: '1K+'
        },
        features: {
            loginEnabled: false,
            liveTrading: false
        }
    }

    const customConfig = {
        site: {
            title: 'Custom Trading Platform',
            description: 'Custom description'
        },
        links: {
            docs: 'https://docs.example.com',
            github: 'https://github.com/example',
            twitter: 'https://twitter.com/example',
            email: 'support@example.com'
        },
        stats: {
            strategies: '100+',
            backtests: '50K+',
            users: '5K+'
        },
        features: {
            loginEnabled: true,
            liveTrading: true
        }
    }

    const wrapper = ({ children }) => (
        <SiteConfigProvider>{children}</SiteConfigProvider>
    )

    beforeEach(() => {
        vi.clearAllMocks()
    })

    afterEach(() => {
        vi.restoreAllMocks()
    })

    describe('initial state', () => {
        it('should start with default config and loading state', () => {
            getSiteConfig.mockImplementation(() => new Promise(() => { })) // Never resolves

            const { result } = renderHook(() => useSiteConfig(), { wrapper })

            expect(result.current.config).toEqual(defaultConfig)
            expect(result.current.loading).toBe(true)
        })
    })

    describe('successful config loading', () => {
        it('should load config from API successfully', async () => {
            getSiteConfig.mockResolvedValue(customConfig)

            const { result } = renderHook(() => useSiteConfig(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(result.current.config).toEqual(customConfig)
            expect(getSiteConfig).toHaveBeenCalledTimes(1)
        })

        it('should update loading state correctly', async () => {
            getSiteConfig.mockResolvedValue(customConfig)

            const { result } = renderHook(() => useSiteConfig(), { wrapper })

            expect(result.current.loading).toBe(true)

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })
        })
    })

    describe('error handling', () => {
        it('should keep default config when API fails', async () => {
            const consoleError = vi.spyOn(console, 'error').mockImplementation(() => { })
            getSiteConfig.mockRejectedValue(new Error('API Error'))

            const { result } = renderHook(() => useSiteConfig(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(result.current.config).toEqual(defaultConfig)
            expect(getSiteConfig).toHaveBeenCalledTimes(1)

            consoleError.mockRestore()
        })

        it('should handle network errors gracefully', async () => {
            const consoleError = vi.spyOn(console, 'error').mockImplementation(() => { })
            getSiteConfig.mockRejectedValue(new Error('Network error'))

            const { result } = renderHook(() => useSiteConfig(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(result.current.loading).toBe(false)
            expect(result.current.config).toEqual(defaultConfig)

            consoleError.mockRestore()
        })
    })

    describe('component lifecycle', () => {
        it('should cleanup on unmount', async () => {
            let resolvePromise
            const promise = new Promise(resolve => {
                resolvePromise = resolve
            })
            getSiteConfig.mockReturnValue(promise)

            const { unmount } = renderHook(() => useSiteConfig(), { wrapper })

            // Unmount before promise resolves
            unmount()

            // Resolve after unmount - should not update state
            resolvePromise(customConfig)

            // If state update happens after unmount, it would cause a warning/error
            // This test verifies cleanup works correctly
            await new Promise(resolve => setTimeout(resolve, 10))
        })

        it('should not update state if unmounted before API response', async () => {
            const consoleError = vi.spyOn(console, 'error').mockImplementation(() => { })

            let resolvePromise
            getSiteConfig.mockImplementation(() => {
                return new Promise(resolve => {
                    resolvePromise = resolve
                })
            })

            const { result, unmount } = renderHook(() => useSiteConfig(), { wrapper })

            expect(result.current.loading).toBe(true)

            unmount()

            // Resolve after unmount
            resolvePromise(customConfig)

            await new Promise(resolve => setTimeout(resolve, 10))

            // No errors should be logged about setting state on unmounted component
            expect(consoleError).not.toHaveBeenCalled()

            consoleError.mockRestore()
        })
    })

    describe('useSiteConfig hook outside provider', () => {
        it('should return default config when used outside provider', () => {
            const { result } = renderHook(() => useSiteConfig())

            expect(result.current.config).toEqual(defaultConfig)
            expect(result.current.loading).toBe(false)
        })

        it('should not attempt API call when used outside provider', () => {
            renderHook(() => useSiteConfig())

            expect(getSiteConfig).not.toHaveBeenCalled()
        })
    })

    describe('config structure validation', () => {
        it('should contain all expected top-level keys', async () => {
            getSiteConfig.mockResolvedValue(customConfig)

            const { result } = renderHook(() => useSiteConfig(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(result.current.config).toHaveProperty('site')
            expect(result.current.config).toHaveProperty('links')
            expect(result.current.config).toHaveProperty('stats')
            expect(result.current.config).toHaveProperty('features')
        })

        it('should have correct site configuration structure', async () => {
            siteApi.getSiteConfig.mockResolvedValue(customConfig)

            const { result } = renderHook(() => useSiteConfig(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(result.current.config.site).toHaveProperty('title')
            expect(result.current.config.site).toHaveProperty('description')
        })

        it('should have correct links structure', async () => {
            siteApi.getSiteConfig.mockResolvedValue(customConfig)

            const { result } = renderHook(() => useSiteConfig(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(result.current.config.links).toHaveProperty('docs')
            expect(result.current.config.links).toHaveProperty('github')
            expect(result.current.config.links).toHaveProperty('twitter')
            expect(result.current.config.links).toHaveProperty('email')
        })

        it('should have correct features flags', async () => {
            siteApi.getSiteConfig.mockResolvedValue(customConfig)

            const { result } = renderHook(() => useSiteConfig(), { wrapper })

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(result.current.config.features).toHaveProperty('loginEnabled')
            expect(result.current.config.features).toHaveProperty('liveTrading')
            expect(typeof result.current.config.features.loginEnabled).toBe('boolean')
            expect(typeof result.current.config.features.liveTrading).toBe('boolean')
        })
    })
})
