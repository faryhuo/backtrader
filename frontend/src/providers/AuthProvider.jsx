import { LogtoProvider as LogtoReactProvider, useLogto } from '@logto/react'
import PropTypes from 'prop-types'
import { useEffect, useState } from 'react'
import { AuthContext } from '../contexts/AuthContext'
import { useLogtoConfig } from '../contexts/LogtoConfigContext'
import { authApi } from '../services/authApi'

const TOKEN_STORAGE_KEY = 'system_auth_token'

function readStoredToken() {
    if (typeof window === 'undefined') {
        return null
    }
    return window.localStorage.getItem(TOKEN_STORAGE_KEY)
}

const ANONYMOUS_AUTH = {
    authProvider: 'none',
    loginEnabled: false,
    registrationEnabled: false,
    isAuthenticated: true,
    isLoading: false,
    error: null,
    user: null,
    signIn: async () => null,
    signOut: async () => null,
    signInWithPassword: async () => null,
    registerWithPassword: async () => null,
    getAccessToken: async () => null,
    getIdTokenClaims: async () => ({}),
    refreshUser: async () => null,
}

function SystemAuthBridge({ children, config }) {
    const [token, setToken] = useState(() => readStoredToken())
    const [user, setUser] = useState(null)
    const [isLoading, setIsLoading] = useState(Boolean(readStoredToken()))
    const [error, setError] = useState(null)

    useEffect(() => {
        let cancelled = false

        async function loadUser() {
            if (!token) {
                setUser(null)
                setIsLoading(false)
                return
            }

            setIsLoading(true)
            try {
                const response = await authApi.getCurrentUser(token)
                if (!cancelled) {
                    setUser(response.user || null)
                    setError(null)
                }
            } catch (fetchError) {
                if (!cancelled) {
                    window.localStorage.removeItem(TOKEN_STORAGE_KEY)
                    setToken(null)
                    setUser(null)
                    setError(fetchError)
                }
            } finally {
                if (!cancelled) {
                    setIsLoading(false)
                }
            }
        }

        loadUser()

        return () => {
            cancelled = true
        }
    }, [token])

    const persistAuth = (response) => {
        const nextToken = response?.access_token || null
        if (nextToken) {
            window.localStorage.setItem(TOKEN_STORAGE_KEY, nextToken)
        } else {
            window.localStorage.removeItem(TOKEN_STORAGE_KEY)
        }
        setToken(nextToken)
        setUser(response?.user || null)
        setError(null)
        return response
    }

    const value = {
        authProvider: 'system',
        loginEnabled: true,
        registrationEnabled: Boolean(config?.registrationEnabled),
        isAuthenticated: Boolean(token && user),
        isLoading,
        error,
        user,
        signIn: async () => null,
        signOut: async () => {
            window.localStorage.removeItem(TOKEN_STORAGE_KEY)
            setToken(null)
            setUser(null)
        },
        signInWithPassword: async (payload) => persistAuth(await authApi.login(payload)),
        registerWithPassword: async (payload) => persistAuth(await authApi.register(payload)),
        getAccessToken: async () => token,
        getIdTokenClaims: async () => user || {},
        refreshUser: async () => {
            if (!token) {
                return null
            }
            const response = await authApi.getCurrentUser(token)
            setUser(response.user || null)
            return response.user || null
        },
    }

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

SystemAuthBridge.propTypes = {
    children: PropTypes.node.isRequired,
    config: PropTypes.object,
}

function LogtoAuthBridge({ children }) {
    const logto = useLogto()
    const value = {
        ...logto,
        authProvider: 'logto',
        loginEnabled: true,
        registrationEnabled: false,
        user: null,
        signInWithPassword: async () => null,
        registerWithPassword: async () => null,
        refreshUser: async () => null,
    }

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

LogtoAuthBridge.propTypes = {
    children: PropTypes.node.isRequired,
}

export function AuthProvider({ children }) {
    const { config, loading, error } = useLogtoConfig()

    if (loading) {
        return <div>Loading authentication configuration...</div>
    }

    if (!config?.enableLogin) {
        return <AuthContext.Provider value={ANONYMOUS_AUTH}>{children}</AuthContext.Provider>
    }

    if (config.authProvider === 'system') {
        return <SystemAuthBridge config={config}>{children}</SystemAuthBridge>
    }

    if (error && (!config?.endpoint || !config?.appId)) {
        return <div>Error loading authentication configuration</div>
    }

    const envApiUrl = import.meta.env.VITE_API_BASE_URL || '/api'
    const resourceUri = envApiUrl.startsWith('http')
        ? envApiUrl
        : `${window.location.origin}${envApiUrl.startsWith('/') ? '' : '/'}${envApiUrl}`

    return (
        <LogtoReactProvider
            config={{
                endpoint: config.endpoint,
                appId: config.appId,
                resources: [resourceUri],
            }}
        >
            <LogtoAuthBridge>{children}</LogtoAuthBridge>
        </LogtoReactProvider>
    )
}

AuthProvider.propTypes = {
    children: PropTypes.node.isRequired,
}
