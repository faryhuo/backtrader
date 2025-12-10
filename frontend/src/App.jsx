import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { LogtoProvider } from './providers/LogtoProvider'
import { PrivateRoute } from './components/Auth/PrivateRoute'
import Layout from './components/Layout/Layout'
import RunStrategy from './pages/RunStrategy'
import StrategyMaintain from './pages/StrategyMaintain'
import DataSource from './pages/DataSource'
import { Home } from './pages/Home'
import { Callback } from './pages/Callback'
import { setTokenGetter } from './services/api'
import { useAuth } from './hooks/useAuth'
import { LOGIN_ENABLED } from './config/auth'
import './index.css'

/**
 * App Content Component
 *
 * Inner component that has access to Logto hooks.
 * Sets up token getter for API calls.
 */
function AppContent() {
    const { getAccessToken, loginEnabled } = useAuth()

    // Initialize token getter for API calls
    useEffect(() => {
        if (loginEnabled) {
            setTokenGetter(getAccessToken)
        } else {
            setTokenGetter(null)
        }
    }, [getAccessToken, loginEnabled])

    return (
        <Routes>
            {loginEnabled && <Route path="/login" element={<Home />} />}
            {loginEnabled && <Route path="/callback" element={<Callback />} />}

            <Route element={loginEnabled ? (
                <PrivateRoute>
                    <Layout />
                </PrivateRoute>
            ) : <Layout />}>
                <Route index element={<RunStrategy />} />
                <Route path="maintain" element={<StrategyMaintain />} />
                <Route path="datasource" element={<DataSource />} />
            </Route>

            {!loginEnabled && (
                <>
                    <Route path="/login" element={<Navigate to="/" replace />} />
                    <Route path="/callback" element={<Navigate to="/" replace />} />
                </>
            )}
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    )
}

/**
 * Root App Component
 *
 * Wraps the application with authentication provider.
 */
function App() {
    if (!LOGIN_ENABLED) {
        return (
            <BrowserRouter>
                <AppContent />
            </BrowserRouter>
        )
    }

    return (
        <LogtoProvider>
            <BrowserRouter>
                <AppContent />
            </BrowserRouter>
        </LogtoProvider>
    )
}

export default App
