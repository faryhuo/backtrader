/**
 * Live Trading API - sessions, orders, exchanges
 */
import { buildRequest, parseResponse } from './apiCore'

export const liveApi = {
    async startLiveTrading(params) {
        const res = await buildRequest('/live/start', {
            method: 'POST',
            body: JSON.stringify(params)
        })
        return await parseResponse(res)
    },

    async stopLiveTrading(sessionId) {
        const res = await buildRequest('/live/stop', {
            method: 'POST',
            body: JSON.stringify({ session_id: sessionId })
        })
        return await parseResponse(res)
    },

    async getLiveStatus(sessionId) {
        const res = await buildRequest(`/live/status/${sessionId}`)
        return await parseResponse(res)
    },

    async listLiveSessions(params = {}) {
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

    async getExchanges() {
        const res = await buildRequest('/live/exchanges')
        return await parseResponse(res)
    },

    async getLiveHealth() {
        const res = await buildRequest('/live/health')
        return await parseResponse(res)
    }
}
