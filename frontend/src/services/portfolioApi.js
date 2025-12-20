/**
 * Portfolio Backtest API
 */
import { buildRequest, parseResponse } from './apiCore'

export const portfolioApi = {
    async runPortfolioBacktest(params) {
        const res = await buildRequest('/portfolio/backtest', {
            method: 'POST',
            body: JSON.stringify(params)
        })
        return await parseResponse(res)
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
        return await parseResponse(res)
    },

    async getPortfolioDetail(portfolioId) {
        const res = await buildRequest(`/portfolio/${portfolioId}`)
        return await parseResponse(res)
    },

    async deletePortfolio(portfolioId) {
        const res = await buildRequest(`/portfolio/${portfolioId}`, {
            method: 'DELETE'
        })
        return await parseResponse(res)
    }
}
