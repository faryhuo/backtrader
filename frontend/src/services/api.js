const API_BASE = '/api'
export const HOST = import.meta.env.VITE_API_HOST || 'http://localhost:8000'
const API_URL = `${HOST}${API_BASE}`

const buildRequest = (path, options = {}) => {
    const headers = new Headers(options.headers || {})

    if (options.body && !headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json')
    }

    return fetch(`${API_URL}${path}`, { ...options, headers })
}

const parseResponse = async (response) => {
    const contentType = response.headers.get('content-type') || ''
    const isJson = contentType.includes('application/json')
    const data = isJson ? await response.json() : null

    if (!response.ok) {
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

    async analyzeChart(message, model, file) {
        const formData = new FormData()
        formData.append('message', message)
        formData.append('model', model)
        formData.append('file', file)

        const res = await fetch(`${API_URL}/ai_analyze`, {
            method: 'POST',
            body: formData
        })
        return await parseResponse(res)
    }
}