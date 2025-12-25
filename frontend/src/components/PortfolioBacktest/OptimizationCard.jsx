import { Card, Tag } from 'antd';
import { ThunderboltOutlined } from '@ant-design/icons';

/**
 * Optimization suggestions card
 */
function OptimizationCard({ t, optimization }) {
    return (
        <Card className="optimization-card" title={
            <span><ThunderboltOutlined /> {t('portfolio.optimization', 'Optimization Suggestions')}</span>
        }>
            <div className="optimization-content">
                <p className="optimization-intro">
                    {t('portfolio.optimization_intro', 'Based on historical returns and covariance, here are the optimal weights for maximum Sharpe ratio:')}
                </p>
                <div className="optimal-weights">
                    {optimization.tickers?.map((ticker, i) => (
                        <div key={ticker} className="optimal-weight-item">
                            <Tag color="green">{ticker}</Tag>
                            <span>{((optimization.optimal_weights?.[i] || 0) * 100).toFixed(1)}%</span>
                        </div>
                    ))}
                </div>
                {optimization.expected_return && (
                    <div className="optimization-metrics">
                        <span>{t('portfolio.optimization_metrics.expected_return', 'Expected Return')}: {(optimization.expected_return * 100).toFixed(2)}%</span>
                        <span>{t('portfolio.optimization_metrics.expected_volatility', 'Expected Volatility')}: {(optimization.expected_volatility * 100).toFixed(2)}%</span>
                        <span>{t('portfolio.optimization_metrics.sharpe_ratio', 'Sharpe Ratio')}: {optimization.sharpe_ratio?.toFixed(4)}</span>
                    </div>
                )}
            </div>
        </Card>
    );
}

export default OptimizationCard;
