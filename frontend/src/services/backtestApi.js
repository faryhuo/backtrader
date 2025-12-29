/**
 * Backtest API - run backtest, history, analysis
 */
import { buildRequest, parseResponse } from './apiCore'

export const backtestApi = {
    async runBacktest(params) {
        const res = await buildRequest('/backtest', {
            method: 'POST',
            body: JSON.stringify(params)
        })
        return await parseResponse(res)
    },

    async getBacktestHistory(params = {}) {
        const res = await buildRequest('/backtest/history', {
            method: 'POST',
            body: JSON.stringify({
                ticker: params.ticker || null,
                strategy_name: params.strategy_name || null,
                start_date: params.start_date || null,
                end_date: params.end_date || null,
                sort_by: params.sort_by || 'created_at',
                sort_order: params.sort_order || 'desc',
                limit: params.limit || 50,
                offset: params.offset || 0
            })
        })
        return await parseResponse(res)
    },

    async getBacktestDetail(backtestId) {
        const res = await buildRequest(`/backtest/history/${backtestId}`)
        return await parseResponse(res)
    },

    async deleteBacktest(backtestId) {
        const res = await buildRequest(`/backtest/history/${backtestId}`, {
            method: 'DELETE'
        })
        return await parseResponse(res)
    },

    async updateBacktestAiAnalysis(backtestId, modelName, analysis) {
        const res = await buildRequest(`/backtest/history/${backtestId}/ai-analysis`, {
            method: 'POST',
            body: JSON.stringify({ model_name: modelName, analysis })
        })
        return await parseResponse(res)
    },

    async analyzeResults(metrics) {
        const res = await buildRequest('/analyze', {
            method: 'POST',
            body: JSON.stringify({ metrics })
        })
        return await parseResponse(res)
    },

    async getDeepAnalysis(backtestId, config = {}) {
        const res = await buildRequest(`/backtest/history/${backtestId}/deep-analysis`, {
            method: 'POST',
            body: JSON.stringify({
                benchmarks: config.benchmarks || null,
                rolling_window: config.rolling_window || 60,
                risk_free_rate: config.risk_free_rate || 0.02
            })
        })
        return await parseResponse(res)
    },

    /**
     * Export backtest data in PyFolio-compatible format as a ZIP file
     * @param {string} backtestId - Backtest ID
     * @returns {Promise<Blob>} - ZIP file blob
     */
    async exportPyFolioData(backtestId) {
        const res = await buildRequest(`/backtest/history/${backtestId}/pyfolio-export`)
        if (!res.ok) {
            const error = await res.json().catch(() => ({ detail: 'Export failed' }))
            throw new Error(error.detail || 'Export failed')
        }
        return await res.blob()
    },

    /**
     * Get PyFolio-style performance metrics
     * @param {string} backtestId - Backtest ID
     * @returns {Promise<Object>} - Metrics object
     */
    async getPyFolioMetrics(backtestId) {
        const res = await buildRequest(`/backtest/history/${backtestId}/pyfolio-metrics`)
        return await parseResponse(res)
    },

    /**
     * Generate PyFolio-style tear sheet (QuantStats HTML report)
     * @param {string} backtestId - Backtest ID
     * @param {Object} config - Configuration options
     * @param {string} config.benchmark_ticker - Optional benchmark ticker
     * @returns {Promise<Object>} - Object with HTML content
     */
    async generatePyFolioTearSheet(backtestId, config = {}) {
        const res = await buildRequest(`/backtest/history/${backtestId}/pyfolio-tearsheet`, {
            method: 'POST',
            body: JSON.stringify({
                include_tear_sheet: true,
                benchmark_ticker: config.benchmark_ticker || null
            })
        })
        return await parseResponse(res)
    }
}
