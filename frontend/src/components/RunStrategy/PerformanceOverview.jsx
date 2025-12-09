import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import { formatCurrency, formatPercent, formatNumber, isNumber } from '../../utils/formatters';

function PerformanceOverview({ result }) {
    const { t } = useTranslation();
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
                <h2>{t('performance.title')}</h2>
                <div className="stats-grid">
                    <div className="stat-item">
                        <span className="stat-label">{t('performance.final_value')}</span>
                        <span className="stat-value highlight">{formatCurrency(metrics.final_value)}</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-label">{t('performance.return')}</span>
                        <span className={`stat-value ${metrics.returns >= 0 ? 'green' : 'red'}`}>
                            {formatPercent(metrics.returns)}
                        </span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-label">{t('performance.sharpe_ratio')}</span>
                        <span className="stat-value highlight">
                            {formatNumber(metrics.sharpe)}
                        </span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-label">{t('performance.max_drawdown')}</span>
                        <span className="stat-value red">
                            {formatPercent(metrics.drawdown)}
                        </span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-label">{t('performance.sqn')}</span>
                        <span className="stat-value highlight">
                            {formatNumber(metrics.sqn)}
                        </span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-label">{t('performance.win_rate')}</span>
                        <span className={`stat-value ${winRateColor}`}>
                            {formatPercent(winRate)}
                        </span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-label">{t('performance.closed_trades')}</span>
                        <span className="stat-value highlight">
                            {isNumber(closedTrades) ? closedTrades : t('common.na')}
                        </span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-label">{t('performance.dd_duration')}</span>
                        <span className="stat-value">
                            {isNumber(maxDrawDuration) ? `${Math.round(maxDrawDuration)} ${t('performance.bars')}` : t('common.na')}
                        </span>
                    </div>
                </div>

                <div className="detail-card">
                    <div className="detail-grid">
                        <div className="detail-column">
                            <div className="detail-header">
                                <h3>{t('performance.annual_returns')}</h3>
                                <span className="muted">{t('performance.per_calendar_year')}</span>
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
                                <h3>{t('performance.trades')}</h3>
                                <span className="muted">{t('performance.from_trade_analyzer')}</span>
                            </div>
                            <ul className="metric-list">
                                <li>
                                    <span className="metric-label">{t('performance.closed_total')}</span>
                                    <span className="metric-value">{closedTrades} / {totalTrades}</span>
                                </li>
                                <li>
                                    <span className="metric-label">{t('performance.open_positions')}</span>
                                    <span className="metric-value">{openTrades}</span>
                                </li>
                                <li>
                                    <span className="metric-label">{t('performance.avg_net_pnl')}</span>
                                    <span className="metric-value">{formatCurrency(avgNetPnl)}</span>
                                </li>
                                <li>
                                    <span className="metric-label">{t('performance.best_trade')}</span>
                                    <span className={`metric-value ${bestTradeClass}`}>{formatCurrency(bestTrade)}</span>
                                </li>
                                <li>
                                    <span className="metric-label">{t('performance.worst_trade')}</span>
                                    <span className={`metric-value ${worstTradeClass}`}>{formatCurrency(worstTrade)}</span>
                                </li>
                                <li>
                                    <span className="metric-label">{t('performance.win_rate')}</span>
                                    <span className={`metric-value ${winRateTone}`}>
                                        {formatPercent(winRate)}
                                    </span>
                                </li>
                                <li>
                                    <span className="metric-label">{t('performance.avg_duration')}</span>
                                    <span className="metric-value">
                                        {isNumber(avgTradeLen) ? avgTradeLen.toFixed(1) : t('common.na')}
                                    </span>
                                </li>
                            </ul>
                        </div>

                        <div className="detail-column">
                            <div className="detail-header">
                                <h3>{t('performance.time_drawdown')}</h3>
                                <span className="muted">{t('performance.depth_duration')}</span>
                            </div>
                            <ul className="metric-list">
                                <li>
                                    <span className="metric-label">{t('performance.max_drawdown')}</span>
                                    <span className="metric-value negative">{formatPercent(maxDrawdownValue)}</span>
                                </li>
                                <li>
                                    <span className="metric-label">{t('performance.longest_duration')}</span>
                                    <span className="metric-value">
                                        {isNumber(maxDrawDuration) ? `${Math.round(maxDrawDuration)} ${t('performance.bars')}` : t('common.na')}
                                    </span>
                                </li>
                                <li>
                                    <span className="metric-label">{t('performance.net_pnl')}</span>
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
