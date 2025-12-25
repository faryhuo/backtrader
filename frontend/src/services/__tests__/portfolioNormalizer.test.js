/**
 * Unit tests for Portfolio Normalizers
 */
import { describe, it, expect } from 'vitest'
import { normalizePortfolioResult, normalizePortfolioHistory } from '../normalizers/portfolioNormalizer'

describe('portfolioNormalizer', () => {
    describe('normalizePortfolioResult', () => {
        it('should return null for null input', () => {
            expect(normalizePortfolioResult(null)).toBeNull()
        })

        it('should return null for undefined input', () => {
            expect(normalizePortfolioResult(undefined)).toBeNull()
        })

        it('should preserve existing fields', () => {
            const data = {
                portfolio_id: 'test-123',
                tickers: ['AAPL', 'GOOGL'],
                total_return: 15.5
            }
            const result = normalizePortfolioResult(data)
            expect(result.portfolio_id).toBe('test-123')
            expect(result.tickers).toEqual(['AAPL', 'GOOGL'])
            expect(result.total_return).toBe(15.5)
        })

        it('should normalize correlation field from correlation_matrix', () => {
            const data = { correlation_matrix: { matrix: [[1, 0.5], [0.5, 1]], tickers: ['AAPL', 'GOOGL'] } }
            const result = normalizePortfolioResult(data)
            expect(result.correlation).toEqual({ matrix: [[1, 0.5], [0.5, 1]], tickers: ['AAPL', 'GOOGL'] })
        })

        it('should prefer correlation over correlation_matrix', () => {
            const data = {
                correlation: { matrix: [[1, 0.8], [0.8, 1]], tickers: ['A', 'B'] },
                correlation_matrix: { matrix: [[1, 0.5], [0.5, 1]], tickers: ['X', 'Y'] }
            }
            const result = normalizePortfolioResult(data)
            expect(result.correlation).toEqual({ matrix: [[1, 0.8], [0.8, 1]], tickers: ['A', 'B'] })
        })

        it('should set correlation to null when neither field exists', () => {
            const data = { portfolio_id: 'test' }
            const result = normalizePortfolioResult(data)
            expect(result.correlation).toBeNull()
        })

        it('should normalize optimization field from optimization_suggestion', () => {
            const data = { optimization_suggestion: { optimal_weights: [0.6, 0.4] } }
            const result = normalizePortfolioResult(data)
            expect(result.optimization).toEqual({ optimal_weights: [0.6, 0.4] })
        })

        it('should prefer optimization over optimization_suggestion', () => {
            const data = {
                optimization: { optimal_weights: [0.7, 0.3] },
                optimization_suggestion: { optimal_weights: [0.5, 0.5] }
            }
            const result = normalizePortfolioResult(data)
            expect(result.optimization).toEqual({ optimal_weights: [0.7, 0.3] })
        })

        it('should set optimization to null when neither field exists', () => {
            const data = { portfolio_id: 'test' }
            const result = normalizePortfolioResult(data)
            expect(result.optimization).toBeNull()
        })

        it('should ensure individual_results is always an array when undefined', () => {
            const data = { individual_results: undefined }
            const result = normalizePortfolioResult(data)
            expect(result.individual_results).toEqual([])
        })

        it('should ensure individual_results is always an array when null', () => {
            const data = { individual_results: null }
            const result = normalizePortfolioResult(data)
            expect(result.individual_results).toEqual([])
        })

        it('should ensure individual_results is always an array when object', () => {
            const data = { individual_results: { ticker: 'AAPL' } }
            const result = normalizePortfolioResult(data)
            expect(result.individual_results).toEqual([])
        })

        it('should preserve existing array for individual_results', () => {
            const items = [
                { ticker: 'AAPL', success: true, total_return: 10.5 },
                { ticker: 'GOOGL', success: true, total_return: 8.2 }
            ]
            const data = { individual_results: items }
            const result = normalizePortfolioResult(data)
            expect(result.individual_results).toEqual(items)
        })
    })

    describe('normalizePortfolioHistory', () => {
        it('should return empty array for null input', () => {
            expect(normalizePortfolioHistory(null)).toEqual([])
        })

        it('should return empty array for undefined input', () => {
            expect(normalizePortfolioHistory(undefined)).toEqual([])
        })

        it('should return empty array for non-array input', () => {
            expect(normalizePortfolioHistory({ items: [] })).toEqual([])
        })

        it('should normalize all items in the array', () => {
            const items = [
                { portfolio_id: '1', correlation_matrix: { matrix: [[1]] } },
                { portfolio_id: '2', optimization_suggestion: { optimal_weights: [0.5, 0.5] } }
            ]
            const result = normalizePortfolioHistory(items)

            expect(result).toHaveLength(2)
            expect(result[0].correlation).toEqual({ matrix: [[1]] })
            expect(result[1].optimization).toEqual({ optimal_weights: [0.5, 0.5] })
        })

        it('should ensure all items have individual_results as array', () => {
            const items = [
                { portfolio_id: '1', individual_results: undefined },
                { portfolio_id: '2', individual_results: [{ ticker: 'AAPL' }] }
            ]
            const result = normalizePortfolioHistory(items)

            expect(result[0].individual_results).toEqual([])
            expect(result[1].individual_results).toEqual([{ ticker: 'AAPL' }])
        })
    })
})
