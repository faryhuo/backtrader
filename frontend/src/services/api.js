import { LOGIN_ENABLED } from '../config/auth'

export const API_URL = import.meta.env.VITE_API_RESOURCE

// Token getter function (set by App component)
let getTokenFn = null

/**
 * Set the token getter function
 * This is called by the App component to provide access to Logto's getAccessToken
 */
export function setTokenGetter(fn) {
    getTokenFn = fn
}

/**
 * Build a request with authentication token
 */
const buildRequest = async (path, options = {}) => {
    const headers = new Headers(options.headers || {})

    if (options.body && !headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json')
    }

    // Inject access token if available
    if (getTokenFn) {
        try {
            const resource = import.meta.env.VITE_API_RESOURCE
            const token = await getTokenFn(resource)
            if (token) {
                headers.set('Authorization', `Bearer ${token}`)
            }
        } catch (error) {
            console.error('Failed to get access token:', error)
            // Continue without token - API will return 401 if auth is required
        }
    }

    return fetch(`${API_URL}${path}`, { ...options, headers })
}

export const getAccessToken = async () => {
    if (getTokenFn) {
        try {
            const resource = import.meta.env.VITE_API_RESOURCE
            return await getTokenFn(resource)
        } catch (error) {
            console.error('Failed to get access token:', error)
        }
    }
    return null
}

export const parseResponse = async (response) => {

    const data = await response.json()

    if (response.status !== 200) {
        // Handle 401 Unauthorized - redirect to login
        if (response.status === 401 && LOGIN_ENABLED) {
            console.error('Unauthorized - redirecting to login')
            const loginPath = '/login'
            if (window.location.pathname !== loginPath) {
                window.location.href = loginPath
            }
        }

        const message = (data && (data.detail || data.message)) || `HTTP error! status: ${response.status}`
        throw new Error(message)
    }

    return data
}

export const api = {
    async getStrategies() {
        const res = await buildRequest('/strategies')
        const data = await parseResponse(res)
        return data?.strategies || []
    },

    async getStrategy(name) {
        if (!name) return null
        const res = await buildRequest(`/strategy?name=${encodeURIComponent(name)}`)
        return await parseResponse(res)
    },

    async saveStrategy(name, code) {
        const res = await buildRequest('/strategy', {
            method: 'POST',
            body: JSON.stringify({ name, code })
        })
        return await parseResponse(res)
    },

    async runBacktest(params) {
        const res = await buildRequest('/backtest', {
            method: 'POST',
            body: JSON.stringify(params)
        })
        return await parseResponse(res)
    },

    async fetchMarketData(params) {
        const res = await buildRequest('/data', {
            method: 'POST',
            body: JSON.stringify(params)
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

    // Backtest History API Methods

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

    // Live Trading API Methods

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
    },

    // Walk-Forward Optimization API Methods

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
