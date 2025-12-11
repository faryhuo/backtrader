import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, theme } from 'antd'
import { LogtoProvider } from './providers/LogtoProvider'
import { NotificationProvider } from './providers/NotificationProvider'
import { PrivateRoute } from './components/Auth/PrivateRoute'
import Layout from './components/Layout/Layout'
import RunStrategy from './pages/RunStrategy'
import StrategyMaintain from './pages/StrategyMaintain'
import DataSource from './pages/DataSource'
import LiveTradingDashboard from './pages/LiveTradingDashboard'
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
        <ConfigProvider
            theme={{
                algorithm: theme.darkAlgorithm,
                token: {
                    colorPrimary: '#0ea5e9',
                    colorBgBase: '#0b0e14',
                    colorBgContainer: '#161b22',
                    colorBorder: '#1e293b',
                    borderRadius: 8,
                    fontFamily: 'Inter, system-ui, sans-serif',
                },
            }}
        >
            <NotificationProvider>
                <Routes>
                    {/* Landing Page - Accessible to everyone */}
                    <Route path="/" element={<Home />} />
                    <Route path="/welcome" element={<Home />} />

                    {/* Auth Routes */}
                    {loginEnabled && <Route path="/login" element={<Navigate to="/" replace />} />}
                    {loginEnabled && <Route path="/callback" element={<Callback />} />}

                    {/* Protected Application Routes */}
                    <Route element={loginEnabled ? (
                        <PrivateRoute>
                            <Layout />
                        </PrivateRoute>
                    ) : <Layout />}>
                        <Route path="strategy" element={<RunStrategy />} />
                        <Route path="maintain" element={<StrategyMaintain />} />
                        <Route path="datasource" element={<DataSource />} />
                        <Route path="live" element={<LiveTradingDashboard />} />
                    </Route>

                    {/* Redirects for Auth Disabled */}
                    {!loginEnabled && (
                        <>
                            <Route path="/login" element={<Navigate to="/" replace />} />
                            <Route path="/callback" element={<Navigate to="/" replace />} />
                        </>
                    )}
                    
                    {/* Catch-all redirect */}
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </NotificationProvider>
        </ConfigProvider>
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
