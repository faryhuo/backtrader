import { useTranslation } from 'react-i18next';
import PropTypes from 'prop-types';
import {
    BankOutlined,
    LineChartOutlined,
    DollarOutlined,
    InfoCircleOutlined,
    ClockCircleOutlined
} from '@ant-design/icons';
import './TickerInfoPanel.css';

function TickerInfoPanel({ tickerInfo }) {
    const { t } = useTranslation();

    // Helper: Format large numbers (market cap, volume)
    const formatLargeNumber = (num) => {
        if (!num) return 'N/A';
        if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
        if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
        if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
        if (num >= 1e3) return `$${(num / 1e3).toFixed(2)}K`;
        return `$${num.toFixed(2)}`;
    };

    // Helper: Format percentage
    const formatPercent = (num) => {
        if (num === null || num === undefined) return 'N/A';
        return `${(num * 100).toFixed(2)}%`;
    };

    // Helper: Format decimal
    const formatDecimal = (num, decimals = 2) => {
        if (num === null || num === undefined) return 'N/A';
        return num.toFixed(decimals);
    };

    return (
        <div className="ticker-info-panel">
            {/* Company Header Card */}
            <div className="card ticker-info-card">
                <div className="ticker-header">
                    <h2>{tickerInfo.long_name || tickerInfo.ticker}</h2>
                    <span className="ticker-symbol">{tickerInfo.ticker}</span>
                </div>

                {tickerInfo.sector && (
                    <div className="ticker-basics">
                        <div className="info-row">
                            <BankOutlined className="info-icon" />
                            <span className="info-label">{t('datasource.sector')}:</span>
                            <span className="info-value">{tickerInfo.sector}</span>
                        </div>
                        {tickerInfo.industry && (
                            <div className="info-row">
                                <span className="info-label">{t('datasource.industry')}:</span>
                                <span className="info-value">{tickerInfo.industry}</span>
                            </div>
                        )}
                        {tickerInfo.website && (
                            <div className="info-row">
                                <a href={tickerInfo.website} target="_blank" rel="noopener noreferrer" className="info-link">
                                    {t('datasource.website')}
                                </a>
                            </div>
                        )}
                    </div>
                )}

                {tickerInfo.long_business_summary && (
                    <div className="ticker-description">
                        <p>{tickerInfo.long_business_summary}</p>
                    </div>
                )}
            </div>

            {/* Three Metrics Cards in a Row */}
            <div className="ticker-metrics-row">
                {/* Market Metrics Card */}
                <div className="card ticker-info-card">
                    <h3><LineChartOutlined /> {t('datasource.market_metrics')}</h3>
                    <div className="metrics-grid">
                        <div className="metric-item">
                            <span className="metric-label">{t('datasource.market_cap')}</span>
                            <span className="metric-value">{formatLargeNumber(tickerInfo.market_cap)}</span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">{t('datasource.pe_ratio')}</span>
                            <span className="metric-value">{formatDecimal(tickerInfo.trailing_pe)}</span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">{t('datasource.beta')}</span>
                            <span className="metric-value">{formatDecimal(tickerInfo.beta)}</span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">{t('datasource.52w_high')}</span>
                            <span className="metric-value">${formatDecimal(tickerInfo.fifty_two_week_high)}</span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">{t('datasource.52w_low')}</span>
                            <span className="metric-value">${formatDecimal(tickerInfo.fifty_two_week_low)}</span>
                        </div>
                    </div>
                </div>

                {/* Trading Statistics Card */}
                <div className="card ticker-info-card">
                    <h3><DollarOutlined /> {t('datasource.trading_stats')}</h3>
                    <div className="metrics-grid">
                        <div className="metric-item">
                            <span className="metric-label">{t('datasource.current_price')}</span>
                            <span className="metric-value metric-price">${formatDecimal(tickerInfo.current_price)}</span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">{t('datasource.previous_close')}</span>
                            <span className="metric-value">${formatDecimal(tickerInfo.previous_close)}</span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">{t('datasource.day_range')}</span>
                            <span className="metric-value">
                                ${formatDecimal(tickerInfo.day_low)} - ${formatDecimal(tickerInfo.day_high)}
                            </span>
                        </div>
                        <div className="metric-item">
                            <span className="metric-label">{t('datasource.avg_volume')}</span>
                            <span className="metric-value">{formatLargeNumber(tickerInfo.average_volume)}</span>
                        </div>
                    </div>
                </div>

                {/* Fundamental Data Card */}
                {(tickerInfo.dividend_yield || tickerInfo.trailing_eps) && (
                    <div className="card ticker-info-card">
                        <h3><InfoCircleOutlined /> {t('datasource.fundamentals')}</h3>
                        <div className="metrics-grid">
                            {tickerInfo.dividend_yield && (
                                <div className="metric-item">
                                    <span className="metric-label">{t('datasource.dividend_yield')}</span>
                                    <span className="metric-value">{formatPercent(tickerInfo.dividend_yield)}</span>
                                </div>
                            )}
                            {tickerInfo.trailing_eps && (
                                <div className="metric-item">
                                    <span className="metric-label">{t('datasource.eps')}</span>
                                    <span className="metric-value">${formatDecimal(tickerInfo.trailing_eps)}</span>
                                </div>
                            )}
                            {tickerInfo.profit_margins && (
                                <div className="metric-item">
                                    <span className="metric-label">{t('datasource.profit_margins')}</span>
                                    <span className="metric-value">{formatPercent(tickerInfo.profit_margins)}</span>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* Cache Indicator */}
            {tickerInfo.cached && (
                <div className="cache-indicator">
                    <ClockCircleOutlined />
                    <span>{t('datasource.cached_data')}: {tickerInfo.cache_age_days} {t('datasource.days_old')}</span>
                </div>
            )}
        </div>
    );
}

TickerInfoPanel.propTypes = {
    tickerInfo: PropTypes.shape({
        ticker: PropTypes.string.isRequired,
        is_valid: PropTypes.bool.isRequired,
        long_name: PropTypes.string,
        short_name: PropTypes.string,
        sector: PropTypes.string,
        industry: PropTypes.string,
        market_cap: PropTypes.number,
        trailing_pe: PropTypes.number,
        beta: PropTypes.number,
        fifty_two_week_high: PropTypes.number,
        fifty_two_week_low: PropTypes.number,
        current_price: PropTypes.number,
        dividend_yield: PropTypes.number,
        trailing_eps: PropTypes.number,
        average_volume: PropTypes.number,
        long_business_summary: PropTypes.string,
        website: PropTypes.string,
        cached: PropTypes.bool,
        cache_age_days: PropTypes.number
    }).isRequired
};

export default TickerInfoPanel;
