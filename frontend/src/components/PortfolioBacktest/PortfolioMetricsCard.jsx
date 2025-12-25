import { Card } from 'antd';
import { PieChartOutlined } from '@ant-design/icons';

/**
 * Portfolio metrics display card
 */
function PortfolioMetricsCard({ t, metrics }) {
    return (
        <Card className="portfolio-metrics-card" title={
            <span><PieChartOutlined /> {t('portfolio.portfolio_metrics', 'Portfolio Metrics')}</span>
        }>
            <div className="metrics-grid">
                <div className="metric-item">
                    <span className="metric-label">{t('portfolio.final_value', 'Final Value')}</span>
                    <span className="metric-value">${metrics?.final_value?.toLocaleString()}</span>
                </div>
                <div className="metric-item">
                    <span className="metric-label">{t('portfolio.total_return', 'Total Return')}</span>
                    <span className={`metric-value ${metrics?.total_return >= 0 ? 'positive' : 'negative'}`}>
                        {metrics?.total_return?.toFixed(2)}%
                    </span>
                </div>
                <div className="metric-item">
                    <span className="metric-label">{t('portfolio.sharpe', 'Weighted Sharpe')}</span>
                    <span className="metric-value">{metrics?.weighted_sharpe?.toFixed(4) || 'N/A'}</span>
                </div>
                <div className="metric-item">
                    <span className="metric-label">{t('portfolio.max_drawdown', 'Max Drawdown')}</span>
                    <span className="metric-value negative">{metrics?.max_drawdown?.toFixed(2)}%</span>
                </div>
            </div>
        </Card>
    );
}

export default PortfolioMetricsCard;
