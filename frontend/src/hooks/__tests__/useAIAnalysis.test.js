/**
 * Unit tests for useAIAnalysis hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useAIAnalysis } from '../useAIAnalysis'

// Mock performFullStrategyAnalysis
vi.mock('../../services/aiAnalysis', () => ({
    performFullStrategyAnalysis: vi.fn()
}))

// Mock antd message
vi.mock('antd', () => ({
    message: {
        success: vi.fn(),
        error: vi.fn(),
        warning: vi.fn()
    }
}))

import { performFullStrategyAnalysis } from '../../services/aiAnalysis'
import { message } from 'antd'

describe('useAIAnalysis', () => {
    const mockGetAvailableModels = () => ['gpt-4o', 'claude-3']
    const mockSettings = { apiKey: 'test-key' }

    beforeEach(() => {
        vi.clearAllMocks()
    })

    afterEach(() => {
        vi.restoreAllMocks()
    })

    describe('initial state', () => {
        it('should return default state', () => {
            const { result } = renderHook(() =>
                useAIAnalysis({
                    getAvailableModels: mockGetAvailableModels,
                    settings: mockSettings
                })
            )

            expect(result.current.selectedModel).toBe('gpt-4o')
            expect(result.current.analyses).toEqual({})
            expect(result.current.aiLoading).toBe(false)
            expect(result.current.hasAnalysis).toBe(false)
            expect(result.current.availableModels).toEqual(['gpt-4o', 'claude-3'])
        })

        it('should provide all required methods', () => {
            const { result } = renderHook(() =>
                useAIAnalysis({
                    getAvailableModels: mockGetAvailableModels,
                    settings: mockSettings
                })
            )

            expect(typeof result.current.runAnalysis).toBe('function')
            expect(typeof result.current.setSelectedModel).toBe('function')
            expect(typeof result.current.clearAnalyses).toBe('function')
        })
    })

    describe('initialAnalyses', () => {
        it('should merge initialAnalyses with local analyses', () => {
            const initialAnalyses = { 'gpt-4o': 'Previous analysis' }

            const { result } = renderHook(() =>
                useAIAnalysis({
                    getAvailableModels: mockGetAvailableModels,
                    settings: mockSettings,
                    initialAnalyses
                })
            )

            expect(result.current.analyses).toEqual(initialAnalyses)
            expect(result.current.hasAnalysis).toBe(true)
        })

        it('should override initialAnalyses with new analyses', async () => {
            const initialAnalyses = { 'gpt-4o': 'Old analysis' }
            performFullStrategyAnalysis.mockResolvedValue({ analysis: 'New analysis' })

            const { result } = renderHook(() =>
                useAIAnalysis({
                    getAvailableModels: mockGetAvailableModels,
                    settings: mockSettings,
                    initialAnalyses
                })
            )

            await act(async () => {
                await result.current.runAnalysis({
                    result: { metrics: {}, plot_url: 'http://test.png' },
                    strategyName: 'TestStrategy',
                    ticker: 'AAPL',
                    startDate: '2023-01-01',
                    endDate: '2023-12-31'
                })
            })

            expect(result.current.analyses['gpt-4o']).toBe('New analysis')
        })
    })

    describe('runAnalysis', () => {
        it('should call performFullStrategyAnalysis with correct parameters', async () => {
            performFullStrategyAnalysis.mockResolvedValue({ analysis: 'Test analysis' })

            const { result } = renderHook(() =>
                useAIAnalysis({
                    getAvailableModels: mockGetAvailableModels,
                    settings: mockSettings
                })
            )

            await act(async () => {
                await result.current.runAnalysis({
                    result: { metrics: { pnl: 1000 }, plot_url: 'http://test.png' },
                    strategyName: 'SMA',
                    ticker: 'AAPL',
                    startDate: '2023-01-01',
                    endDate: '2023-12-31',
                    strategyCode: 'code here'
                })
            })

            expect(performFullStrategyAnalysis).toHaveBeenCalledWith({
                result: { metrics: { pnl: 1000 }, plot_url: 'http://test.png' },
                strategyName: 'SMA',
                ticker: 'AAPL',
                startDate: '2023-01-01',
                endDate: '2023-12-31',
                model: 'gpt-4o',
                initialStrategyCode: 'code here',
                settings: mockSettings
            })
        })

        it('should update analyses state on success', async () => {
            performFullStrategyAnalysis.mockResolvedValue({ analysis: 'Analysis result' })

            const { result } = renderHook(() =>
                useAIAnalysis({
                    getAvailableModels: mockGetAvailableModels,
                    settings: mockSettings
                })
            )

            await act(async () => {
                await result.current.runAnalysis({
                    result: { metrics: {}, plot_url: 'http://test.png' },
                    strategyName: 'Test',
                    ticker: 'AAPL',
                    startDate: '2023-01-01',
                    endDate: '2023-12-31'
                })
            })

            expect(result.current.analyses['gpt-4o']).toBe('Analysis result')
            expect(result.current.activeTab).toBe('gpt-4o')
            expect(result.current.hasAnalysis).toBe(true)
        })

        it('should set loading state during analysis', async () => {
            let resolvePromise
            performFullStrategyAnalysis.mockImplementation(() =>
                new Promise(resolve => { resolvePromise = resolve })
            )

            const { result } = renderHook(() =>
                useAIAnalysis({
                    getAvailableModels: mockGetAvailableModels,
                    settings: mockSettings
                })
            )

            act(() => {
                result.current.runAnalysis({
                    result: { metrics: {}, plot_url: 'http://test.png' },
                    strategyName: 'Test',
                    ticker: 'AAPL',
                    startDate: '2023-01-01',
                    endDate: '2023-12-31'
                })
            })

            await waitFor(() => {
                expect(result.current.aiLoading).toBe(true)
            })

            await act(async () => {
                resolvePromise({ analysis: 'Done' })
            })

            await waitFor(() => {
                expect(result.current.aiLoading).toBe(false)
            })
        })

        it('should return null if result is missing', async () => {
            const { result } = renderHook(() =>
                useAIAnalysis({
                    getAvailableModels: mockGetAvailableModels,
                    settings: mockSettings
                })
            )

            let returnValue
            await act(async () => {
                returnValue = await result.current.runAnalysis({
                    result: null,
                    strategyName: 'Test'
                })
            })

            expect(returnValue).toBeNull()
            expect(performFullStrategyAnalysis).not.toHaveBeenCalled()
        })

        it('should handle errors gracefully', async () => {
            const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { })
            performFullStrategyAnalysis.mockRejectedValue(new Error('API Error'))

            const { result } = renderHook(() =>
                useAIAnalysis({
                    getAvailableModels: mockGetAvailableModels,
                    settings: mockSettings
                })
            )

            await act(async () => {
                await result.current.runAnalysis({
                    result: { metrics: {}, plot_url: 'http://test.png' },
                    strategyName: 'Test',
                    ticker: 'AAPL'
                })
            })

            expect(message.error).toHaveBeenCalled()
            expect(result.current.aiLoading).toBe(false)
            consoleSpy.mockRestore()
        })
    })

    describe('onAnalysisSaved callback', () => {
        it('should call onAnalysisSaved after successful analysis', async () => {
            const onAnalysisSaved = vi.fn().mockResolvedValue()
            performFullStrategyAnalysis.mockResolvedValue({ analysis: 'Analysis result' })

            const { result } = renderHook(() =>
                useAIAnalysis({
                    getAvailableModels: mockGetAvailableModels,
                    settings: mockSettings,
                    onAnalysisSaved
                })
            )

            await act(async () => {
                await result.current.runAnalysis({
                    result: { metrics: {}, plot_url: 'http://test.png' },
                    strategyName: 'Test',
                    ticker: 'AAPL',
                    startDate: '2023-01-01',
                    endDate: '2023-12-31',
                    backtestId: 'bt-123'
                })
            })

            expect(onAnalysisSaved).toHaveBeenCalledWith('bt-123', 'gpt-4o', 'Analysis result')
            expect(message.success).toHaveBeenCalled()
        })

        it('should not call onAnalysisSaved without backtestId', async () => {
            const onAnalysisSaved = vi.fn()
            performFullStrategyAnalysis.mockResolvedValue({ analysis: 'Analysis result' })

            const { result } = renderHook(() =>
                useAIAnalysis({
                    getAvailableModels: mockGetAvailableModels,
                    settings: mockSettings,
                    onAnalysisSaved
                })
            )

            await act(async () => {
                await result.current.runAnalysis({
                    result: { metrics: {}, plot_url: 'http://test.png' },
                    strategyName: 'Test',
                    ticker: 'AAPL'
                    // No backtestId
                })
            })

            expect(onAnalysisSaved).not.toHaveBeenCalled()
        })

        it('should handle onAnalysisSaved failure gracefully', async () => {
            const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { })
            const onAnalysisSaved = vi.fn().mockRejectedValue(new Error('Save failed'))
            performFullStrategyAnalysis.mockResolvedValue({ analysis: 'Analysis result' })

            const { result } = renderHook(() =>
                useAIAnalysis({
                    getAvailableModels: mockGetAvailableModels,
                    settings: mockSettings,
                    onAnalysisSaved
                })
            )

            await act(async () => {
                await result.current.runAnalysis({
                    result: { metrics: {}, plot_url: 'http://test.png' },
                    strategyName: 'Test',
                    ticker: 'AAPL',
                    backtestId: 'bt-123'
                })
            })

            // Analysis should still succeed even if save fails
            expect(result.current.analyses['gpt-4o']).toBe('Analysis result')
            expect(message.error).toHaveBeenCalled()
            consoleSpy.mockRestore()
        })
    })

    describe('clearAnalyses', () => {
        it('should clear all analyses', async () => {
            performFullStrategyAnalysis.mockResolvedValue({ analysis: 'Test' })

            const { result } = renderHook(() =>
                useAIAnalysis({
                    getAvailableModels: mockGetAvailableModels,
                    settings: mockSettings
                })
            )

            await act(async () => {
                await result.current.runAnalysis({
                    result: { metrics: {}, plot_url: 'http://test.png' },
                    strategyName: 'Test',
                    ticker: 'AAPL'
                })
            })

            expect(result.current.hasAnalysis).toBe(true)

            act(() => {
                result.current.clearAnalyses()
            })

            expect(result.current.analyses).toEqual({})
            expect(result.current.activeTab).toBeNull()
            expect(result.current.hasAnalysis).toBe(false)
        })
    })

    describe('model selection', () => {
        it('should allow changing selected model', () => {
            const { result } = renderHook(() =>
                useAIAnalysis({
                    getAvailableModels: mockGetAvailableModels,
                    settings: mockSettings
                })
            )

            expect(result.current.selectedModel).toBe('gpt-4o')

            act(() => {
                result.current.setSelectedModel('claude-3')
            })

            expect(result.current.selectedModel).toBe('claude-3')
        })
    })
})
