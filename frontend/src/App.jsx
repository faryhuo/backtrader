import { useState, useEffect } from 'react'
import Editor from '@monaco-editor/react'
import './index.css'

function App() {
    const [activeTab, setActiveTab] = useState('backtest')

    // Backtest State
    const [ticker, setTicker] = useState('AAPL')
    const [startDate, setStartDate] = useState('2022-01-01')
    const [endDate, setEndDate] = useState('2023-12-31')
    const [initialCash, setInitialCash] = useState(100000.0)
    const [commission, setCommission] = useState(0.0005)
    const [stake, setStake] = useState(100)
    const [isPlotMaximized, setIsPlotMaximized] = useState(false)
    const [plotScale, setPlotScale] = useState(1)
    const [strategies, setStrategies] = useState([])
    const [selectedStrategy, setSelectedStrategy] = useState('')
    const [newStrategyName, setNewStrategyName] = useState('')
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    // AI Analysis State
    const [aiLoading, setAiLoading] = useState(false)
    const [aiAnalysis, setAiAnalysis] = useState('')

    // Strategy Editor State
    const [code, setCode] = useState('')
    const [codeLoading, setCodeLoading] = useState(false)

    useEffect(() => {
        const init = async () => {
            const names = await fetchStrategies();
            if (names && names.length > 0) {
                setSelectedStrategy(names[0]);
                await fetchStrategy(names[0]);
            }
        }
        init();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    useEffect(() => {
        if (activeTab === 'strategy' && selectedStrategy) {
            fetchStrategy(selectedStrategy);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeTab, selectedStrategy])

    const defaultTemplate = `import backtrader as bt


class UserStrategy(bt.Strategy):
    params = (
        ("fast_period", 10),
        ("slow_period", 30),
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(period=self.p.fast_period)
        self.slow_ma = bt.indicators.SMA(period=self.p.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        if not self.position and self.crossover > 0:
            self.buy()
        elif self.position and self.crossover < 0:
            self.close()
`

    const fetchStrategies = async () => {
        try {
            const res = await fetch('/api/strategies')
            const data = await res.json()
            const names = data.strategies || []
            setStrategies(names)
            if (!names.includes(selectedStrategy)) {
                setSelectedStrategy(names[0] || '')
            }
            return names
        } catch (err) {
            console.error("Failed to fetch strategies", err)
            return []
        }
    }

    const fetchStrategy = async (name) => {
        if (!name) return
        try {
            setCodeLoading(true)
            const res = await fetch(`/api/strategy?name=${encodeURIComponent(name)}`)
            const data = await res.json()
            if (data.code) {
                setCode(data.code)
            }
        } catch (err) {
            console.error("Failed to fetch strategy", err)
        } finally {
            setCodeLoading(false)
        }
    }

    const saveStrategy = async () => {
        try {
            setCodeLoading(true);
            await fetch('/api/strategy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: selectedStrategy || 'default', code })
            });
            await fetchStrategies();
            alert("Strategy Saved!");
        } catch (err) {
            alert("Failed to save strategy");
        } finally {
            setCodeLoading(false);
        }
    }

    const createStrategy = async () => {
        const name = newStrategyName.trim()
        if (!name) return
        setSelectedStrategy(name)
        setCode(defaultTemplate)
        setNewStrategyName('')
    }

    const handleBacktest = async (e) => {
        e.preventDefault()
        if (!selectedStrategy) {
            setError('Please select or create a strategy first.')
            return
        }
        setLoading(true)
        setError(null)
        setResult(null)
        setAiAnalysis('')

        try {
            const response = await fetch('/api/backtest', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ticker,
                    start_date: startDate,
                    end_date: endDate,
                    initial_cash: parseFloat(initialCash),
                    commission: parseFloat(commission),
                    stake: parseInt(stake, 10),
                    strategy_name: selectedStrategy
                }),
            })

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }

            const data = await response.json()
            // data structure: { metrics: {...}, plot_url: "/images/..." }
            setResult(data)
        } catch (err) {
            console.error(err)
            setError(err.message || 'An error occurred')
        } finally {
            setLoading(false)
        }
    }

    const handleAnalyze = async () => {
        if (!result) return;
        setAiLoading(true);
        try {
            const res = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ metrics: result.metrics })
            });
            const data = await res.json();
            setAiAnalysis(data.analysis);
        } catch (err) {
            setAiAnalysis("Failed to perform AI analysis.");
        } finally {
            setAiLoading(false);
        }
    }

    const strategyFileName = selectedStrategy ? `${selectedStrategy}${selectedStrategy.endsWith('.py') ? '' : '.py'}` : ''
    const strategyRelativePath = strategyFileName ? `backend/strategy/${strategyFileName}` : ''

    const copyPath = async () => {
        if (!strategyRelativePath) return
        try {
            await navigator.clipboard.writeText(strategyRelativePath)
            alert('Path copied')
        } catch (_) {
            alert('Copy failed')
        }
    }

    return (
        <div className="container">
            <header className="header">
                <h1>Backtrader Pro</h1>
                <p className="subtitle">Advanced Strategy Backtesting</p>
            </header>

            <nav className="tabs">
                <button
                    className={activeTab === 'backtest' ? 'active' : ''}
                    onClick={() => setActiveTab('backtest')}
                >
                    Run Backtest
                </button>
                <button
                    className={activeTab === 'strategy' ? 'active' : ''}
                    onClick={() => setActiveTab('strategy')}
                >
                    Edit Strategy
                </button>
            </nav>

            <main className="main-content">
                {activeTab === 'backtest' ? (
                    <>
                        <section className="card form-card">
                            <h2>Strategy Configuration</h2>
                            <form onSubmit={handleBacktest} className="form-grid">
                                <div className="form-group">
                                    <label htmlFor="strategy-select">Strategy</label>
                                    <div className="strategy-row">
                                        <select
                                            id="strategy-select"
                                            value={selectedStrategy}
                                            onChange={(e) => setSelectedStrategy(e.target.value)}
                                        >
                                            {strategies.map((s) => (
                                                <option key={s} value={s}>{s}</option>
                                            ))}
                                        </select>
                                        <button
                                            type="button"
                                            className="btn-ghost"
                                            onClick={fetchStrategies}
                                            title="Refresh strategies"
                                        >
                                            Refresh
                                        </button>
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label htmlFor="ticker">Asset Ticker</label>
                                    <input
                                        id="ticker"
                                        type="text"
                                        value={ticker}
                                        onChange={(e) => setTicker(e.target.value)}
                                        required
                                    />
                                </div>

                                <div className="form-group">
                                    <label htmlFor="start-date">Start Date</label>
                                    <input
                                        id="start-date"
                                        type="date"
                                        value={startDate}
                                        onChange={(e) => setStartDate(e.target.value)}
                                        required
                                    />
                                </div>

                                <div className="form-group">
                                    <label htmlFor="end-date">End Date</label>
                                    <input
                                        id="end-date"
                                        type="date"
                                        value={endDate}
                                        onChange={(e) => setEndDate(e.target.value)}
                                        required
                                    />
                                </div>

                                <div className="form-group">
                                    <label htmlFor="initial-cash">Initial Capital ($)</label>
                                    <input
                                        id="initial-cash"
                                        type="number"
                                        value={initialCash}
                                        onChange={(e) => setInitialCash(e.target.value)}
                                        required
                                    />
                                </div>

                                <div className="form-group">
                                    <label htmlFor="commission">Commission (rate)</label>
                                    <input
                                        id="commission"
                                        type="number"
                                        step="0.0001"
                                        value={commission}
                                        onChange={(e) => setCommission(e.target.value)}
                                        required
                                    />
                                </div>

                                <div className="form-group">
                                    <label htmlFor="stake">Order Size (shares/contracts)</label>
                                    <input
                                        id="stake"
                                        type="number"
                                        value={stake}
                                        onChange={(e) => setStake(e.target.value)}
                                        required
                                    />
                                </div>

                                <div className="form-actions">
                                    <button type="submit" className="btn-primary" disabled={loading}>
                                        {loading ? <span className="spinner"></span> : 'Run Backtest'}
                                    </button>
                                </div>
                            </form>

                            {error && <div className="error-message">{error}</div>}
                        </section>

                        {result && (
                            <section className="results-section">
                                <div className="card stats-card">
                                    <h2>Performance Overview</h2>
                                    <div className="stats-grid">
                                        <div className="stat-item">
                                            <span className="stat-label">Final Value</span>
                                            <span className="stat-value highlight">${result.metrics.final_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                                        </div>
                                        <div className="stat-item">
                                            <span className="stat-label">Return</span>
                                            <span className={`stat-value ${result.metrics.returns >= 0 ? 'green' : 'red'}`}>
                                                {result.metrics.returns.toFixed(2)}%
                                            </span>
                                        </div>
                                        <div className="stat-item">
                                            <span className="stat-label">Sharpe Ratio</span>
                                            <span className="stat-value highlight">
                                                {result.metrics.sharpe ? result.metrics.sharpe.toFixed(2) : 'N/A'}
                                            </span>
                                        </div>
                                        <div className="stat-item">
                                            <span className="stat-label">Max Drawdown</span>
                                            <span className="stat-value red">
                                                {result.metrics.drawdown.toFixed(2)}%
                                            </span>
                                        </div>
                                    </div>

                                    <div className="ai-section">
                                        <button className="btn-secondary" onClick={handleAnalyze} disabled={aiLoading}>
                                            {aiLoading ? 'Analyzing...' : '✨ AI Analysis'}
                                        </button>
                                        {aiAnalysis && (
                                            <div className="ai-response">
                                                <h3>AI Insight:</h3>
                                                <p>{aiAnalysis}</p>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {result.plot_url && (
                                    <div className="card plot-card">
                                        <div className="plot-header">
                                            <h2>Strategy Visualization</h2>
                                            <div className="plot-actions">
                                                <button
                                                    type="button"
                                                    className="btn-ghost"
                                                    onClick={() => setIsPlotMaximized(true)}
                                                >
                                                    Maximize
                                                </button>
                                            </div>
                                        </div>
                                        <div className="plot-container">
                                            <img src={result.plot_url} alt="Strategy Plot" />
                                        </div>
                                    </div>
                                )}
                            </section>
                        )}
                    </>
                ) : (
                    <section className="card editor-card">
                        <h2>Strategy Editor (UserStrategy)</h2>
                        <p className="subtitle">Edit only the strategy class below; backtest engine is fixed.</p>
                        <div className="strategy-toolbar">
                            <div className="strategy-row">
                                <label htmlFor="editor-strategy-select">Active Strategy</label>
                                <select
                                    id="editor-strategy-select"
                                    value={selectedStrategy}
                                    onChange={(e) => setSelectedStrategy(e.target.value)}
                                    disabled={codeLoading}
                                >
                                    {strategies.map((s) => (
                                        <option key={s} value={s}>{s}</option>
                                    ))}
                                </select>
                                <button
                                    type="button"
                                    className="btn-ghost"
                                    onClick={() => fetchStrategy(selectedStrategy)}
                                    disabled={codeLoading}
                                >
                                    Reload
                                </button>
                                <button
                                    type="button"
                                    className="btn-ghost"
                                    onClick={fetchStrategies}
                                    disabled={codeLoading}
                                >
                                    Refresh List
                                </button>
                            </div>
                            <div className="strategy-row">
                                <label htmlFor="new-strategy">New Strategy Name</label>
                                <input
                                    id="new-strategy"
                                    type="text"
                                    value={newStrategyName}
                                    onChange={(e) => setNewStrategyName(e.target.value)}
                                    placeholder="e.g., breakout_v1"
                                />
                                <button
                                    type="button"
                                    className="btn-primary"
                                    onClick={createStrategy}
                                    disabled={codeLoading}
                                >
                                    New
                                </button>
                            </div>
                            {strategyRelativePath && (
                                <div className="strategy-info">
                                    <span>File: <code>{strategyRelativePath}</code></span>
                                    <div className="strategy-actions">
                                        <button type="button" className="btn-ghost" onClick={copyPath}>
                                            Copy Path
                                        </button>
                                        <a
                                            className="btn-ghost"
                                            href={`vscode://file/${strategyRelativePath}`}
                                            title="Open in VS Code"
                                        >
                                            Open in VS Code
                                        </a>
                                    </div>
                                </div>
                            )}
                        </div>
                        <div className="code-editor">
                            <Editor
                                height="60vh"
                                defaultLanguage="python"
                                language="python"
                                theme="vs-dark"
                                value={code}
                                onChange={(value) => setCode(value ?? '')}
                                options={{
                                    fontSize: 14,
                                    minimap: { enabled: false },
                                    scrollBeyondLastLine: false,
                                    wordWrap: 'on',
                                    roundedSelection: false,
                                    automaticLayout: true,
                                }}
                            />
                        </div>
                        <div className="form-actions">
                            <button className="btn-primary" onClick={saveStrategy} disabled={codeLoading}>
                                {codeLoading ? 'Saving...' : 'Save Strategy'}
                            </button>
                        </div>
                    </section>
                )}

            </main>

            {isPlotMaximized && result?.plot_url && (
                <div className="plot-overlay" onClick={() => setIsPlotMaximized(false)}>
                    <div className="plot-overlay-content" onClick={(e) => e.stopPropagation()}>
                        <div className="plot-overlay-actions">
                            <div className="plot-overlay-controls">
                                <button
                                    type="button"
                                    className="btn-ghost"
                                    onClick={() => setPlotScale((s) => Math.max(0.5, +(s - 0.1).toFixed(2)))}
                                >
                                    -
                                </button>
                                <input
                                    type="range"
                                    min="0.5"
                                    max="2.5"
                                    step="0.1"
                                    value={plotScale}
                                    onChange={(e) => setPlotScale(parseFloat(e.target.value))}
                                />
                                <button
                                    type="button"
                                    className="btn-ghost"
                                    onClick={() => setPlotScale((s) => Math.min(2.5, +(s + 0.1).toFixed(2)))}
                                >
                                    +
                                </button>
                                <button
                                    type="button"
                                    className="btn-ghost"
                                    onClick={() => setPlotScale(1)}
                                >
                                    Reset
                                </button>
                            </div>
                            <button
                                type="button"
                                className="btn-ghost"
                                onClick={() => setIsPlotMaximized(false)}
                            >
                                Close
                            </button>
                        </div>
                        <div className="plot-overlay-viewport">
                            <img
                                src={result.plot_url}
                                alt="Strategy Plot Enlarged"
                                style={{ transform: `scale(${plotScale})` }}
                            />
                        </div>
                    </div>
                </div>
            )}

            <footer className="footer">
                <p>Built with Backtrader & React</p>
            </footer>
        </div>
    )
}

export default App
