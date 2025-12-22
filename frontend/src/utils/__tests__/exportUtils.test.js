/**
 * Unit tests for exportUtils utility functions
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { generateFilename, exportToCSV } from '../exportUtils'

describe('exportUtils', () => {
    describe('generateFilename', () => {
        beforeEach(() => {
            // Mock Date to return a fixed date
            vi.useFakeTimers()
            vi.setSystemTime(new Date('2025-01-15T10:30:00Z'))
        })

        afterEach(() => {
            vi.useRealTimers()
        })

        it('should generate filename with ticker and date', () => {
            const result = generateFilename('AAPL', '.csv')
            expect(result).toBe('AAPL_2025-01-15.csv')
        })

        it('should handle different extensions', () => {
            expect(generateFilename('TSLA', '.xlsx')).toBe('TSLA_2025-01-15.xlsx')
            expect(generateFilename('MSFT', '.png')).toBe('MSFT_2025-01-15.png')
        })

        it('should handle tickers with special characters', () => {
            expect(generateFilename('BRK.A', '.csv')).toBe('BRK.A_2025-01-15.csv')
        })
    })

    describe('exportToCSV', () => {
        let mockLink
        let appendChildSpy
        let removeChildSpy

        beforeEach(() => {
            // Mock DOM elements and methods
            mockLink = {
                href: '',
                download: '',
                click: vi.fn()
            }
            vi.spyOn(document, 'createElement').mockReturnValue(mockLink)
            appendChildSpy = vi.spyOn(document.body, 'appendChild').mockImplementation(() => { })
            removeChildSpy = vi.spyOn(document.body, 'removeChild').mockImplementation(() => { })
        })

        afterEach(() => {
            vi.restoreAllMocks()
        })

        it('should not export when data is empty', () => {
            const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => { })

            exportToCSV([], 'test.csv')

            expect(warnSpy).toHaveBeenCalledWith('No data to export')
            expect(document.createElement).not.toHaveBeenCalled()
        })

        it('should not export when data is null', () => {
            const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => { })

            exportToCSV(null, 'test.csv')

            expect(warnSpy).toHaveBeenCalledWith('No data to export')
        })

        it('should create CSV with correct headers', () => {
            const testData = [
                { time: '2025-01-01', open: 100, high: 110, low: 95, close: 105 }
            ]

            exportToCSV(testData, 'test.csv')

            expect(mockLink.click).toHaveBeenCalled()
            expect(mockLink.download).toBe('test.csv')
        })

        it('should include volume column when data has volume', () => {
            const testData = [
                { time: '2025-01-01', open: 100, high: 110, low: 95, close: 105, volume: 1000000 }
            ]

            exportToCSV(testData, 'test.csv')

            expect(mockLink.click).toHaveBeenCalled()
        })

        it('should include ticker info as comments when provided', () => {
            const testData = [
                { time: '2025-01-01', open: 100, high: 110, low: 95, close: 105 }
            ]
            const tickerInfo = {
                ticker: 'AAPL',
                long_name: 'Apple Inc.'
            }

            exportToCSV(testData, 'test.csv', tickerInfo)

            expect(mockLink.click).toHaveBeenCalled()
        })
    })
})
