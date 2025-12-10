import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import RunStrategy from './pages/RunStrategy'
import StrategyMaintain from './pages/StrategyMaintain'
import DataSource from './pages/DataSource'
import './index.css'

/**
 * Root App Component
 *
 * Simple routing without authentication.
 * All routes are public since backend uses M2M authentication.
 */
function App() {
    return (
        <BrowserRouter>
            <Routes>
                {/* Redirect root to /app */}
                <Route path="/" element={<Navigate to="/app" replace />} />

                {/* Main application routes */}
                <Route
                    path="/app/*"
                    element={
                        <Layout>
                            <Routes>
                                <Route index element={<RunStrategy />} />
                                <Route path="maintain" element={<StrategyMaintain />} />
                                <Route path="datasource" element={<DataSource />} />
                            </Routes>
                        </Layout>
                    }
                />
            </Routes>
        </BrowserRouter>
    )
}

export default App
