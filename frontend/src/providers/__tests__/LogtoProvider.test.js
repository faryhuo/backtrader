/**
 * Unit tests for LogtoProvider
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LogtoProvider } from '../LogtoProvider'

// Mock @logto/react
vi.mock('@logto/react', () => ({
    LogtoProvider: ({ children, config }) => (
        <div data-testid="logto-provider" data-config={JSON.stringify(config)}>
            {children}
        </div>
    )
}))

// Mock LogtoConfigContext
vi.mock('../../contexts/LogtoConfigContext', () => ({
    useLogtoConfig: vi.fn()
}))

// Import after mocking
import { useLogtoConfig } from '../../contexts/LogtoConfigContext'

describe('LogtoProvider', () => {
    const mockValidConfig = {
        endpoint: 'https://logto.example.com',
        appId: 'test-app-id',
        redirectUri: 'http://localhost:5173/callback',
        postLogoutRedirectUri: 'http://localhost:5173',
        enableLogin: true
    }

    const mockDisabledConfig = {
        endpoint: null,
        appId: null,
        redirectUri: null,
        postLogoutRedirectUri: null,
        enableLogin: false
    }

    beforeEach(() => {
        vi.clearAllMocks()
        vi.stubGlobal('import.meta', {
            env: {
                VITE_API_BASE_URL: 'http://localhost:8000/api'
            }
        })
    })

    afterEach(() => {
        vi.restoreAllMocks()
        vi.unstubAllGlobals()
    })

    describe('loading state', () => {
        it('should show loading message while config is loading', () => {
            useLogtoConfig.mockReturnValue({
                config: null,
                loading: true,
                error: null
            })

            render(
                <LogtoProvider>
                    <div>Test Child</div>
                </LogtoProvider>
            )

            expect(screen.getByText('Loading authentication configuration...')).toBeInTheDocument()
            expect(screen.queryByText('Test Child')).not.toBeInTheDocument()
        })
    })

    describe('successful config loading', () => {
        it('should render children with Logto provider when config is valid', () => {
            useLogtoConfig.mockReturnValue({
                config: mockValidConfig,
                loading: false,
                error: null
            })

            render(
                <LogtoProvider>
                    <div>Test Child</div>
                </LogtoProvider>
            )

            expect(screen.getByTestId('logto-provider')).toBeInTheDocument()
            expect(screen.getByText('Test Child')).toBeInTheDocument()
        })

        it('should pass correct config to Logto provider', () => {
            useLogtoConfig.mockReturnValue({
                config: mockValidConfig,
                loading: false,
                error: null
            })

            render(
                <LogtoProvider>
                    <div>Test Child</div>
                </LogtoProvider>
            )

            const logtoProvider = screen.getByTestId('logto-provider')
            const configAttr = logtoProvider.getAttribute('data-config')
            const parsedConfig = JSON.parse(configAttr)

            expect(parsedConfig.endpoint).toBe('https://logto.example.com')
            expect(parsedConfig.appId).toBe('test-app-id')
            expect(parsedConfig.resources).toEqual(['http://localhost:8000/api'])
        })
    })

    describe('error handling', () => {
        it('should render children without Logto when login is disabled', () => {
            useLogtoConfig.mockReturnValue({
                config: mockDisabledConfig,
                loading: false,
                error: new Error('Config not available')
            })

            render(
                <LogtoProvider>
                    <div>Test Child</div>
                </LogtoProvider>
            )

            expect(screen.getByText('Test Child')).toBeInTheDocument()
            expect(screen.queryByTestId('logto-provider')).not.toBeInTheDocument()
        })

        it('should show error message when config is missing and login is enabled', () => {
            const consoleError = vi.spyOn(console, 'error').mockImplementation(() => { })

            useLogtoConfig.mockReturnValue({
                config: {
                    ...mockDisabledConfig,
                    enableLogin: true
                },
                loading: false,
                error: new Error('Config error')
            })

            render(
                <LogtoProvider>
                    <div>Test Child</div>
                </LogtoProvider>
            )

            expect(screen.getByText('Error loading authentication configuration')).toBeInTheDocument()
            expect(screen.queryByText('Test Child')).not.toBeInTheDocument()

            consoleError.mockRestore()
        })
    })
})
