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
    BarChartOutlined,
    InfoCircleOutlined
} from '@ant-design/icons';
import { Tooltip, Tag } from 'antd';

/**
 * Get Sharpe Ratio rating
 * @param {number} sharpe - Sharpe ratio value
 * @param {function} t - Translation function
 * @returns {{ label: string, color: string } | null}
 */
function getSharpeRating(sharpe, t) {
    if (!isNumber(sharpe)) return null;
    if (sharpe >= 3) return { label: t('performance.rating_superb', '卓越'), color: '#52c41a' };
    if (sharpe >= 2) return { label: t('performance.rating_excellent', '优秀'), color: '#1890ff' };
    if (sharpe >= 1) return { label: t('performance.rating_good', '良好'), color: '#13c2c2' };
    if (sharpe >= 0) return { label: t('performance.rating_average', '一般'), color: '#faad14' };
    return { label: t('performance.rating_poor', '较差'), color: '#ff4d4f' };
}

/**
 * Get SQN rating
 * @param {number} sqn - SQN value
 * @param {function} t - Translation function
 * @returns {{ label: string, color: string } | null}
 */
function getSqnRating(sqn, t) {
    if (!isNumber(sqn)) return null;
    if (sqn >= 5) return { label: t('performance.rating_superb', '卓越'), color: '#52c41a' };
    if (sqn >= 3) return { label: t('performance.rating_excellent', '优秀'), color: '#1890ff' };
    if (sqn >= 2) return { label: t('performance.rating_good', '良好'), color: '#13c2c2' };
    if (sqn >= 1.5) return { label: t('performance.rating_average', '一般'), color: '#faad14' };
    return { label: t('performance.rating_poor', '较差'), color: '#ff4d4f' };
}

/**
 * Get Max Drawdown rating (lower is better)
 * @param {number} drawdown - Max drawdown percentage (as decimal, e.g., 0.1 = 10%)
 * @param {function} t - Translation function
 * @returns {{ label: string, color: string } | null}
 */
function getDrawdownRating(drawdown, t) {
    if (!isNumber(drawdown)) return null;
    const dd = Math.abs(drawdown);
    if (dd <= 0.05) return { label: t('performance.rating_superb', '卓越'), color: '#52c41a' };
    if (dd <= 0.10) return { label: t('performance.rating_excellent', '优秀'), color: '#1890ff' };
    if (dd <= 0.20) return { label: t('performance.rating_good', '良好'), color: '#13c2c2' };
    if (dd <= 0.30) return { label: t('performance.rating_average', '一般'), color: '#faad14' };
    return { label: t('performance.rating_poor', '较差'), color: '#ff4d4f' };
}

/**
 * Get VWR (Volatility Weighted Return) rating
 * @param {number} vwr - VWR value
 * @param {function} t - Translation function
 * @returns {{ label: string, color: string } | null}
 */
function getVwrRating(vwr, t) {
    if (!isNumber(vwr)) return null;
    if (vwr >= 2) return { label: t('performance.rating_superb', '卓越'), color: '#52c41a' };
    if (vwr >= 1) return { label: t('performance.rating_excellent', '优秀'), color: '#1890ff' };
    if (vwr >= 0.5) return { label: t('performance.rating_good', '良好'), color: '#13c2c2' };
    if (vwr >= 0) return { label: t('performance.rating_average', '一般'), color: '#faad14' };
    return { label: t('performance.rating_poor', '较差'), color: '#ff4d4f' };
}

/**
 * Get Calmar Ratio rating
 * @param {number} calmar - Calmar ratio value
 * @param {function} t - Translation function
 * @returns {{ label: string, color: string } | null}
 */
function getCalmarRating(calmar, t) {
    if (!isNumber(calmar)) return null;
    if (calmar >= 3) return { label: t('performance.rating_superb', '卓越'), color: '#52c41a' };
    if (calmar >= 2) return { label: t('performance.rating_excellent', '优秀'), color: '#1890ff' };
    if (calmar >= 1) return { label: t('performance.rating_good', '良好'), color: '#13c2c2' };
    if (calmar >= 0.5) return { label: t('performance.rating_average', '一般'), color: '#faad14' };
    return { label: t('performance.rating_poor', '较差'), color: '#ff4d4f' };
}

/**
 * MetricCard Component - Premium styled card with icon, optional tooltip and rating tag
 */
function MetricCard({ icon, label, value, valueClass = '', bgVariant = '', tooltip = '', ratingTag = null }) {
    const classes = ['metric-card'];
    if (bgVariant) classes.push(bgVariant);

    return (
        <div className={classes.join(' ')}>
            <div className="metric-card-header">
                <div className="metric-card-icon">
                    {icon}
                </div>
            </div>
            <div className={`metric-card-value ${valueClass}`}>
                {value}
                {ratingTag && (
                    <Tag
                        color={ratingTag.color}
                        style={{
                            marginLeft: 8,
                            fontSize: '11px',
                            padding: '0 6px',
                            borderRadius: '10px',
                            fontWeight: 500,
                            verticalAlign: 'middle'
                        }}
                    >
                        {ratingTag.label}
                    </Tag>
                )}
            </div>
            <div className="metric-card-label">
                {label}
                {tooltip && (
                    <Tooltip title={tooltip}>
                        <InfoCircleOutlined style={{ marginLeft: 4, color: '#64748b', cursor: 'help', fontSize: '12px' }} />
                    </Tooltip>
                )}
            </div>
        </div>
    );
}

MetricCard.propTypes = {
    icon: PropTypes.node.isRequired,
    label: PropTypes.string.isRequired,
    value: PropTypes.string.isRequired,
    valueClass: PropTypes.string,
    bgVariant: PropTypes.string,
    tooltip: PropTypes.string,
    ratingTag: PropTypes.shape({
        label: PropTypes.string,
        color: PropTypes.string
    })
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
                    tooltip={t('performance.final_value_desc')}
                />
                <MetricCard
                    icon={metrics.returns >= 0 ? <RiseOutlined /> : <FallOutlined />}
                    label={t('performance.return')}
                    value={formatPercent(metrics.returns)}
                    valueClass={returnClass}
                    bgVariant={returnBg}
                    tooltip={t('performance.return_desc')}
                />
                <MetricCard
                    icon={<LineChartOutlined />}
                    label={t('performance.sharpe_ratio')}
                    value={formatNumber(metrics.sharpe)}
                    bgVariant="neutral-bg"
                    tooltip={t('performance.sharpe_ratio_desc')}
                    ratingTag={getSharpeRating(metrics.sharpe, t)}
                />
                <MetricCard
                    icon={<FallOutlined />}
                    label={t('performance.max_drawdown')}
                    value={formatPercent(metrics.drawdown)}
                    valueClass="negative"
                    bgVariant="negative-bg"
                    tooltip={t('performance.max_drawdown_desc')}
                    ratingTag={getDrawdownRating(metrics.drawdown, t)}
                />
                <MetricCard
                    icon={<ThunderboltOutlined />}
                    label={t('performance.sqn')}
                    value={formatNumber(metrics.sqn)}
                    tooltip={t('performance.sqn_desc')}
                    ratingTag={getSqnRating(metrics.sqn, t)}
                />
                <MetricCard
                    icon={<TrophyOutlined />}
                    label={t('performance.win_rate')}
                    value={formatPercent(winRate)}
                    valueClass={winRateClass}
                    bgVariant={winRateBg}
                    tooltip={t('performance.win_rate_desc')}
                />
                <MetricCard
                    icon={<SwapOutlined />}
                    label={t('performance.closed_trades')}
                    value={isNumber(closedTrades) ? String(closedTrades) : t('common.na')}
                    tooltip={t('performance.closed_trades_desc')}
                />
                <MetricCard
                    icon={<FieldTimeOutlined />}
                    label={t('performance.dd_duration')}
                    value={isNumber(maxDrawDuration) ? `${Math.round(maxDrawDuration)} ${t('performance.bars')}` : t('common.na')}
                    tooltip={t('performance.dd_duration_desc')}
                />
                <MetricCard
                    icon={<LineChartOutlined />}
                    label={t('performance.calmar', 'Calmar Ratio')}
                    value={formatNumber(metrics.calmar)}
                    bgVariant="neutral-bg"
                    tooltip={t('performance.calmar_desc')}
                    ratingTag={getCalmarRating(metrics.calmar, t)}
                />
                <MetricCard
                    icon={<BarChartOutlined />}
                    label={t('performance.vwr', 'VWR')}
                    value={formatNumber(metrics.vwr)}
                    bgVariant="neutral-bg"
                    tooltip={t('performance.vwr_desc')}
                    ratingTag={getVwrRating(metrics.vwr, t)}
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
