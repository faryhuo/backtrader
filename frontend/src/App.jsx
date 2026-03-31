import { useEffect, useRef, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { ConfigProvider, Spin, theme } from 'antd'
import { AuthProvider } from './providers/AuthProvider'
import { LogtoConfigProvider, useLogtoConfig } from './contexts/LogtoConfigContext'
import { NotificationProvider } from './providers/NotificationProvider'
import { SettingsProvider } from './contexts/SettingsContext'
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
import OnboardingSetup from './pages/OnboardingSetup'
import DataManagement from './pages/DataManagement'
import { Home } from './pages/Home'
import { Callback } from './pages/Callback'
import Login from './pages/Login'
import TaskCenter from './pages/TaskCenter'
import ReportCenter from './pages/ReportCenter'
import SharedReport from './pages/SharedReport'
import { setTokenGetter } from './services/api'
import { setupApi } from './services/setupApi'
import { useAuth } from './hooks/useAuth'
import './index.css'

function isSetupBypassPath(pathname) {
    return pathname === '/onboarding'
        || pathname === '/callback'
        || pathname.startsWith('/report/shared/')
}

function SetupRedirectGate({ authLoading, children, getAccessToken, loginEnabled }) {
    const { pathname } = useLocation()
    const previousPathRef = useRef(null)
    const setupReadyRef = useRef(null)
    const [checkingSetup, setCheckingSetup] = useState(true)
    const [needsOnboarding, setNeedsOnboarding] = useState(false)

    useEffect(() => {
        const previousPath = previousPathRef.current
        previousPathRef.current = pathname

        if (isSetupBypassPath(pathname)) {
            setCheckingSetup(false)
            setNeedsOnboarding(false)
            return
        }

        if (loginEnabled && authLoading) {
            setCheckingSetup(true)
            return
        }

        if (setupReadyRef.current === true && previousPath !== '/onboarding') {
            setCheckingSetup(false)
            setNeedsOnboarding(false)
            return
        }

        let cancelled = false

        async function checkSetupReadiness() {
            setCheckingSetup(true)
            try {
                if (loginEnabled) {
                    setTokenGetter(getAccessToken)
                }
                const response = await setupApi.getSetupWizard()
                const isReady = Boolean(response?.status?.is_ready)

                if (cancelled) {
                    return
                }

                setupReadyRef.current = isReady
                setNeedsOnboarding(!isReady)
            } catch (error) {
                if (cancelled) {
                    return
                }

                if (error.message === 'Unauthorized') {
                    setupReadyRef.current = true
                    setNeedsOnboarding(false)
                } else {
                    setupReadyRef.current = null
                    setNeedsOnboarding(false)
                    console.error('Failed to load setup readiness:', error)
                }
            } finally {
                if (!cancelled) {
                    setCheckingSetup(false)
                }
            }
        }

        checkSetupReadiness()

        return () => {
            cancelled = true
        }
    }, [authLoading, getAccessToken, loginEnabled, pathname])

    if (needsOnboarding) {
        return <Navigate to="/onboarding" replace />
    }

    if (checkingSetup) {
        return (
            <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center' }}>
                <Spin size="large" />
            </div>
        )
    }

    return children
}

/**
 * App Content Component
 *
 * Inner component that has access to Logto hooks.
 * Sets up token getter for API calls.
 */
function AppContent() {
    const { getAccessToken, isLoading: authLoading, loginEnabled, authProvider } = useAuth()

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
            <SettingsProvider>
                <NotificationProvider>
                    <SetupRedirectGate
                        authLoading={authLoading}
                        getAccessToken={getAccessToken}
                        loginEnabled={loginEnabled}
                    >
                        <Routes>
                            {/* Landing Page - Accessible to everyone */}
                            <Route path="/" element={<Home />} />
                            <Route path="/welcome" element={<Home />} />
                            <Route path="/onboarding" element={<OnboardingSetup />} />

                            {/* Auth Routes */}
                            {loginEnabled && <Route path="/login" element={<Login />} />}
                            {loginEnabled && authProvider === 'logto' && <Route path="/callback" element={<Callback />} />}

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
                                <Route path="data_management" element={<DataManagement />} />
                                <Route path="tasks" element={<TaskCenter />} />
                                <Route path="reports" element={<ReportCenter />} />
                                <Route path="settings" element={<Settings />} />
                            </Route>

                            {/* Public Shared Report Route - No authentication required */}
                            <Route path="report/shared/:token" element={<SharedReport />} />

                            {/* Redirects for Auth Disabled */}
                            {!loginEnabled && (
                                <>
                                    <Route path="/login" element={<Navigate to="/" replace />} />
                                    <Route path="/callback" element={<Navigate to="/" replace />} />
                                </>
                            )}

                            {loginEnabled && authProvider !== 'logto' && (
                                <Route path="/callback" element={<Navigate to="/login" replace />} />
                            )}

                            {/* Catch-all redirect */}
                            <Route path="*" element={<Navigate to="/" replace />} />
                        </Routes>
                    </SetupRedirectGate>
                </NotificationProvider>
            </SettingsProvider>
        </ConfigProvider>
    )
}

/**
 * Root App Component
 *
 * Wraps the application with authentication provider.
 */
function App() {
    return (
        <LogtoConfigProvider>
            <AppInner />
        </LogtoConfigProvider>
    )
}

/**
 * App Inner Component
 * 
 * Has access to Logto config from context.
 */
function AppInner() {
    const { loading } = useLogtoConfig()

    // Show loading while config is being fetched
    if (loading) {
        return <div>Loading...</div>
    }

    return (
        <AuthProvider>
            <BrowserRouter>
                <AppContent />
            </BrowserRouter>
        </AuthProvider>
    )
}

export default App
