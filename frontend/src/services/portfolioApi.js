/**
 * Portfolio Backtest API
 */
import { buildRequest, parseResponse } from './apiCore'
import { normalizePortfolioResult, normalizePortfolioHistory } from './normalizers/portfolioNormalizer'

export const portfolioApi = {
    async runPortfolioBacktest(params) {
        const res = await buildRequest('/portfolio/multi-asset/backtest', {
            method: 'POST',
            body: JSON.stringify(params)
        })
        const data = await parseResponse(res)
        return normalizePortfolioResult(data)
    },

    async getPortfolioHistory(params = {}) {
        const queryParams = new URLSearchParams()
        if (params.sort_by) queryParams.append('sort_by', params.sort_by)
        if (params.sort_order) queryParams.append('sort_order', params.sort_order)
        if (params.limit) queryParams.append('limit', params.limit.toString())
        if (params.offset) queryParams.append('offset', params.offset.toString())

        const query = queryParams.toString()
        const path = query ? `/portfolio/history?${query}` : '/portfolio/history'

        const res = await buildRequest(path)
        const data = await parseResponse(res)
        // Normalize history items if response is an array or has items property
        if (Array.isArray(data)) {
            return normalizePortfolioHistory(data)
        }
        if (data?.items) {
            return { ...data, items: normalizePortfolioHistory(data.items) }
        }
        return data
    },

    async getPortfolioDetail(portfolioId) {
        const res = await buildRequest(`/portfolio/${portfolioId}`)
        const data = await parseResponse(res)
        return normalizePortfolioResult(data)
    },

    async deletePortfolio(portfolioId) {
        const res = await buildRequest(`/portfolio/${portfolioId}`, {
            method: 'DELETE'
        })
        return await parseResponse(res)
    }
}
