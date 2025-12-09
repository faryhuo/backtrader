import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import RunStrategy from './pages/RunStrategy'
import StrategyMaintain from './pages/StrategyMaintain'
import DataSource from './pages/DataSource'
import './index.css'

function App() {
    return (
        <BrowserRouter>
            <Layout>
                <Routes>
                    <Route path="/" element={<RunStrategy />} />
                    <Route path="/maintain" element={<StrategyMaintain />} />
                    <Route path="/datasource" element={<DataSource />} />
                </Routes>
            </Layout>
        </BrowserRouter>
    )
}

export default App
