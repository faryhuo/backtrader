/**
 * Core API utilities - authentication, request building, response parsing
 */
import { LOGIN_ENABLED } from '../config/auth'

// API base URL for HTTP requests (separate from Logto resource identifier)
export const API_URL = import.meta.env.VITE_API_BASE_URL

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
export const buildRequest = async (path, options = {}) => {
    const headers = new Headers(options.headers || {})

    if (options.body && !headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json')
    }

    // Inject access token if available
    if (getTokenFn) {
        try {
            const token = await getTokenFn(API_URL)
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
            return await getTokenFn(API_RESOURCE)
        } catch (error) {
            console.error('Failed to get access token:', error)
        }
    }
    return null
}

export const parseResponse = async (response) => {
    // Handle 401 Unauthorized first (before trying to parse body)
    if (response.status === 401 && LOGIN_ENABLED) {
        console.error('Unauthorized - redirecting to login')
        const loginPath = '/login'
        if (window.location.pathname !== loginPath) {
            window.location.href = loginPath
        }
        throw new Error('Unauthorized')
    }

    // Handle 204 No Content (no response body)
    if (response.status === 204) {
        return null
    }

    // Read body as text first to avoid consumption issues
    let bodyText = ''
    try {
        bodyText = await response.text()
    } catch {
        bodyText = ''
    }

    // Try to parse as JSON
    let data = null
    let isJson = false
    const contentType = response.headers.get('Content-Type') || ''

    if (bodyText) {
        // Check if Content-Type indicates JSON or try parsing anyway
        if (contentType.includes('application/json') || bodyText.trim().startsWith('{') || bodyText.trim().startsWith('[')) {
            try {
                data = JSON.parse(bodyText)
                isJson = true
            } catch {
                // JSON parsing failed, store as raw text
                data = { rawText: bodyText }
            }
        } else {
            // Non-JSON response (e.g., HTML error page)
            data = { rawText: bodyText }
        }
    }

    // Check if response is successful (status 200-299)
    if (!response.ok) {
        let message = `HTTP error! status: ${response.status}`
        if (data) {
            if (isJson && data.detail) {
                message = data.detail
            } else if (isJson && data.message) {
                message = data.message
            } else if (data.rawText) {
                // Include a snippet of the raw text for debugging (limit to prevent huge messages)
                const snippet = data.rawText.substring(0, 200)
                message = `${message} - ${snippet}${data.rawText.length > 200 ? '...' : ''}`
            }
        }
        throw new Error(message)
    }

    return data
}
