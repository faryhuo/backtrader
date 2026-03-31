import { API_URL, buildRequest, parseResponse } from './apiCore'

async function authFetch(path, options = {}, token = undefined) {
    if (token === undefined) {
        const response = await buildRequest(path, options)
        return parseResponse(response)
    }

    const headers = new Headers(options.headers || {})
    if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json')
    }
    if (token) {
        headers.set('Authorization', `Bearer ${token}`)
    }
    const response = await fetch(`${API_URL}${path}`, { ...options, headers })
    return parseResponse(response)
}

export const authApi = {
    async getAuthConfig() {
        return authFetch('/auth/config')
    },

    async login(payload) {
        return authFetch('/auth/login', {
            method: 'POST',
            body: JSON.stringify(payload),
        })
    },

    async register(payload) {
        return authFetch('/auth/register', {
            method: 'POST',
            body: JSON.stringify(payload),
        })
    },

    async getCurrentUser(token) {
        return authFetch('/auth/me', {}, token)
    },

    async getSystemUsers() {
        return authFetch('/auth/system-users')
    },

    async createSystemUser(payload) {
        return authFetch('/auth/system-users', {
            method: 'POST',
            body: JSON.stringify(payload),
        })
    },

    async setSystemUserActive(userId, isActive) {
        return authFetch(`/auth/system-users/${userId}/activate?is_active=${isActive}`, {
            method: 'POST',
        })
    },

    async resetSystemUserPassword(userId, password) {
        return authFetch(`/auth/system-users/${userId}/password`, {
            method: 'POST',
            body: JSON.stringify({ password }),
        })
    },
}
