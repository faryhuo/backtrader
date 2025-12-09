const API_BASE = '/api'
const HOST = 'http://localhost:8000'

const API_URL = `${HOST}${API_BASE}`

export const api = {
    async getStrategies() {
        const res = await fetch(`${API_URL}/strategies`)
        if (!res.ok) throw new Error('Failed to fetch strategies')
        const data = await res.json()
        return data.strategies || []
    },

    async getStrategy(name) {
        if (!name) return null
        const res = await fetch(`${API_URL}/strategy?name=${encodeURIComponent(name)}`)
        if (!res.ok) throw new Error('Failed to fetch strategy')
        return await res.json()
    },

    async saveStrategy(name, code) {
        const res = await fetch(`${API_URL}/strategy`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name || 'default', code })
        })
        if (!res.ok) throw new Error('Failed to save strategy')
        return await res.json()
    },

    async runBacktest(params) {
        const res = await fetch(`${API_URL}/backtest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
        })
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`)
        return await res.json()
    },

    async analyzeResults(metrics) {
        const res = await fetch(`${API_URL}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ metrics })
        })
        if (!res.ok) throw new Error('Failed to perform AI analysis')
        return await res.json()
    }
}
