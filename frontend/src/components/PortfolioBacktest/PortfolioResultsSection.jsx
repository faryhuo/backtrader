import { Card, Image, Table, Tabs } from 'antd';
import { LineChartOutlined, PieChartOutlined, SyncOutlined, TableOutlined, UnorderedListOutlined } from '@ant-design/icons';
import PortfolioMetricsCard from './PortfolioMetricsCard';
import CorrelationCard from './CorrelationCard';
import OptimizationCard from './OptimizationCard';
import EquityCurveChart from './EquityCurveChart';
import RebalancingTimeline from './RebalancingTimeline';
import AssetContributionChart from './AssetContributionChart';
import PortfolioTradeLog from './PortfolioTradeLog';

/**
 * Results section displaying all portfolio backtest results
 */
function PortfolioResultsSection({ t, result, columns }) {
    // Check if we have multi-asset specific data
    const hasEquityCurve = result.equity_curve && Object.keys(result.equity_curve).length > 0;
    const hasRebalancing = result.rebalancing_events && result.rebalancing_events.length > 0;
    const hasContributions = result.asset_contributions && Object.keys(result.asset_contributions).length > 0;
    const hasTrades = (result.all_trades && result.all_trades.length > 0) || hasRebalancing;
    const hasMultiAssetData = hasEquityCurve || hasRebalancing || hasContributions || hasTrades;

    // Build tab items for multi-asset results
    const tabItems = [];

    if (hasEquityCurve) {
        tabItems.push({
            key: 'equity',
            label: (
                <span>
                    <LineChartOutlined />
                    {t('portfolio.equity_curve', 'Equity Curve')}
                </span>
            ),
            children: (
                <EquityCurveChart
                    equityCurve={result.equity_curve}
                    rebalancingEvents={result.rebalancing_events}
                    t={t}
                />
            ),
        });
    }

    if (hasRebalancing) {
        tabItems.push({
            key: 'rebalancing',
            label: (
                <span>
                    <SyncOutlined />
                    {t('portfolio.rebalancing', 'Rebalancing')}
                </span>
            ),
            children: (
                <RebalancingTimeline
                    rebalancingEvents={result.rebalancing_events}
                    t={t}
                />
            ),
        });
    }

    if (hasContributions) {
        tabItems.push({
            key: 'contributions',
            label: (
                <span>
                    <PieChartOutlined />
                    {t('portfolio.contributions', 'Contributions')}
                </span>
            ),
            children: (
                <AssetContributionChart
                    assetContributions={result.asset_contributions}
                    weights={result.weights}
                    t={t}
                />
            ),
        });
    }

    // Add individual results tab
    tabItems.push({
        key: 'individual',
        label: (
            <span>
                <TableOutlined />
                {t('portfolio.individual_results', 'Individual Results')}
            </span>
        ),
        children: (
            <Card className="individual-results-card">
                <Table
                    dataSource={result.individual_results}
                    rowKey="ticker"
                    size="small"
                    pagination={false}
                    columns={columns}
                />
            </Card>
        ),
    });

    // Always add trade log tab (shows trades from rebalancing events or initial positions)
    tabItems.push({
        key: 'trades',
        label: (
            <span>
                <UnorderedListOutlined />
                {t('portfolio.trade_log', 'Trade Log')}
            </span>
        ),
        children: (
            <PortfolioTradeLog
                allTrades={result.all_trades}
                rebalancingEvents={result.rebalancing_events}
                t={t}
            />
        ),
    });

    return (
        <div className="results-section">
            <PortfolioMetricsCard t={t} metrics={{
                final_value: result.final_value ?? result.portfolio_metrics?.final_value,
                total_return: result.total_return ?? result.portfolio_metrics?.total_return,
                weighted_sharpe: result.weighted_sharpe ?? result.sharpe_ratio ?? result.portfolio_metrics?.weighted_sharpe,
                max_drawdown: result.max_drawdown ?? result.portfolio_metrics?.max_drawdown,
            }} />

            {hasMultiAssetData ? (
                <Card className="multi-asset-results-card">
                    <Tabs
                        defaultActiveKey="equity"
                        items={tabItems}
                        type="card"
                    />
                </Card>
            ) : (
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
            )}

            {result.correlation && !result.correlation.error && (
                <CorrelationCard t={t} correlation={result.correlation} />
            )}

            {result.optimization && !result.optimization.error && (
                <OptimizationCard t={t} optimization={result.optimization} />
            )}

            {result.plot_url && (
                <Card className="chart-card" title={t('portfolio.chart', 'Portfolio Chart')}>
                    <Image src={result.plot_url} alt={t('portfolio.chart_alt', 'Portfolio Chart')} className="portfolio-chart" style={{ maxWidth: '100%' }} />
                </Card>
            )}
        </div>
    );
}

export default PortfolioResultsSection;
