import { Card, Tag, Alert, List, Badge, Divider, Row, Col } from 'antd';
import {
    ThunderboltOutlined,
    BulbOutlined,
    WarningOutlined,
    CheckCircleOutlined,
    InfoCircleOutlined,
} from '@ant-design/icons';

/**
 * Generate optimization insights based on portfolio metrics
 * Handles both live backtest data structure and historical data structure
 */
const generateInsights = (metrics, t) => {
    const insights = [];

    // Handle multiple possible data structures for portfolio metrics
    // Live backtest: metrics.metrics.portfolio_metrics
    // History detail: metrics.portfolio_metrics.portfolio_metrics OR metrics.portfolio_metrics
    const portfolioMetrics =
        metrics?.metrics?.portfolio_metrics ||
        metrics?.portfolio_metrics?.portfolio_metrics ||
        metrics?.portfolio_metrics ||
        {};

    // Risk-adjusted return analysis
    // sharpe_ratio can be at root or in portfolio_metrics
    const sharpeRatio = metrics?.sharpe_ratio || metrics?.weighted_sharpe || portfolioMetrics?.sharpe_ratio || 0;
    const sortinoRatio = portfolioMetrics?.sortino_ratio || 0;
    const calmarRatio = metrics?.calmar_ratio || portfolioMetrics?.calmar_ratio || 0;

    if (sharpeRatio < 0.5) {
        insights.push({
            type: 'warning',
            icon: <WarningOutlined />,
            message: t('portfolio.insights.low_sharpe', 'Low risk-adjusted returns (Sharpe < 0.5). Consider: 1) Reducing position sizes, 2) Adding uncorrelated assets, 3) Adjusting entry/exit criteria.'),
        });
    } else if (sharpeRatio >= 1.0) {
        insights.push({
            type: 'success',
            icon: <CheckCircleOutlined />,
            message: t('portfolio.insights.good_sharpe', 'Excellent risk-adjusted returns (Sharpe ≥ 1.0). Strategy shows strong performance.'),
        });
    }

    // Win rate analysis
    const winRate = portfolioMetrics?.win_rate || 0;
    if (winRate < 0.4 && winRate > 0) {
        insights.push({
            type: 'warning',
            icon: <WarningOutlined />,
            message: t('portfolio.insights.low_win_rate', 'Low win rate (<40%). Consider: 1) Tightening stop-losses, 2) Improving entry timing, 3) Filtering weak signals.'),
        });
    } else if (winRate > 0.6) {
        insights.push({
            type: 'success',
            icon: <CheckCircleOutlined />,
            message: t('portfolio.insights.high_win_rate', 'High win rate (>60%). Good signal quality and timing.'),
        });
    }

    // Volatility analysis
    const annualVol = portfolioMetrics?.annual_volatility || 0;
    if (annualVol > 0.3) {
        insights.push({
            type: 'warning',
            icon: <WarningOutlined />,
            message: t('portfolio.insights.high_volatility', 'High volatility (>30%). Consider: 1) Diversifying across sectors, 2) Adding bonds/cash, 3) Using smaller position sizes.'),
        });
    }

    // Drawdown analysis
    const maxDD = Math.abs(metrics?.max_drawdown || 0);
    if (maxDD > 20) {
        insights.push({
            type: 'error',
            icon: <WarningOutlined />,
            message: t('portfolio.insights.large_drawdown', 'Large drawdown (>20%). Risk management needs improvement. Consider: 1) Portfolio-level stop-loss, 2) Position size limits, 3) Hedging strategies.'),
        });
    }

    // Sortino vs Sharpe comparison
    if (sortinoRatio > sharpeRatio * 1.3) {
        insights.push({
            type: 'info',
            icon: <InfoCircleOutlined />,
            message: t('portfolio.insights.asymmetric_returns', 'Asymmetric returns detected (Sortino >> Sharpe). Strategy handles downside well. Consider increasing position sizes cautiously.'),
        });
    }

    // Recovery factor analysis
    const recoveryFactor = metrics?.recovery_factor || portfolioMetrics?.recovery_factor || 0;
    if (recoveryFactor < 2 && recoveryFactor !== 0) {
        insights.push({
            type: 'warning',
            icon: <WarningOutlined />,
            message: t('portfolio.insights.low_recovery', 'Low recovery factor (<2). Profits may not justify risk. Consider: 1) Better risk/reward setups, 2) Trailing stops, 3) Profit targets.'),
        });
    } else if (recoveryFactor > 5) {
        insights.push({
            type: 'success',
            icon: <CheckCircleOutlined />,
            message: t('portfolio.insights.high_recovery', 'Excellent recovery factor (>5). Strong profit relative to drawdown.'),
        });
    }

    // Trading frequency analysis
    const totalTrades = metrics?.total_trades || portfolioMetrics?.total_trades || 0;
    const numDays = portfolioMetrics?.num_days || 1;
    const tradesPerDay = totalTrades / numDays;

    if (tradesPerDay > 2) {
        const commission = metrics?.total_commission || portfolioMetrics?.total_commission || 0;
        insights.push({
            type: 'info',
            icon: <InfoCircleOutlined />,
            message: t('portfolio.insights.high_frequency', 'High trading frequency detected. Monitor transaction costs carefully. Commission impact: $' + commission.toFixed(2)),
        });
    }

    // Calmar ratio analysis
    if (calmarRatio < 0.5 && maxDD > 0) {
        insights.push({
            type: 'warning',
            icon: <WarningOutlined />,
            message: t('portfolio.insights.low_calmar', 'Low Calmar ratio (<0.5). Annual return does not justify drawdown risk. Consider reducing leverage or improving entry points.'),
        });
    }

    return insights;
};

/**
 * Optimization suggestions card with smart insights
 */
function OptimizationCard({ t, optimization, metrics }) {
    const insights = metrics ? generateInsights(metrics, t) : [];

    return (
        <Card className="optimization-card" title={
            <span><ThunderboltOutlined /> {t('portfolio.optimization', 'Optimization Suggestions')}</span>
        }>
            <div className="optimization-content">
                {/* Smart Insights Section */}
                {insights.length > 0 && (
                    <>
                        <div className="insights-section">
                            <h4 className="section-subtitle">
                                <BulbOutlined /> {t('portfolio.insights_title', 'Performance Insights')}
                            </h4>
                            <List
                                size="small"
                                dataSource={insights}
                                renderItem={(item) => (
                                    <List.Item>
                                        <Alert
                                            description={item.message}
                                            type={item.type}
                                            icon={item.icon}
                                            showIcon
                                            style={{ width: '100%' }}
                                        />
                                    </List.Item>
                                )}
                            />
                        </div>
                        <Divider />
                    </>
                )}

                {/* Optimal Weights Section */}
                <div className="optimal-weights-section">
                    <h4 className="section-subtitle">
                        {t('portfolio.optimal_allocation', 'Optimal Asset Allocation')}
                    </h4>
                    <p className="optimization-intro">
                        {t('portfolio.optimization_intro', 'Based on historical returns and covariance, here are the optimal weights for maximum Sharpe ratio:')}
                    </p>

                    <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
                        {optimization.tickers?.map((ticker, i) => {
                            const currentWeight = metrics?.weights?.[i] || 0;
                            const optimalWeight = optimization.optimal_weights?.[i] || 0;
                            const diff = (optimalWeight - currentWeight) * 100;
                            const shouldRebalance = Math.abs(diff) > 5;

                            return (
                                <Col xs={24} sm={12} md={8} key={ticker}>
                                    <div className="optimal-weight-item">
                                        <div className="weight-header">
                                            <Tag color="blue">{ticker}</Tag>
                                            {shouldRebalance && (
                                                <Badge
                                                    count={diff > 0 ? '+' + diff.toFixed(1) + '%' : diff.toFixed(1) + '%'}
                                                    style={{
                                                        backgroundColor: diff > 0 ? '#52c41a' : '#ff4d4f',
                                                    }}
                                                />
                                            )}
                                        </div>
                                        <div className="weight-values">
                                            <div className="weight-row">
                                                <span className="weight-label">{t('portfolio.current', 'Current')}:</span>
                                                <span className="weight-value">{(currentWeight * 100).toFixed(1)}%</span>
                                            </div>
                                            <div className="weight-row">
                                                <span className="weight-label">{t('portfolio.optimal', 'Optimal')}:</span>
                                                <span className="weight-value optimal">{(optimalWeight * 100).toFixed(1)}%</span>
                                            </div>
                                        </div>
                                    </div>
                                </Col>
                            );
                        })}
                    </Row>

                    {optimization.expected_return && (
                        <div className="optimization-metrics">
                            <Badge status="processing" text={t('portfolio.optimization_metrics.expected_return', 'Expected Return') + ': ' + (optimization.expected_return * 100).toFixed(2) + '%'} />
                            <Badge status="processing" text={t('portfolio.optimization_metrics.expected_volatility', 'Expected Volatility') + ': ' + (optimization.expected_volatility * 100).toFixed(2) + '%'} />
                            <Badge status="success" text={t('portfolio.optimization_metrics.sharpe_ratio', 'Sharpe Ratio') + ': ' + optimization.sharpe_ratio?.toFixed(4)} />
                        </div>
                    )}
                </div>
            </div>
        </Card>
    );
}

export default OptimizationCard;
