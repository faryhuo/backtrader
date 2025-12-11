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

const parseResponse = async (response) => {

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

    async analyzeChart(message, model, file) {
        const formData = new FormData()
        formData.append('message', message)
        formData.append('model', model)
        if (file) {
            formData.append('file', file)
        }

        // Build headers with auth token
        const headers = new Headers()
        if (getTokenFn) {
            try {
                const resource = import.meta.env.VITE_API_RESOURCE
                const token = await getTokenFn(resource)
                if (token) {
                    headers.set('Authorization', `Bearer ${token}`)
                }
            } catch (error) {
                console.error('Failed to get access token:', error)
            }
        }

        const res = await fetch(`${API_URL}/ai_analyze`, {
            method: 'POST',
            headers,
            body: formData
        })
        return await parseResponse(res)
    },

    async analyzeCode(code, model = 'gpt-5.1') {
        const prompt = `Please analyze the following Backtrader strategy code. Explain its logic, potential pitfalls, and suggest improvements:\n\n${code}`;
        const formData = new FormData();
        formData.append('message', prompt);
        formData.append('model', model);

        // Build headers with auth token
        const headers = new Headers()
        if (getTokenFn) {
            try {
                const resource = import.meta.env.VITE_API_RESOURCE
                const token = await getTokenFn(resource)
                if (token) {
                    headers.set('Authorization', `Bearer ${token}`)
                }
            } catch (error) {
                console.error('Failed to get access token:', error)
            }
        }

        const res = await fetch(`${API_URL}/ai_analyze`, {
            method: 'POST',
            headers,
            body: formData
        });
        const data = await parseResponse(res);
        return data.analysis;
    },

    async analyzeBacktest(metrics, model = 'gpt-5.1') {
        const prompt = `Please analyze the following backtest results and provide insights on the strategy's performance, risk, and potential improvements:\n\n${JSON.stringify(metrics, null, 2)}`;
        const formData = new FormData();
        formData.append('message', prompt);
        formData.append('model', model);

        // Build headers with auth token
        const headers = new Headers()
        if (getTokenFn) {
            try {
                const resource = import.meta.env.VITE_API_RESOURCE
                const token = await getTokenFn(resource)
                if (token) {
                    headers.set('Authorization', `Bearer ${token}`)
                }
            } catch (error) {
                console.error('Failed to get access token:', error)
            }
        }

        const res = await fetch(`${API_URL}/ai_analyze`, {
            method: 'POST',
            headers,
            body: formData
        });
        const data = await parseResponse(res);
        return data.analysis;
    },

    async rewriteCode(code, model = 'gpt-5.1') {
        const prompt = `Please rewrite and optimize the following Backtrader strategy code to follow best practices and fix potential issues. Return ONLY the python code, no markdown formatting or explanation:\n\n${code}`;
        const formData = new FormData();
        formData.append('message', prompt);
        formData.append('model', model);

        // Build headers with auth token
        const headers = new Headers()
        if (getTokenFn) {
            try {
                const resource = import.meta.env.VITE_API_RESOURCE
                const token = await getTokenFn(resource)
                if (token) {
                    headers.set('Authorization', `Bearer ${token}`)
                }
            } catch (error) {
                console.error('Failed to get access token:', error)
            }
        }

        const res = await fetch(`${API_URL}/ai_analyze`, {
            method: 'POST',
            headers,
            body: formData
        });
        const data = await parseResponse(res);
        // Clean up markdown code blocks if present
        let cleanCode = data.analysis;
        if (cleanCode.startsWith('```python')) {
            cleanCode = cleanCode.replace(/^```python\n/, '').replace(/\n```$/, '');
        } else if (cleanCode.startsWith('```')) {
            cleanCode = cleanCode.replace(/^```\n/, '').replace(/\n```$/, '');
        }
        return cleanCode;
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
    }
}
