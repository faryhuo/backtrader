import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import RunStrategy from './pages/RunStrategy'
import StrategyMaintain from './pages/StrategyMaintain'
import './index.css'

function App() {
    return (
        <BrowserRouter>
            <Layout>
                <Routes>
                    <Route path="/" element={<RunStrategy />} />
                    <Route path="/maintain" element={<StrategyMaintain />} />
                </Routes>
            </Layout>
        </BrowserRouter>
    )
}

export default App
