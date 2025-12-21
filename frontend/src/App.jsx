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
import BacktestHistory from './pages/BacktestHistory'
import WalkForward from './pages/WalkForward'
import LiveTradingDashboard from './pages/LiveTradingDashboard'
import PortfolioBacktest from './pages/PortfolioBacktest'
import Settings from './pages/Settings'
import { Home } from './pages/Home'
import { Callback } from './pages/Callback'
import TaskCenter from './pages/TaskCenter'
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
                    colorPrimary: '#22d3ee',
                    colorBgBase: '#0a0b10',
                    colorBgContainer: '#1a1b23',
                    colorBorder: '#1e293b',
                    borderRadius: 12,
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
                        <Route path="history" element={<BacktestHistory />} />
                        <Route path="walkforward" element={<WalkForward />} />
                        <Route path="portfolio" element={<PortfolioBacktest />} />
                        <Route path="live" element={<LiveTradingDashboard />} />
                        <Route path="tasks" element={<TaskCenter />} />
                        <Route path="settings" element={<Settings />} />
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
