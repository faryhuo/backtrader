import { useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useLogto } from '@logto/react'
import { LogtoProvider } from './providers/LogtoProvider'
import { PrivateRoute } from './components/Auth/PrivateRoute'
import Layout from './components/Layout/Layout'
import RunStrategy from './pages/RunStrategy'
import StrategyMaintain from './pages/StrategyMaintain'
import DataSource from './pages/DataSource'
import { Home } from './pages/Home'
import { Callback } from './pages/Callback'
import { setTokenGetter } from './services/api'
import './index.css'

/**
 * App Content Component
 *
 * Inner component that has access to Logto hooks.
 * Sets up token getter for API calls.
 */
function AppContent() {
    const { getAccessToken } = useLogto()

    // Initialize token getter for API calls
    useEffect(() => {
        setTokenGetter(getAccessToken)
    }, [getAccessToken])

    return (
        <Routes>
            <Route path="/login" element={<Home />} />
            <Route path="/callback" element={<Callback />} />

            <Route
                element={
                    <PrivateRoute>
                        <Layout />
                    </PrivateRoute>
                }
            >
                <Route index element={<RunStrategy />} />
                <Route path="maintain" element={<StrategyMaintain />} />
                <Route path="datasource" element={<DataSource />} />
            </Route>
        </Routes>
    )
}

/**
 * Root App Component
 *
 * Wraps the application with authentication provider.
 */
function App() {
    return (
        <LogtoProvider>
            <BrowserRouter>
                <AppContent />
            </BrowserRouter>
        </LogtoProvider>
    )
}

export default App
