import { Card, Tooltip, Row, Col, Divider } from 'antd';
import {
    PieChartOutlined,
    RiseOutlined,
    FallOutlined,
    DollarOutlined,
    LineChartOutlined,
    ThunderboltOutlined,
    TrophyOutlined,
    WarningOutlined,
    PercentageOutlined,
    SwapOutlined,
} from '@ant-design/icons';

/**
 * Portfolio metrics display card with expanded metrics
 */
function PortfolioMetricsCard({ t, metrics }) {
    // Extract metrics from nested structure
    const portfolioMetrics = metrics?.metrics?.portfolio_metrics || {};
    // Helper to format percentage
    const formatPct = (value, decimals = 2) => {
        return value !== null && value !== undefined ? `${(value * 100).toFixed(decimals)}%` : 'N/A';
    };

    // Helper to format number
    const formatNum = (value, decimals = 2) => {
        return value !== null && value !== undefined ? value.toFixed(decimals) : 'N/A';
    };

    // Helper to format currency
    const formatCurrency = (value) => {
        return value !== null && value !== undefined ? `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : 'N/A';
    };

    const MetricItem = ({ label, value, icon, tooltip, valueClassName = "" }) => (
        <div className="metric-item">
            <Tooltip title={tooltip}>
                <span className="metric-label">
                    {icon && <span className="metric-icon">{icon}</span>}
                    {label}
                </span>
            </Tooltip>
            <span className={`metric-value ${valueClassName}`}>{value}</span>
        </div>
    );

    return (
        <Card className="portfolio-metrics-card" title={
            <span><PieChartOutlined /> {t('portfolio.portfolio_metrics', 'Portfolio Metrics')}</span>
        }>
            {/* Overview Section */}
            <div className="metrics-section">
                <h4 className="section-title">{t('portfolio.overview', 'Overview')}</h4>
                <Row gutter={[16, 16]}>
                    <Col xs={24} sm={12} md={8}>
                        <MetricItem
                            label={t('portfolio.initial_cash', 'Initial Cash')}
                            value={formatCurrency(metrics?.initial_cash)}
                            icon={<DollarOutlined />}
                            tooltip={t('portfolio.initial_cash_desc', 'Starting portfolio capital')}
                        />
                    </Col>
                    <Col xs={24} sm={12} md={8}>
                        <MetricItem
                            label={t('portfolio.final_value', 'Final Value')}
                            value={formatCurrency(metrics?.final_value)}
                            icon={<DollarOutlined />}
                            tooltip={t('portfolio.final_value_desc', 'Ending portfolio value')}
                        />
                    </Col>
                    <Col xs={24} sm={12} md={8}>
                        <MetricItem
                            label={t('portfolio.total_return', 'Total Return')}
                            value={`${formatNum(metrics?.total_return)}%`}
                            icon={metrics?.total_return >= 0 ? <RiseOutlined /> : <FallOutlined />}
                            valueClassName={metrics?.total_return >= 0 ? 'positive' : 'negative'}
                            tooltip={t('portfolio.total_return_desc', 'Total portfolio return percentage')}
                        />
                    </Col>
                </Row>
            </div>

            <Divider />

            {/* Risk-Adjusted Returns */}
            <div className="metrics-section">
                <h4 className="section-title">{t('portfolio.risk_adjusted', 'Risk-Adjusted Returns')}</h4>
                <Row gutter={[16, 16]}>
                    <Col xs={24} sm={12} md={6}>
                        <MetricItem
                            label={t('portfolio.sharpe_ratio', 'Sharpe Ratio')}
                            value={formatNum(metrics?.sharpe_ratio)}
                            icon={<LineChartOutlined />}
                            tooltip={t('portfolio.sharpe_desc', 'Risk-adjusted return (higher is better)')}
                        />
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                        <MetricItem
                            label={t('portfolio.sortino_ratio', 'Sortino Ratio')}
                            value={formatNum(portfolioMetrics?.sortino_ratio)}
                            icon={<LineChartOutlined />}
                            tooltip={t('portfolio.sortino_desc', 'Downside risk-adjusted return')}
                        />
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                        <MetricItem
                            label={t('portfolio.calmar_ratio', 'Calmar Ratio')}
                            value={formatNum(metrics?.calmar_ratio)}
                            icon={<LineChartOutlined />}
                            tooltip={t('portfolio.calmar_desc', 'Annual return / max drawdown')}
                        />
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                        <MetricItem
                            label={t('portfolio.recovery_factor', 'Recovery Factor')}
                            value={formatNum(metrics?.recovery_factor)}
                            icon={<ThunderboltOutlined />}
                            tooltip={t('portfolio.recovery_desc', 'Net profit / max drawdown')}
                        />
                    </Col>
                </Row>
            </div>

            <Divider />

            {/* Risk Metrics */}
            <div className="metrics-section">
                <h4 className="section-title">{t('portfolio.risk_metrics', 'Risk Metrics')}</h4>
                <Row gutter={[16, 16]}>
                    <Col xs={24} sm={12} md={8}>
                        <MetricItem
                            label={t('portfolio.max_drawdown', 'Max Drawdown')}
                            value={`${formatNum(metrics?.max_drawdown)}%`}
                            icon={<FallOutlined />}
                            valueClassName="negative"
                            tooltip={t('portfolio.max_dd_desc', 'Maximum peak-to-trough decline')}
                        />
                    </Col>
                    <Col xs={24} sm={12} md={8}>
                        <MetricItem
                            label={t('portfolio.annual_volatility', 'Annual Volatility')}
                            value={formatPct(portfolioMetrics?.annual_volatility)}
                            icon={<WarningOutlined />}
                            tooltip={t('portfolio.volatility_desc', 'Annualized standard deviation of returns')}
                        />
                    </Col>
                    <Col xs={24} sm={12} md={8}>
                        <MetricItem
                            label={t('portfolio.var_95', 'VaR (95%)')}
                            value={formatPct(portfolioMetrics?.var_95)}
                            icon={<WarningOutlined />}
                            tooltip={t('portfolio.var_desc', 'Value at Risk at 95% confidence level')}
                        />
                    </Col>
                </Row>
            </div>

            <Divider />

            {/* Return Statistics */}
            <div className="metrics-section">
                <h4 className="section-title">{t('portfolio.return_stats', 'Return Statistics')}</h4>
                <Row gutter={[16, 16]}>
                    <Col xs={24} sm={12} md={6}>
                        <MetricItem
                            label={t('portfolio.annual_return', 'Annual Return')}
                            value={formatPct(portfolioMetrics?.annual_return)}
                            icon={<RiseOutlined />}
                            valueClassName={portfolioMetrics?.annual_return >= 0 ? 'positive' : 'negative'}
                            tooltip={t('portfolio.annual_return_desc', 'Annualized return percentage')}
                        />
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                        <MetricItem
                            label={t('portfolio.win_rate', 'Win Rate')}
                            value={formatPct(portfolioMetrics?.win_rate)}
                            icon={<TrophyOutlined />}
                            tooltip={t('portfolio.win_rate_desc', 'Percentage of positive return days')}
                        />
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                        <MetricItem
                            label={t('portfolio.best_day', 'Best Day')}
                            value={formatPct(portfolioMetrics?.best_day)}
                            icon={<RiseOutlined />}
                            valueClassName="positive"
                            tooltip={t('portfolio.best_day_desc', 'Best single-day return')}
                        />
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                        <MetricItem
                            label={t('portfolio.worst_day', 'Worst Day')}
                            value={formatPct(portfolioMetrics?.worst_day)}
                            icon={<FallOutlined />}
                            valueClassName="negative"
                            tooltip={t('portfolio.worst_day_desc', 'Worst single-day return')}
                        />
                    </Col>
                </Row>
            </div>

            <Divider />

            {/* Trading Costs */}
            <div className="metrics-section">
                <h4 className="section-title">{t('portfolio.trading_costs', 'Trading Activity')}</h4>
                <Row gutter={[16, 16]}>
                    <Col xs={24} sm={12} md={8}>
                        <MetricItem
                            label={t('portfolio.total_trades', 'Total Trades')}
                            value={metrics?.total_trades || 0}
                            icon={<SwapOutlined />}
                            tooltip={t('portfolio.total_trades_desc', 'Total number of trades executed')}
                        />
                    </Col>
                    <Col xs={24} sm={12} md={8}>
                        <MetricItem
                            label={t('portfolio.total_commission', 'Total Commission')}
                            value={formatCurrency(metrics?.total_commission)}
                            icon={<PercentageOutlined />}
                            tooltip={t('portfolio.total_commission_desc', 'Total trading commissions paid')}
                        />
                    </Col>
                    <Col xs={24} sm={12} md={8}>
                        <MetricItem
                            label={t('portfolio.total_volume', 'Total Volume')}
                            value={formatCurrency(metrics?.total_volume)}
                            icon={<DollarOutlined />}
                            tooltip={t('portfolio.total_volume_desc', 'Total dollar volume traded')}
                        />
                    </Col>
                </Row>
            </div>
        </Card>
    );
}

export default PortfolioMetricsCard;
