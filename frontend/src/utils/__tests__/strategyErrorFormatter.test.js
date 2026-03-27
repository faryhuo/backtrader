import { describe, expect, it } from 'vitest'
import {
    formatStrategyError,
    shouldShowStrategyErrorDetail,
} from '../strategyErrorFormatter'

describe('strategyErrorFormatter', () => {
    const mockT = (key, fallbackOrOptions) => {
        if (typeof fallbackOrOptions === 'string') {
            return fallbackOrOptions
        }

        return fallbackOrOptions?.defaultValue || key
    }

    it('formats insufficient-data errors into a friendly message', () => {
        const error = formatStrategyError(
            "Backtest failed: Insufficient market data for strategy 'KDJ' on AAPL at 1d timeframe: the requested range 2026-03-22 to 2026-03-27 returned 4 bars, but the strategy indicators need at least 18 bars. Extend the start date or reduce the indicator periods.",
            mockT
        )

        expect(error.type).toBe('insufficient_data')
        expect(error.title).toBe('Not enough market data to run this strategy')
        expect(error.description).toContain('returned 4 bars')
        expect(error.description).toContain('needs at least 18 bars')
        expect(error.suggestions).toHaveLength(2)
        expect(shouldShowStrategyErrorDetail(error)).toBe(false)
    })

    it('keeps technical details for generic execution failures', () => {
        const error = formatStrategyError(
            'Backtest failed: division by zero',
            mockT
        )

        expect(error.type).toBe('generic')
        expect(error.title).toBe('Strategy execution failed')
        expect(error.detail).toBe('Backtest failed: division by zero')
        expect(shouldShowStrategyErrorDetail(error)).toBe(true)
    })
})
