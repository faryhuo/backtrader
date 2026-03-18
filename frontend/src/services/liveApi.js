/**
 * Live Trading API - Binance Spot sessions, orders, ticker
 */
import { buildRequest, parseResponse } from './apiCore'

export const liveApi = {
    async startSession(params) {
        const res = await buildRequest('/live/start', {
            method: 'POST',
            body: JSON.stringify(params)
        })
        return await parseResponse(res)
    },

    async stopSession(sessionId) {
        const res = await buildRequest('/live/stop', {
            method: 'POST',
            body: JSON.stringify({ session_id: sessionId })
        })
        return await parseResponse(res)
    },

    async getSessionStatus(sessionId) {
        const res = await buildRequest(`/live/status/${sessionId}`)
        return await parseResponse(res)
    },

    async listSessions(params = {}) {
        const queryParams = new URLSearchParams()
        if (params.status) queryParams.append('status', params.status)
        if (params.active_only) queryParams.append('active_only', 'true')
        if (params.limit) queryParams.append('limit', params.limit.toString())

        const query = queryParams.toString()
        const path = query ? `/live/sessions?${query}` : '/live/sessions'

        const res = await buildRequest(path)
        return await parseResponse(res)
    },

    async getSessionOrders(sessionId) {
        const res = await buildRequest(`/live/orders/${sessionId}`)
        return await parseResponse(res)
    },

    async cancelOrder(sessionId, orderId) {
        const res = await buildRequest(`/live/orders/${sessionId}/cancel/${orderId}`, {
            method: 'POST'
        })
        return await parseResponse(res)
    },

    async getTickerPrice(sessionId) {
        const res = await buildRequest(`/live/ticker/${sessionId}`)
        return await parseResponse(res)
    },

    async getOhlcv(sessionId, limit = 100) {
        const res = await buildRequest(`/live/ohlcv/${sessionId}?limit=${limit}`)
        return await parseResponse(res)
    },

    async getStrategyLogs(sessionId, limit = 100) {
        const res = await buildRequest(`/live/logs/${sessionId}?limit=${limit}`)
        return await parseResponse(res)
    },

    async getExchanges() {
        const res = await buildRequest('/live/exchanges')
        return await parseResponse(res)
    },

    async getHealth() {
        const res = await buildRequest('/live/health')
        return await parseResponse(res)
    }
}
