import { useState, useEffect } from 'react'
import '../index.css'
import { api } from '../services/api'

function RunStrategy() {
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
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    // AI Analysis State
    const [aiLoading, setAiLoading] = useState(false)
    const [aiAnalysis, setAiAnalysis] = useState('')

    useEffect(() => {
        const init = async () => {
            const names = await fetchStrategies();
            if (names && names.length > 0) {
                if (!names.includes(selectedStrategy)) {
                    setSelectedStrategy(names[0]);
                }
            }
        }
        init();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    const isNumber = (value) => typeof value === 'number' && !Number.isNaN(value)
    const formatNumber = (value, digits = 2) => isNumber(value) ? value.toFixed(digits) : 'N/A'
    const formatPercent = (value, digits = 2, multiplier = 1) =>
        isNumber(value) ? `${(value * multiplier).toFixed(digits)}%` : 'N/A'
    const formatCurrency = (value, digits = 2) =>
        isNumber(value)
            ? `$${value.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits })}`
            : 'N/A'

    const fetchStrategies = async () => {
        try {
            const names = await api.getStrategies()
            setStrategies(names)
            return names
        } catch (err) {
            console.error("Failed to fetch strategies", err)
            return []
        }
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
            const data = await api.runBacktest({
                ticker,
                start_date: startDate,
                end_date: endDate,
                initial_cash: parseFloat(initialCash),
                commission: parseFloat(commission),
                stake: parseInt(stake, 10),
                strategy_name: selectedStrategy
            })
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
            const data = await api.analyzeResults(result.metrics)
            setAiAnalysis(data.analysis);
        } catch (err) {
            setAiAnalysis("Failed to perform AI analysis.");
        } finally {
            setAiLoading(false);
        }
    }

    const metrics = result?.metrics || {}
    const trades = metrics.trades || {}
    const totalTrades = trades.total?.total ?? 0
    const closedTrades = trades.total?.closed ?? 0
    const openTrades = trades.total?.open ?? 0
    const wins = trades.won?.total ?? 0
    const winRate = closedTrades ? (wins / closedTrades) * 100 : null
    const winRateColor = isNumber(winRate) ? (winRate >= 50 ? 'green' : 'red') : ''
    const winRateTone = isNumber(winRate) ? (winRate >= 50 ? 'positive' : 'negative') : ''
    const avgNetPnl = trades.pnl?.net?.average
    const totalNetPnl = trades.pnl?.net?.total
    const bestTrade = trades.won?.pnl?.max
    const worstTrade = trades.lost?.pnl?.max
    const bestTradeClass = isNumber(bestTrade) ? 'positive' : ''
    const worstTradeClass = isNumber(worstTrade) ? 'negative' : ''
    const avgTradeLen = trades.len?.average
    const annualEntries = Object.entries(metrics.annual_returns || {}).sort((a, b) => Number(a[0]) - Number(b[0]))
    const maxDrawDuration = metrics.time_drawdown?.maxdrawdownperiod
    const maxDrawdownValue = metrics.time_drawdown?.maxdrawdown ?? metrics.drawdown
    const netPnlClass = isNumber(totalNetPnl) ? (totalNetPnl >= 0 ? 'positive' : 'negative') : ''

    return (
        <div className="page-container">
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
                                <span className="stat-value highlight">{formatCurrency(metrics.final_value)}</span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-label">Return</span>
                                <span className={`stat-value ${metrics.returns >= 0 ? 'green' : 'red'}`}>
                                    {formatPercent(metrics.returns)}
                                </span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-label">Sharpe Ratio</span>
                                <span className="stat-value highlight">
                                    {formatNumber(metrics.sharpe)}
                                </span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-label">Max Drawdown</span>
                                <span className="stat-value red">
                                    {formatPercent(metrics.drawdown)}
                                </span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-label">SQN</span>
                                <span className="stat-value highlight">
                                    {formatNumber(metrics.sqn)}
                                </span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-label">Win Rate</span>
                                <span className={`stat-value ${winRateColor}`}>
                                    {formatPercent(winRate)}
                                </span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-label">Closed Trades</span>
                                <span className="stat-value highlight">
                                    {isNumber(closedTrades) ? closedTrades : 'N/A'}
                                </span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-label">DD Duration</span>
                                <span className="stat-value">
                                    {isNumber(maxDrawDuration) ? `${Math.round(maxDrawDuration)} bars` : 'N/A'}
                                </span>
                            </div>
                        </div>

                        <div className="detail-card">
                            <div className="detail-grid">
                                <div className="detail-column">
                                    <div className="detail-header">
                                        <h3>Annual Returns</h3>
                                        <span className="muted">per calendar year</span>
                                    </div>
                                    <div className="annual-returns">
                                        {annualEntries.length > 0 ? (
                                            annualEntries.map(([year, value]) => (
                                                <div
                                                    key={year}
                                                    className={`annual-chip ${value >= 0 ? 'positive' : 'negative'}`}
                                                >
                                                    <span className="chip-year">{year}</span>
                                                    <span className="chip-value">{formatPercent(value, 2, 100)}</span>
                                                </div>
                                            ))
                                        ) : (
                                            <p className="muted">No annual return data available.</p>
                                        )}
                                    </div>
                                </div>

                                <div className="detail-column">
                                    <div className="detail-header">
                                        <h3>Trades</h3>
                                        <span className="muted">from TradeAnalyzer</span>
                                    </div>
                                    <ul className="metric-list">
                                        <li>
                                            <span className="metric-label">Closed / Total</span>
                                            <span className="metric-value">{closedTrades} / {totalTrades}</span>
                                        </li>
                                        <li>
                                            <span className="metric-label">Open Positions</span>
                                            <span className="metric-value">{openTrades}</span>
                                        </li>
                                        <li>
                                            <span className="metric-label">Average Net PnL</span>
                                            <span className="metric-value">{formatCurrency(avgNetPnl)}</span>
                                        </li>
                                        <li>
                                            <span className="metric-label">Best Trade</span>
                                            <span className={`metric-value ${bestTradeClass}`}>{formatCurrency(bestTrade)}</span>
                                        </li>
                                        <li>
                                            <span className="metric-label">Worst Trade</span>
                                            <span className={`metric-value ${worstTradeClass}`}>{formatCurrency(worstTrade)}</span>
                                        </li>
                                        <li>
                                            <span className="metric-label">Win Rate</span>
                                            <span className={`metric-value ${winRateTone}`}>
                                                {formatPercent(winRate)}
                                            </span>
                                        </li>
                                        <li>
                                            <span className="metric-label">Avg Duration (bars)</span>
                                            <span className="metric-value">
                                                {isNumber(avgTradeLen) ? avgTradeLen.toFixed(1) : 'N/A'}
                                            </span>
                                        </li>
                                    </ul>
                                </div>

                                <div className="detail-column">
                                    <div className="detail-header">
                                        <h3>Time Drawdown</h3>
                                        <span className="muted">depth and duration</span>
                                    </div>
                                    <ul className="metric-list">
                                        <li>
                                            <span className="metric-label">Max Drawdown</span>
                                            <span className="metric-value negative">{formatPercent(maxDrawdownValue)}</span>
                                        </li>
                                        <li>
                                            <span className="metric-label">Longest Duration</span>
                                            <span className="metric-value">
                                                {isNumber(maxDrawDuration) ? `${Math.round(maxDrawDuration)} bars` : 'N/A'}
                                            </span>
                                        </li>
                                        <li>
                                            <span className="metric-label">Net PnL</span>
                                            <span className={`metric-value ${netPnlClass}`}>
                                                {formatCurrency(totalNetPnl)}
                                            </span>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        </div>

                        <div className="ai-section">
                            <button className="btn-secondary" onClick={handleAnalyze} disabled={aiLoading}>
                                {aiLoading ? 'Analyzing...' : 'AI Analysis'}
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
        </div>
    )
}

export default RunStrategy
