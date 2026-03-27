/**
 * Unit tests for apiCore service functions
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ApiError, parseResponse, buildRequest, setTokenGetter, getAccessToken } from '../apiCore'

describe('apiCore', () => {
    describe('parseResponse', () => {
        it('should return null for 204 No Content', async () => {
            const response = {
                status: 204,
                ok: true
            }

            const result = await parseResponse(response)
            expect(result).toBeNull()
        })

        it('should parse JSON response correctly', async () => {
            const mockData = { id: 1, name: 'Test' }
            const response = {
                status: 200,
                ok: true,
                headers: new Headers({ 'Content-Type': 'application/json' }),
                text: vi.fn().mockResolvedValue(JSON.stringify(mockData))
            }

            const result = await parseResponse(response)
            expect(result).toEqual(mockData)
        })

        it('should handle JSON response without Content-Type header', async () => {
            const mockData = { status: 'ok' }
            const response = {
                status: 200,
                ok: true,
                headers: new Headers(),
                text: vi.fn().mockResolvedValue(JSON.stringify(mockData))
            }

            const result = await parseResponse(response)
            expect(result).toEqual(mockData)
        })

        it('should handle array JSON response', async () => {
            const mockData = [1, 2, 3]
            const response = {
                status: 200,
                ok: true,
                headers: new Headers({ 'Content-Type': 'application/json' }),
                text: vi.fn().mockResolvedValue(JSON.stringify(mockData))
            }

            const result = await parseResponse(response)
            expect(result).toEqual(mockData)
        })

        it('should handle non-JSON response (HTML error page)', async () => {
            const htmlContent = '<html><body>502 Bad Gateway</body></html>'
            const response = {
                status: 200,
                ok: true,
                headers: new Headers({ 'Content-Type': 'text/html' }),
                text: vi.fn().mockResolvedValue(htmlContent)
            }

            const result = await parseResponse(response)
            expect(result).toEqual({ rawText: htmlContent })
        })

        it('should throw error for non-OK responses with JSON error detail', async () => {
            const errorData = {
                detail: 'Resource not found',
                error_code: 'NOT_FOUND',
                request_id: 'req-123',
                retryable: false,
            }
            const response = {
                status: 404,
                ok: false,
                headers: new Headers({ 'Content-Type': 'application/json' }),
                text: vi.fn().mockResolvedValue(JSON.stringify(errorData))
            }

            await expect(parseResponse(response)).rejects.toMatchObject({
                name: 'ApiError',
                message: 'Resource not found',
                error_code: 'NOT_FOUND',
                request_id: 'req-123',
                retryable: false,
            })
        })

        it('should throw error for non-OK responses with JSON message', async () => {
            const errorData = { message: 'Invalid request' }
            const response = {
                status: 400,
                ok: false,
                headers: new Headers({ 'Content-Type': 'application/json' }),
                text: vi.fn().mockResolvedValue(JSON.stringify(errorData))
            }

            await expect(parseResponse(response)).rejects.toThrow('Invalid request')
        })

        it('should include snippet of raw text in error for non-JSON errors', async () => {
            const htmlError = '<html>Error Page</html>'
            const response = {
                status: 502,
                ok: false,
                headers: new Headers({ 'Content-Type': 'text/html' }),
                text: vi.fn().mockResolvedValue(htmlError)
            }

            await expect(parseResponse(response)).rejects.toThrow('HTTP error! status: 502')
        })

        it('should throw ApiError for unauthorized responses', async () => {
            const response = {
                status: 401,
                ok: false,
            }

            await expect(parseResponse(response)).rejects.toBeInstanceOf(ApiError)
        })

        it('should handle empty response body', async () => {
            const response = {
                status: 200,
                ok: true,
                headers: new Headers(),
                text: vi.fn().mockResolvedValue('')
            }

            const result = await parseResponse(response)
            expect(result).toBeNull()
        })
    })

    describe('setTokenGetter and getAccessToken', () => {
        beforeEach(() => {
            // Reset token getter before each test
            setTokenGetter(null)
        })

        it('should return null when no token getter is set', async () => {
            const token = await getAccessToken()
            expect(token).toBeNull()
        })

        it('should use token getter when set', async () => {
            const mockToken = 'test-jwt-token'
            const mockTokenFn = vi.fn().mockResolvedValue(mockToken)

            setTokenGetter(mockTokenFn)
            const token = await getAccessToken()

            expect(token).toBe(mockToken)
        })

        it('should return null when token getter throws', async () => {
            const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => { })
            const mockTokenFn = vi.fn().mockRejectedValue(new Error('Token error'))

            setTokenGetter(mockTokenFn)
            const token = await getAccessToken()

            expect(token).toBeNull()
            expect(errorSpy).toHaveBeenCalled()

            errorSpy.mockRestore()
        })
    })

    describe('buildRequest', () => {
        const originalFetch = global.fetch

        beforeEach(() => {
            setTokenGetter(null)
            global.fetch = vi.fn().mockResolvedValue({ ok: true })
        })

        afterEach(() => {
            global.fetch = originalFetch
        })

        it('should build request with correct URL', async () => {
            await buildRequest('/api/test')

            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/test'),
                expect.any(Object)
            )
        })

        it('should set Content-Type header when body is provided', async () => {
            await buildRequest('/api/test', {
                method: 'POST',
                body: JSON.stringify({ data: 'test' })
            })

            expect(global.fetch).toHaveBeenCalled()
            const callArgs = global.fetch.mock.calls[0]
            const headers = callArgs[1].headers
            expect(headers.get('Content-Type')).toBe('application/json')
        })

        it('should not override existing Content-Type header', async () => {
            await buildRequest('/api/test', {
                method: 'POST',
                body: 'plain text',
                headers: { 'Content-Type': 'text/plain' }
            })

            expect(global.fetch).toHaveBeenCalled()
            const callArgs = global.fetch.mock.calls[0]
            const headers = callArgs[1].headers
            expect(headers.get('Content-Type')).toBe('text/plain')
        })

        it('should add Authorization header when token getter is set', async () => {
            const mockToken = 'jwt-token-123'
            setTokenGetter(vi.fn().mockResolvedValue(mockToken))

            await buildRequest('/api/test')

            const callArgs = global.fetch.mock.calls[0]
            const headers = callArgs[1].headers
            expect(headers.get('Authorization')).toBe(`Bearer ${mockToken}`)
        })

        it('should continue without token when token getter fails', async () => {
            const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => { })
            setTokenGetter(vi.fn().mockRejectedValue(new Error('Token fail')))

            await buildRequest('/api/test')

            expect(global.fetch).toHaveBeenCalled()
            const callArgs = global.fetch.mock.calls[0]
            const headers = callArgs[1].headers
            expect(headers.has('Authorization')).toBe(false)

            errorSpy.mockRestore()
        })
    })
})
