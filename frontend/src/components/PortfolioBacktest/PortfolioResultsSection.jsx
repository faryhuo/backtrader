import { Card, Table } from 'antd';
import { LineChartOutlined } from '@ant-design/icons';
import PortfolioMetricsCard from './PortfolioMetricsCard';
import CorrelationCard from './CorrelationCard';
import OptimizationCard from './OptimizationCard';

/**
 * Results section displaying all portfolio backtest results
 */
function PortfolioResultsSection({ t, result, columns }) {
    return (
        <div className="results-section">
            <PortfolioMetricsCard t={t} metrics={result.portfolio_metrics} />

            <Card className="individual-results-card" title={
                <span><LineChartOutlined /> {t('portfolio.individual_results', 'Individual Asset Results')}</span>
            }>
                <Table
                    dataSource={result.individual_results}
                    rowKey="ticker"
                    size="small"
                    pagination={false}
                    columns={columns}
                />
            </Card>

            {result.correlation && !result.correlation.error && (
                <CorrelationCard t={t} correlation={result.correlation} />
            )}

            {result.optimization && !result.optimization.error && (
                <OptimizationCard t={t} optimization={result.optimization} />
            )}

            {result.plot_url && (
                <Card className="chart-card" title={t('portfolio.chart', 'Portfolio Chart')}>
                    <img src={result.plot_url} alt={t('portfolio.chart_alt', 'Portfolio Chart')} className="portfolio-chart" />
                </Card>
            )}
        </div>
    );
}

export default PortfolioResultsSection;
