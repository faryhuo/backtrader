/**
 * Unit tests for useStrategyParams hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useStrategyParams } from '../useStrategyParams'
import { api } from '../../services/api'

// Mock the api module
vi.mock('../../services/api', () => ({
    api: {
        getStrategyParams: vi.fn(),
        getStrategy: vi.fn()
    }
}))

describe('useStrategyParams', () => {
    const mockParams = [
        { name: 'period', value: 20, type: 'int' },
        { name: 'fast', value: 10, type: 'int' },
        { name: 'slow', value: 30, type: 'int' }
    ]

    const mockStrategyCode = 'class SMAStrategy: pass'

    beforeEach(() => {
        vi.clearAllMocks()
    })

    afterEach(() => {
        vi.restoreAllMocks()
    })

    describe('initial state', () => {
        it('should return default state when no strategy selected', () => {
            const { result } = renderHook(() =>
                useStrategyParams(null)
            )

            expect(result.current.strategyParams).toEqual([])
            expect(result.current.paramOverrides).toEqual({})
            expect(result.current.paramDefaults).toEqual({})
            expect(result.current.strategyCode).toBe('')
            expect(result.current.loading).toBe(false)
            expect(result.current.error).toBe(null)
        })

        it('should provide all required methods', () => {
            const { result } = renderHook(() =>
                useStrategyParams('SMA')
            )

            expect(typeof result.current.handleParamChange).toBe('function')
            expect(typeof result.current.resetParams).toBe('function')
            expect(typeof result.current.getParamsForApi).toBe('function')
            expect(typeof result.current.refresh).toBe('function')
        })
    })

    describe('fetching strategy params', () => {
        it('should fetch params when strategy is selected', async () => {
            api.getStrategyParams.mockResolvedValue({ params: mockParams })
            api.getStrategy.mockResolvedValue({ code: mockStrategyCode })

            const { result } = renderHook(() =>
                useStrategyParams('SMA_CrossOver')
            )

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(api.getStrategyParams).toHaveBeenCalledWith('SMA_CrossOver')
            expect(result.current.strategyParams).toEqual(mockParams)
            expect(result.current.paramDefaults).toEqual({
                period: 20,
                fast: 10,
                slow: 30
            })
        })

        it('should fetch strategy code when includeCode is true', async () => {
            api.getStrategyParams.mockResolvedValue({ params: mockParams })
            api.getStrategy.mockResolvedValue({ code: mockStrategyCode })

            const { result } = renderHook(() =>
                useStrategyParams('SMA_CrossOver', { includeCode: true })
            )

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(api.getStrategy).toHaveBeenCalledWith('SMA_CrossOver')
            expect(result.current.strategyCode).toBe(mockStrategyCode)
        })

        it('should not fetch strategy code when includeCode is false', async () => {
            api.getStrategyParams.mockResolvedValue({ params: mockParams })

            const { result } = renderHook(() =>
                useStrategyParams('SMA_CrossOver', { includeCode: false })
            )

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(api.getStrategy).not.toHaveBeenCalled()
            expect(result.current.strategyCode).toBe('')
        })

        it('should not fetch when enabled is false', async () => {
            const { result } = renderHook(() =>
                useStrategyParams('SMA_CrossOver', { enabled: false })
            )

            expect(api.getStrategyParams).not.toHaveBeenCalled()
            expect(result.current.strategyParams).toEqual([])
        })

        it('should handle API errors gracefully', async () => {
            const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => { })
            api.getStrategyParams.mockRejectedValue(new Error('Network error'))

            const { result } = renderHook(() =>
                useStrategyParams('SMA_CrossOver')
            )

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(result.current.error).toBeInstanceOf(Error)
            expect(result.current.strategyParams).toEqual([])
            consoleSpy.mockRestore()
        })
    })

    describe('initialOverrides', () => {
        it('should merge initialOverrides with defaults', async () => {
            api.getStrategyParams.mockResolvedValue({ params: mockParams })
            api.getStrategy.mockResolvedValue({ code: '' })

            const { result } = renderHook(() =>
                useStrategyParams('SMA', {
                    initialOverrides: { period: 50 }
                })
            )

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(result.current.paramOverrides.period).toBe(50)
            expect(result.current.paramOverrides.fast).toBe(10) // from defaults
        })
    })

    describe('handleParamChange', () => {
        it('should update param with integer coercion', async () => {
            api.getStrategyParams.mockResolvedValue({ params: mockParams })
            api.getStrategy.mockResolvedValue({ code: '' })

            const { result } = renderHook(() =>
                useStrategyParams('SMA')
            )

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            act(() => {
                result.current.handleParamChange('period', '25', 'int')
            })

            expect(result.current.paramOverrides.period).toBe(25)
        })

        it('should update param with float coercion', async () => {
            api.getStrategyParams.mockResolvedValue({ params: mockParams })
            api.getStrategy.mockResolvedValue({ code: '' })

            const { result } = renderHook(() =>
                useStrategyParams('SMA')
            )

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            act(() => {
                result.current.handleParamChange('threshold', '0.05', 'float')
            })

            expect(result.current.paramOverrides.threshold).toBe(0.05)
        })

        it('should keep string for other types', async () => {
            api.getStrategyParams.mockResolvedValue({ params: mockParams })
            api.getStrategy.mockResolvedValue({ code: '' })

            const { result } = renderHook(() =>
                useStrategyParams('SMA')
            )

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            act(() => {
                result.current.handleParamChange('name', 'test', 'string')
            })

            expect(result.current.paramOverrides.name).toBe('test')
        })
    })

    describe('resetParams', () => {
        it('should reset params to defaults', async () => {
            api.getStrategyParams.mockResolvedValue({ params: mockParams })
            api.getStrategy.mockResolvedValue({ code: '' })

            const { result } = renderHook(() =>
                useStrategyParams('SMA')
            )

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            act(() => {
                result.current.handleParamChange('period', '100', 'int')
            })

            expect(result.current.paramOverrides.period).toBe(100)

            act(() => {
                result.current.resetParams()
            })

            expect(result.current.paramOverrides.period).toBe(20)
        })
    })

    describe('getParamsForApi', () => {
        it('should return params object when overrides exist', async () => {
            api.getStrategyParams.mockResolvedValue({ params: mockParams })
            api.getStrategy.mockResolvedValue({ code: '' })

            const { result } = renderHook(() =>
                useStrategyParams('SMA')
            )

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            const params = result.current.getParamsForApi()
            expect(params).toEqual({
                period: 20,
                fast: 10,
                slow: 30
            })
        })

        it('should return null when no overrides', () => {
            const { result } = renderHook(() =>
                useStrategyParams(null)
            )

            expect(result.current.getParamsForApi()).toBe(null)
        })
    })

    describe('strategy change', () => {
        it('should refetch when strategy changes', async () => {
            api.getStrategyParams.mockResolvedValue({ params: mockParams })
            api.getStrategy.mockResolvedValue({ code: '' })

            const { result, rerender } = renderHook(
                ({ strategy }) => useStrategyParams(strategy),
                { initialProps: { strategy: 'SMA' } }
            )

            await waitFor(() => {
                expect(result.current.loading).toBe(false)
            })

            expect(api.getStrategyParams).toHaveBeenCalledWith('SMA')

            rerender({ strategy: 'MACD' })

            await waitFor(() => {
                expect(api.getStrategyParams).toHaveBeenCalledWith('MACD')
            })
        })
    })
})
