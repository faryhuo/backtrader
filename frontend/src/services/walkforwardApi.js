/**
 * Walk-Forward Optimization API
 */
import { buildRequest, parseResponse } from './apiCore'

export const walkforwardApi = {
    async startWalkForward(params) {
        const res = await buildRequest('/walkforward/start', {
            method: 'POST',
            body: JSON.stringify(params)
        })
        return await parseResponse(res)
    },

    async listWalkForward(params = {}) {
        const queryParams = new URLSearchParams()
        if (params.ticker) queryParams.append('ticker', params.ticker)
        if (params.strategy_name) queryParams.append('strategy_name', params.strategy_name)
        if (params.status) queryParams.append('status', params.status)
        if (params.sort_by) queryParams.append('sort_by', params.sort_by)
        if (params.sort_order) queryParams.append('sort_order', params.sort_order)
        if (params.limit) queryParams.append('limit', params.limit.toString())
        if (params.offset) queryParams.append('offset', params.offset.toString())

        const query = queryParams.toString()
        const path = query ? `/walkforward/list?${query}` : '/walkforward/list'

        const res = await buildRequest(path)
        return await parseResponse(res)
    },

    async getWalkForward(optimizationId) {
        const res = await buildRequest(`/walkforward/${optimizationId}`)
        return await parseResponse(res)
    },

    async getWalkForwardStatus(optimizationId) {
        const res = await buildRequest(`/walkforward/${optimizationId}/status`)
        return await parseResponse(res)
    },

    async deleteWalkForward(optimizationId) {
        const res = await buildRequest(`/walkforward/${optimizationId}`, {
            method: 'DELETE'
        })
        return await parseResponse(res)
    }
}
