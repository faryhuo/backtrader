/**
 * Unit tests for formatters utility functions
 */
import { describe, it, expect } from 'vitest'
import { isNumber, formatNumber, formatPercent, formatCurrency } from '../formatters'

describe('formatters', () => {
    describe('isNumber', () => {
        it('should return true for valid numbers', () => {
            expect(isNumber(0)).toBe(true)
            expect(isNumber(42)).toBe(true)
            expect(isNumber(-123.45)).toBe(true)
            expect(isNumber(Infinity)).toBe(true)
        })

        it('should return false for NaN', () => {
            expect(isNumber(NaN)).toBe(false)
        })

        it('should return false for non-numbers', () => {
            expect(isNumber(null)).toBe(false)
            expect(isNumber(undefined)).toBe(false)
            expect(isNumber('123')).toBe(false)
            expect(isNumber('abc')).toBe(false)
            expect(isNumber({})).toBe(false)
            expect(isNumber([])).toBe(false)
        })
    })

    describe('formatNumber', () => {
        it('should format numbers with default 2 decimal places', () => {
            expect(formatNumber(123.456)).toBe('123.46')
            expect(formatNumber(0)).toBe('0.00')
            expect(formatNumber(-99.9)).toBe('-99.90')
        })

        it('should format numbers with custom decimal places', () => {
            expect(formatNumber(123.456789, 4)).toBe('123.4568')
            expect(formatNumber(100, 0)).toBe('100')
        })

        it('should return N/A for non-numbers', () => {
            expect(formatNumber(NaN)).toBe('N/A')
            expect(formatNumber(null)).toBe('N/A')
            expect(formatNumber(undefined)).toBe('N/A')
            expect(formatNumber('123')).toBe('N/A')
        })
    })

    describe('formatPercent', () => {
        it('should format percentages with default settings', () => {
            expect(formatPercent(0.1234)).toBe('0.12%')
            expect(formatPercent(0)).toBe('0.00%')
            expect(formatPercent(-0.5)).toBe('-0.50%')
        })

        it('should format percentages with custom decimal places', () => {
            expect(formatPercent(0.123456, 4)).toBe('0.1235%')
        })

        it('should apply multiplier correctly', () => {
            expect(formatPercent(0.1234, 2, 100)).toBe('12.34%')
            expect(formatPercent(50, 0, 1)).toBe('50%')
        })

        it('should return N/A for non-numbers', () => {
            expect(formatPercent(NaN)).toBe('N/A')
            expect(formatPercent(null)).toBe('N/A')
            expect(formatPercent(undefined)).toBe('N/A')
        })
    })

    describe('formatCurrency', () => {
        it('should format currency with dollar sign', () => {
            expect(formatCurrency(1234.56)).toBe('$1,234.56')
            expect(formatCurrency(0)).toBe('$0.00')
        })

        it('should format negative currency', () => {
            // Note: toLocaleString formats negative as $-X rather than -$X
            expect(formatCurrency(-1234.56)).toBe('$-1,234.56')
        })

        it('should format with custom decimal places', () => {
            expect(formatCurrency(1234.5678, 4)).toBe('$1,234.5678')
            expect(formatCurrency(1000, 0)).toBe('$1,000')
        })

        it('should return N/A for non-numbers', () => {
            expect(formatCurrency(NaN)).toBe('N/A')
            expect(formatCurrency(null)).toBe('N/A')
            expect(formatCurrency(undefined)).toBe('N/A')
        })
    })
})
