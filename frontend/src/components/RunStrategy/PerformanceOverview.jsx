import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import { formatCurrency, formatPercent, formatNumber, isNumber } from '../../utils/formatters';
import {
    DollarOutlined,
    RiseOutlined,
    FallOutlined,
    LineChartOutlined,
    ThunderboltOutlined,
    TrophyOutlined,
    SwapOutlined,
    FieldTimeOutlined,
    CalendarOutlined,
    BarChartOutlined
} from '@ant-design/icons';

/**
 * MetricCard Component - Premium styled card with icon
 */
function MetricCard({ icon, label, value, valueClass = '', bgVariant = '' }) {
    const classes = ['metric-card'];
    if (bgVariant) classes.push(bgVariant);

    return (
        <div className={classes.join(' ')}>
            <div className="metric-card-header">
                <div className="metric-card-icon">
                    {icon}
                </div>
            </div>
            <div className={`metric-card-value ${valueClass}`}>{value}</div>
            <div className="metric-card-label">{label}</div>
        </div>
    );
}

MetricCard.propTypes = {
    icon: PropTypes.node.isRequired,
    label: PropTypes.string.isRequired,
    value: PropTypes.string.isRequired,
    valueClass: PropTypes.string,
    bgVariant: PropTypes.string
};

function PerformanceOverview({ result }) {
    const { t } = useTranslation();
    const metrics = result?.metrics || {}
    const trades = metrics.trades || {}
    const closedTrades = trades.total?.closed ?? 0
    const wins = trades.won?.total ?? 0
    const winRate = closedTrades ? (wins / closedTrades) * 100 : null
    const winRateClass = isNumber(winRate) ? (winRate >= 50 ? 'positive' : 'negative') : ''
    const winRateBg = isNumber(winRate) ? (winRate >= 50 ? 'positive-bg' : 'negative-bg') : ''
    const returnClass = metrics.returns >= 0 ? 'positive' : 'negative'
    const returnBg = metrics.returns >= 0 ? 'positive-bg' : 'negative-bg'
    const avgNetPnl = trades.pnl?.net?.average
    const totalNetPnl = trades.pnl?.net?.total
    const bestTrade = trades.won?.pnl?.max
    const worstTrade = trades.lost?.pnl?.max
    const avgTradeLen = trades.len?.average
    const annualEntries = Object.entries(metrics.annual_returns || {}).sort((a, b) => Number(a[0]) - Number(b[0]))
    const maxDrawDuration = metrics.time_drawdown?.maxdrawdownperiod
    const maxDrawdownValue = metrics.time_drawdown?.maxdrawdown ?? metrics.drawdown
    const netPnlClass = isNumber(totalNetPnl) ? (totalNetPnl >= 0 ? 'positive' : 'negative') : ''

    return (
        <section className="results-section">
            {/* Premium 4-column Metric Cards Grid */}
            <div className="metric-cards-grid">
                <MetricCard
                    icon={<DollarOutlined />}
                    label={t('performance.final_value')}
                    value={formatCurrency(metrics.final_value)}
                    bgVariant="neutral-bg"
                />
                <MetricCard
                    icon={metrics.returns >= 0 ? <RiseOutlined /> : <FallOutlined />}
                    label={t('performance.return')}
                    value={formatPercent(metrics.returns)}
                    valueClass={returnClass}
                    bgVariant={returnBg}
                />
                <MetricCard
                    icon={<LineChartOutlined />}
                    label={t('performance.sharpe_ratio')}
                    value={formatNumber(metrics.sharpe)}
                    bgVariant="neutral-bg"
                />
                <MetricCard
                    icon={<FallOutlined />}
                    label={t('performance.max_drawdown')}
                    value={formatPercent(metrics.drawdown)}
                    valueClass="negative"
                    bgVariant="negative-bg"
                />
                <MetricCard
                    icon={<ThunderboltOutlined />}
                    label={t('performance.sqn')}
                    value={formatNumber(metrics.sqn)}
                />
                <MetricCard
                    icon={<TrophyOutlined />}
                    label={t('performance.win_rate')}
                    value={formatPercent(winRate)}
                    valueClass={winRateClass}
                    bgVariant={winRateBg}
                />
                <MetricCard
                    icon={<SwapOutlined />}
                    label={t('performance.closed_trades')}
                    value={isNumber(closedTrades) ? String(closedTrades) : t('common.na')}
                />
                <MetricCard
                    icon={<FieldTimeOutlined />}
                    label={t('performance.dd_duration')}
                    value={isNumber(maxDrawDuration) ? `${Math.round(maxDrawDuration)} ${t('performance.bars')}` : t('common.na')}
                />
            </div>

            {/* Details Two-Column Layout */}
            <div className="details-two-column">
                {/* Annual Returns */}
                <div className="details-section-card">
                    <div className="details-section-header">
                        <h3 className="details-section-title">
                            <CalendarOutlined />
                            {t('performance.annual_returns')}
                        </h3>
                        <span className="details-section-subtitle">{t('performance.per_calendar_year')}</span>
                    </div>
                    <div className="annual-returns">
                        {annualEntries.length > 0 ? (
                            annualEntries.map(([year, value]) => (
                                <div
                                    key={year}
                                    className={`annual-chip ${value >= 0 ? 'positive' : 'negative'}`}
                                >
                                    <span className="chip-year">{year}</span>
                                    <span className={`chip-value ${value >= 0 ? 'positive' : 'negative'}`}>
                                        {formatPercent(value, 2, 100)}
                                    </span>
                                </div>
                            ))
                        ) : (
                            <p className="muted">{t('common.na')}</p>
                        )}
                    </div>
                </div>

                {/* Trade Statistics */}
                <div className="details-section-card">
                    <div className="details-section-header">
                        <h3 className="details-section-title">
                            <BarChartOutlined />
                            {t('performance.trades')}
                        </h3>
                        <span className="details-section-subtitle">{t('performance.from_trade_analyzer')}</span>
                    </div>
                    <ul className="metric-list">
                        <li>
                            <span className="metric-label">{t('performance.avg_net_pnl')}</span>
                            <span className="metric-value">{formatCurrency(avgNetPnl)}</span>
                        </li>
                        <li>
                            <span className="metric-label">{t('performance.best_trade')}</span>
                            <span className="metric-value positive">{formatCurrency(bestTrade)}</span>
                        </li>
                        <li>
                            <span className="metric-label">{t('performance.worst_trade')}</span>
                            <span className="metric-value negative">{formatCurrency(worstTrade)}</span>
                        </li>
                        <li>
                            <span className="metric-label">{t('performance.net_pnl')}</span>
                            <span className={`metric-value ${netPnlClass}`}>{formatCurrency(totalNetPnl)}</span>
                        </li>
                        <li>
                            <span className="metric-label">{t('performance.avg_duration')}</span>
                            <span className="metric-value">
                                {isNumber(avgTradeLen) ? avgTradeLen.toFixed(1) : t('common.na')}
                            </span>
                        </li>
                        <li>
                            <span className="metric-label">{t('performance.max_drawdown')}</span>
                            <span className="metric-value negative">{formatPercent(maxDrawdownValue)}</span>
                        </li>
                    </ul>
                </div>
            </div>
        </section>
    );
}

PerformanceOverview.propTypes = {
    result: PropTypes.object
};

export default PerformanceOverview;
