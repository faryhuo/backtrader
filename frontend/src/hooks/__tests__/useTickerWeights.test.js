/**
 * Unit tests for useTickerWeights hook
 */
import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useTickerWeights } from '../useTickerWeights'

describe('useTickerWeights', () => {
    describe('initial state', () => {
        it('should return default initial values', () => {
            const { result } = renderHook(() => useTickerWeights())

            expect(result.current.tickers).toEqual(['AAPL', 'GOOGL'])
            expect(result.current.weights).toEqual([0.5, 0.5])
            expect(result.current.totalWeight).toBe(1)
            expect(result.current.isWeightValid).toBe(true)
        })

        it('should accept custom initial values', () => {
            const { result } = renderHook(() =>
                useTickerWeights({
                    initialTickers: ['MSFT', 'AMZN', 'META'],
                    initialWeights: [0.3, 0.4, 0.3]
                })
            )

            expect(result.current.tickers).toEqual(['MSFT', 'AMZN', 'META'])
            expect(result.current.weights).toEqual([0.3, 0.4, 0.3])
        })

        it('should provide all required methods', () => {
            const { result } = renderHook(() => useTickerWeights())

            expect(typeof result.current.addTicker).toBe('function')
            expect(typeof result.current.removeTicker).toBe('function')
            expect(typeof result.current.updateTicker).toBe('function')
            expect(typeof result.current.updateWeight).toBe('function')
            expect(typeof result.current.normalizeWeights).toBe('function')
            expect(typeof result.current.equalWeights).toBe('function')
            expect(typeof result.current.reset).toBe('function')
        })
    })

    describe('addTicker', () => {
        it('should add a new ticker with zero weight', () => {
            const { result } = renderHook(() => useTickerWeights())

            act(() => {
                result.current.addTicker()
            })

            expect(result.current.tickers).toEqual(['AAPL', 'GOOGL', ''])
            expect(result.current.weights).toEqual([0.5, 0.5, 0])
        })

        it('should allow adding multiple tickers', () => {
            const { result } = renderHook(() => useTickerWeights())

            act(() => {
                result.current.addTicker()
                result.current.addTicker()
            })

            expect(result.current.tickers).toHaveLength(4)
            expect(result.current.weights).toHaveLength(4)
        })
    })

    describe('removeTicker', () => {
        it('should remove ticker at specified index', () => {
            const { result } = renderHook(() =>
                useTickerWeights({
                    initialTickers: ['A', 'B', 'C'],
                    initialWeights: [0.3, 0.4, 0.3]
                })
            )

            act(() => {
                result.current.removeTicker(1)
            })

            expect(result.current.tickers).toEqual(['A', 'C'])
            expect(result.current.weights).toEqual([0.3, 0.3])
        })

        it('should not remove if only one ticker remains', () => {
            const { result } = renderHook(() =>
                useTickerWeights({
                    initialTickers: ['AAPL'],
                    initialWeights: [1]
                })
            )

            act(() => {
                result.current.removeTicker(0)
            })

            expect(result.current.tickers).toEqual(['AAPL'])
            expect(result.current.weights).toEqual([1])
        })
    })

    describe('updateTicker', () => {
        it('should update ticker symbol at index', () => {
            const { result } = renderHook(() => useTickerWeights())

            act(() => {
                result.current.updateTicker(0, 'MSFT')
            })

            expect(result.current.tickers[0]).toBe('MSFT')
        })

        it('should convert ticker to uppercase', () => {
            const { result } = renderHook(() => useTickerWeights())

            act(() => {
                result.current.updateTicker(0, 'msft')
            })

            expect(result.current.tickers[0]).toBe('MSFT')
        })
    })

    describe('updateWeight', () => {
        it('should update weight at index', () => {
            const { result } = renderHook(() => useTickerWeights())

            act(() => {
                result.current.updateWeight(0, 0.7)
            })

            expect(result.current.weights[0]).toBe(0.7)
        })

        it('should handle zero/falsy values', () => {
            const { result } = renderHook(() => useTickerWeights())

            act(() => {
                result.current.updateWeight(0, 0)
            })

            expect(result.current.weights[0]).toBe(0)
        })
    })

    describe('normalizeWeights', () => {
        it('should normalize weights to sum to 1', () => {
            const { result } = renderHook(() =>
                useTickerWeights({
                    initialTickers: ['A', 'B'],
                    initialWeights: [1, 1]
                })
            )

            act(() => {
                result.current.normalizeWeights()
            })

            expect(result.current.weights).toEqual([0.5, 0.5])
            expect(result.current.totalWeight).toBe(1)
        })

        it('should handle uneven weights', () => {
            const { result } = renderHook(() =>
                useTickerWeights({
                    initialTickers: ['A', 'B', 'C'],
                    initialWeights: [1, 2, 3]
                })
            )

            act(() => {
                result.current.normalizeWeights()
            })

            const total = result.current.weights.reduce((a, b) => a + b, 0)
            expect(total).toBeCloseTo(1, 1)
        })

        it('should not change weights if total is zero', () => {
            const { result } = renderHook(() =>
                useTickerWeights({
                    initialTickers: ['A', 'B'],
                    initialWeights: [0, 0]
                })
            )

            act(() => {
                result.current.normalizeWeights()
            })

            expect(result.current.weights).toEqual([0, 0])
        })
    })

    describe('equalWeights', () => {
        it('should set equal weights for all tickers', () => {
            const { result } = renderHook(() =>
                useTickerWeights({
                    initialTickers: ['A', 'B', 'C', 'D'],
                    initialWeights: [0.1, 0.2, 0.3, 0.4]
                })
            )

            act(() => {
                result.current.equalWeights()
            })

            expect(result.current.weights).toEqual([0.25, 0.25, 0.25, 0.25])
        })

        it('should handle two tickers', () => {
            const { result } = renderHook(() => useTickerWeights())

            act(() => {
                result.current.equalWeights()
            })

            expect(result.current.weights).toEqual([0.5, 0.5])
        })
    })

    describe('computed values', () => {
        it('should calculate totalWeight correctly', () => {
            const { result } = renderHook(() =>
                useTickerWeights({
                    initialTickers: ['A', 'B', 'C'],
                    initialWeights: [0.2, 0.3, 0.4]
                })
            )

            expect(result.current.totalWeight).toBeCloseTo(0.9, 2)
        })

        it('should validate weights correctly', () => {
            const { result } = renderHook(() =>
                useTickerWeights({
                    initialTickers: ['A', 'B'],
                    initialWeights: [0.5, 0.5]
                })
            )

            expect(result.current.isWeightValid).toBe(true)

            act(() => {
                result.current.updateWeight(0, 0.3)
            })

            expect(result.current.isWeightValid).toBe(false)
        })

        it('should filter valid tickers', () => {
            const { result } = renderHook(() =>
                useTickerWeights({
                    initialTickers: ['AAPL', '', 'GOOGL', '  '],
                    initialWeights: [0.25, 0.25, 0.25, 0.25]
                })
            )

            expect(result.current.validTickers).toEqual(['AAPL', 'GOOGL'])
        })
    })

    describe('reset', () => {
        it('should reset to initial state', () => {
            const { result } = renderHook(() =>
                useTickerWeights({
                    initialTickers: ['AAPL', 'GOOGL'],
                    initialWeights: [0.5, 0.5]
                })
            )

            act(() => {
                result.current.addTicker()
                result.current.updateTicker(0, 'MSFT')
                result.current.updateWeight(0, 0.8)
            })

            expect(result.current.tickers).not.toEqual(['AAPL', 'GOOGL'])

            act(() => {
                result.current.reset()
            })

            expect(result.current.tickers).toEqual(['AAPL', 'GOOGL'])
            expect(result.current.weights).toEqual([0.5, 0.5])
        })
    })
})
