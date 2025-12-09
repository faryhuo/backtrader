import PropTypes from 'prop-types';
import { formatCurrency, formatPercent, formatNumber, isNumber } from '../utils/formatters';

function PerformanceOverview({ result }) {
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
            </div>
        </section>
    );
}

PerformanceOverview.propTypes = {
    result: PropTypes.object
};

export default PerformanceOverview;
