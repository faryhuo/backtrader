/**
 * Unit tests for useBacktest hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useBacktest } from '../useBacktest'
import { api } from '../../services/api'
import { taskApi } from '../../services/taskApi'

// Mock the api module
vi.mock('../../services/api', () => ({
    api: {
        runBacktest: vi.fn(),
        runPortfolioBacktest: vi.fn(),
        getBacktestDetail: vi.fn(),
        getPortfolioDetail: vi.fn()
    }
}))

// Mock the taskApi module
vi.mock('../../services/taskApi', () => ({
    taskApi: {
        getTask: vi.fn()
    }
}))

describe('useBacktest', () => {
    const mockT = (key) => key

    beforeEach(() => {
        vi.clearAllMocks()
        vi.useFakeTimers()
    })

    afterEach(() => {
        vi.useRealTimers()
        vi.restoreAllMocks()
    })

    describe('initial state', () => {
        it('should return default state', () => {
            const { result } = renderHook(() => useBacktest())

            expect(result.current.result).toBe(null)
            expect(result.current.loading).toBe(false)
            expect(result.current.error).toBe(null)
            expect(result.current.taskProgress).toBe(null)
        })

        it('should provide all required methods', () => {
            const { result } = renderHook(() => useBacktest())

            expect(typeof result.current.runBacktest).toBe('function')
            expect(typeof result.current.runPortfolioBacktest).toBe('function')
            expect(typeof result.current.clearResult).toBe('function')
            expect(typeof result.current.setResult).toBe('function')
            expect(typeof result.current.setError).toBe('function')
        })
    })

    describe('runBacktest', () => {
        it('should return null if no strategy selected', async () => {
            const { result } = renderHook(() => useBacktest())

            let returnValue
            await act(async () => {
                returnValue = await result.current.runBacktest(
                    { selectedStrategy: null },
                    mockT
                )
            })

            expect(returnValue).toBe(null)
            expect(result.current.error).toBeTruthy()
        })

        it('should handle legacy synchronous response', async () => {
            const mockResult = {
                backtest_id: 'test-123',
                metrics: { pnl: 1000 }
            }
            api.runBacktest.mockResolvedValue(mockResult)

            const { result } = renderHook(() => useBacktest())

            await act(async () => {
                await result.current.runBacktest({
                    ticker: 'AAPL',
                    startDate: '2023-01-01',
                    endDate: '2023-12-31',
                    initialCash: '100000',
                    commission: '0.001',
                    stake: '100',
                    selectedStrategy: 'SMA',
                    paramOverrides: { period: 20 }
                }, mockT)
            })

            expect(api.runBacktest).toHaveBeenCalledWith({
                ticker: 'AAPL',
                start_date: '2023-01-01',
                end_date: '2023-12-31',
                initial_cash: 100000,
                commission: 0.001,
                stake: 100,
                strategy_name: 'SMA',
                params: { period: 20 }
            })
            expect(result.current.result).toEqual(mockResult)
            expect(result.current.loading).toBe(false)
        })

        it('should handle async task-based response', async () => {
            vi.useRealTimers() // Use real timers for this test

            const mockTaskResponse = { task_id: 'task-123', name: 'Backtest AAPL' }
            const mockBacktestResult = { backtest_id: 'bt-456', metrics: { pnl: 500 } }

            api.runBacktest.mockResolvedValue(mockTaskResponse)
            taskApi.getTask
                .mockResolvedValueOnce({ status: 'completed', result_id: 'bt-456' })
            api.getBacktestDetail.mockResolvedValue(mockBacktestResult)

            const { result } = renderHook(() => useBacktest())

            await act(async () => {
                await result.current.runBacktest({
                    ticker: 'AAPL',
                    startDate: '2023-01-01',
                    endDate: '2023-12-31',
                    initialCash: '100000',
                    commission: '0.001',
                    stake: '100',
                    selectedStrategy: 'SMA',
                    paramOverrides: {}
                }, mockT)
            })

            expect(result.current.result).toEqual(mockBacktestResult)
            expect(api.getBacktestDetail).toHaveBeenCalledWith('bt-456')

            vi.useFakeTimers() // Restore fake timers for other tests
        })

        it('should handle API errors', async () => {
            const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { })
            api.runBacktest.mockRejectedValue(new Error('Network error'))

            const { result } = renderHook(() => useBacktest())

            await act(async () => {
                await result.current.runBacktest({
                    ticker: 'AAPL',
                    startDate: '2023-01-01',
                    endDate: '2023-12-31',
                    initialCash: '100000',
                    commission: '0.001',
                    stake: '100',
                    selectedStrategy: 'SMA',
                    paramOverrides: null
                }, mockT)
            })

            expect(result.current.error).toBe('Network error')
            expect(result.current.loading).toBe(false)
            consoleSpy.mockRestore()
        })

        it('should not send params if paramOverrides is empty', async () => {
            api.runBacktest.mockResolvedValue({ backtest_id: 'test' })

            const { result } = renderHook(() => useBacktest())

            await act(async () => {
                await result.current.runBacktest({
                    ticker: 'AAPL',
                    startDate: '2023-01-01',
                    endDate: '2023-12-31',
                    initialCash: '100000',
                    commission: '0.001',
                    stake: '100',
                    selectedStrategy: 'SMA',
                    paramOverrides: {}
                }, mockT)
            })

            expect(api.runBacktest).toHaveBeenCalledWith(
                expect.objectContaining({ params: null })
            )
        })
    })

    describe('runPortfolioBacktest', () => {
        it('should return null if no valid tickers', async () => {
            const { result } = renderHook(() => useBacktest())

            let returnValue
            await act(async () => {
                returnValue = await result.current.runPortfolioBacktest(
                    { tickers: ['', '  '], weights: [0.5, 0.5] },
                    mockT
                )
            })

            expect(returnValue).toBe(null)
            expect(result.current.error).toBeTruthy()
        })

        it('should call API with correct parameters', async () => {
            const mockResult = { portfolio_id: 'pf-123' }
            api.runPortfolioBacktest.mockResolvedValue(mockResult)

            const { result } = renderHook(() => useBacktest())

            await act(async () => {
                await result.current.runPortfolioBacktest({
                    tickers: ['AAPL', 'GOOGL'],
                    weights: [0.6, 0.4],
                    startDate: '2023-01-01',
                    endDate: '2023-12-31',
                    initialCash: 100000,
                    commission: 0.001,
                    stake: 100,
                    selectedStrategy: 'SMA',
                    paramOverrides: { period: 20 }
                }, mockT)
            })

            expect(api.runPortfolioBacktest).toHaveBeenCalledWith({
                tickers: ['AAPL', 'GOOGL'],
                weights: [0.6, 0.4],
                start_date: '2023-01-01',
                end_date: '2023-12-31',
                initial_cash: 100000,
                commission: 0.001,
                stake: 100,
                strategy_name: 'SMA',
                params: { period: 20 }
            })
            expect(result.current.result).toEqual(mockResult)
        })

        it('should filter empty tickers from input', async () => {
            api.runPortfolioBacktest.mockResolvedValue({ portfolio_id: 'test' })

            const { result } = renderHook(() => useBacktest())

            await act(async () => {
                await result.current.runPortfolioBacktest({
                    tickers: ['AAPL', '', 'GOOGL', '  '],
                    weights: [0.4, 0.1, 0.4, 0.1],
                    startDate: '2023-01-01',
                    endDate: '2023-12-31',
                    initialCash: 100000,
                    commission: 0.001,
                    stake: 100,
                    selectedStrategy: null,
                    paramOverrides: {}
                }, mockT)
            })

            expect(api.runPortfolioBacktest).toHaveBeenCalledWith(
                expect.objectContaining({
                    tickers: ['AAPL', 'GOOGL'],
                    weights: [0.4, 0.1]
                })
            )
        })
    })

    describe('clearResult', () => {
        it('should clear all state', async () => {
            api.runBacktest.mockResolvedValue({ backtest_id: 'test' })

            const { result } = renderHook(() => useBacktest())

            await act(async () => {
                await result.current.runBacktest({
                    ticker: 'AAPL',
                    startDate: '2023-01-01',
                    endDate: '2023-12-31',
                    initialCash: '100000',
                    commission: '0.001',
                    stake: '100',
                    selectedStrategy: 'SMA',
                    paramOverrides: {}
                }, mockT)
            })

            expect(result.current.result).toBeTruthy()

            act(() => {
                result.current.clearResult()
            })

            expect(result.current.result).toBe(null)
            expect(result.current.error).toBe(null)
            expect(result.current.taskProgress).toBe(null)
        })
    })
})
