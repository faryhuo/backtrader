/**
 * Core API utilities - authentication, request building, response parsing
 */

// API base URL for HTTP requests (also used as Logto resource identifier)
// Logto requires absolute URIs for resource indicators
const envApiUrl = import.meta.env.VITE_API_BASE_URL || '/api';
export const API_URL = envApiUrl.startsWith('http')
    ? envApiUrl
    : (typeof window !== 'undefined'
        ? `${window.location.origin}${envApiUrl.startsWith('/') ? '' : '/'}${envApiUrl}`
        : envApiUrl);

// Token getter function (set by App component)
let getTokenFn = null

export class ApiError extends Error {
    constructor(payload = {}, options = {}) {
        super(payload.detail || options.fallbackMessage || 'Request failed')
        this.name = 'ApiError'
        this.status = options.status ?? null
        this.payload = payload
        this.error_code = payload.error_code || null
        this.request_id = payload.request_id || null
        this.details = payload.details || null
        this.retryable = Boolean(payload.retryable)
        this.data = options.data ?? null
    }
}

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

    // Set Content-Type for JSON body, but not for FormData (browser sets it with boundary)
    if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
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
            return await getTokenFn(API_URL)
        } catch (error) {
            console.error('Failed to get access token:', error)
        }
    }
    return null
}

export const parseResponse = async (response) => {
    // Handle 401 Unauthorized
    // Note: Auth redirect is handled by PrivateRoute component, not here
    if (response.status === 401) {
        console.warn('Unauthorized request')
        throw new ApiError({
            detail: 'Unauthorized',
            error_code: 'UNAUTHORIZED',
            retryable: false,
        }, { status: 401 })
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
        let payload = {
            detail: `HTTP error! status: ${response.status}`,
            error_code: 'HTTP_ERROR',
            retryable: response.status >= 500 || response.status === 429,
        }
        if (data) {
            if (isJson && data.detail) {
                payload = {
                    detail: data.detail,
                    error_code: data.error_code || payload.error_code,
                    request_id: data.request_id || null,
                    details: data.details || null,
                    retryable: data.retryable ?? payload.retryable,
                }
            } else if (isJson && data.message) {
                payload.detail = data.message
            } else if (data.rawText) {
                // Include a snippet of the raw text for debugging (limit to prevent huge messages)
                const snippet = data.rawText.substring(0, 200)
                payload.detail = `${payload.detail} - ${snippet}${data.rawText.length > 200 ? '...' : ''}`
            }
        }
        throw new ApiError(payload, { status: response.status, data })
    }

    return data
}
