import React from 'react';
import { Image } from 'antd';
import {
    LineChartOutlined,
    SyncOutlined,
    PieChartOutlined,
    TableOutlined,
    UnorderedListOutlined,
    AppstoreOutlined,
    BulbOutlined,
    PictureOutlined,
} from '@ant-design/icons';

/**
 * Check what data is available in a portfolio result.
 * Use this to conditionally render tabs based on available data.
 *
 * @param {Object} result - Portfolio backtest result
 * @returns {Object} Object with boolean flags for each data type
 */
export function getAvailableData(result) {
    if (!result) {
        return {
            hasEquityCurve: false,
            hasRebalancing: false,
            hasContributions: false,
            hasTrades: false,
            hasCorrelation: false,
            hasOptimization: false,
            hasIndividualResults: false,
            hasChart: false,
        };
    }

    return {
        hasEquityCurve: result.equity_curve && Object.keys(result.equity_curve).length > 0,
        hasRebalancing: result.rebalancing_events && result.rebalancing_events.length > 0,
        hasContributions: result.asset_contributions && Object.keys(result.asset_contributions).length > 0,
        hasTrades: (result.all_trades && result.all_trades.length > 0) ||
            (result.rebalancing_events && result.rebalancing_events.length > 0),
        hasCorrelation: result.correlation && !result.correlation.error,
        hasOptimization: result.optimization && !result.optimization.error,
        hasIndividualResults: result.individual_results && result.individual_results.length > 0,
        hasChart: !!result.plot_url,
    };
}

/**
 * Build tab items for portfolio results display.
 *
 * This function is shared between PortfolioResultsSection and PortfolioDetailModal
 * to ensure consistent tab structure and behavior.
 *
 * @param {Object} params - Configuration parameters
 * @param {Object} params.result - Portfolio backtest result data
 * @param {Function} params.t - Translation function
 * @param {Object} params.components - React component references
 * @param {React.ComponentType} params.components.EquityCurveChart - Equity curve chart component
 * @param {React.ComponentType} params.components.RebalancingTimeline - Rebalancing timeline component
 * @param {React.ComponentType} params.components.AssetContributionChart - Asset contribution chart
 * @param {React.ComponentType} params.components.CorrelationCard - Correlation matrix card
 * @param {React.ComponentType} params.components.OptimizationCard - Optimization suggestions card
 * @param {React.ComponentType} params.components.TradeLogTable - Trade log table component
 * @param {React.ComponentType} params.components.IndividualResultsTable - Individual results table
 * @param {Object} params.options - Display options
 * @param {boolean} params.options.showCorrelation - Whether to show correlation tab
 * @param {boolean} params.options.showOptimization - Whether to show optimization tab
 * @param {boolean} params.options.showChart - Whether to show chart tab
 * @param {string} params.options.defaultTab - Default active tab key
 * @returns {Array} Array of tab item configurations for Ant Design Tabs
 */
export function buildPortfolioTabItems({ result, t, components, options = {} }) {
    const {
        EquityCurveChart,
        RebalancingTimeline,
        AssetContributionChart,
        CorrelationCard,
        OptimizationCard,
        TradeLogTable,
        IndividualResultsTable,
    } = components;

    const {
        showCorrelation = true,
        showOptimization = true,
        showChart = true,
    } = options;

    // Check data availability
    const available = getAvailableData(result);

    const tabItems = [];

    // 1. Equity Curve Tab
    if (available.hasEquityCurve && EquityCurveChart) {
        tabItems.push({
            key: 'equity',
            label: (
                <span>
                    <LineChartOutlined /> {t('portfolio.equity_curve', 'Equity Curve')}
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

    // 2. Rebalancing Tab
    if (available.hasRebalancing && RebalancingTimeline) {
        tabItems.push({
            key: 'rebalancing',
            label: (
                <span>
                    <SyncOutlined /> {t('portfolio.rebalancing', 'Rebalancing')}
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

    // 3. Asset Contribution Tab
    if (available.hasContributions && AssetContributionChart) {
        tabItems.push({
            key: 'contributions',
            label: (
                <span>
                    <PieChartOutlined /> {t('portfolio.contributions', 'Contributions')}
                </span>
            ),
            children: (
                <AssetContributionChart
                    contributions={result.asset_contributions}
                    tickers={result.tickers}
                    weights={result.weights}
                    t={t}
                />
            ),
        });
    }

    // 4. Trade Log Tab
    if (available.hasTrades && TradeLogTable) {
        tabItems.push({
            key: 'trades',
            label: (
                <span>
                    <TableOutlined /> {t('portfolio.trade_log', 'Trade Log')}
                </span>
            ),
            children: (
                <TradeLogTable
                    trades={result.all_trades}
                    rebalancingEvents={result.rebalancing_events}
                    t={t}
                />
            ),
        });
    }

    // 5. Individual Results Tab
    if (available.hasIndividualResults && IndividualResultsTable) {
        tabItems.push({
            key: 'individual',
            label: (
                <span>
                    <UnorderedListOutlined /> {t('portfolio.individual_results', 'By Asset')}
                </span>
            ),
            children: (
                <IndividualResultsTable
                    results={result.individual_results}
                    t={t}
                />
            ),
        });
    }

    // 6. Correlation Tab
    if (showCorrelation && available.hasCorrelation && CorrelationCard) {
        tabItems.push({
            key: 'correlation',
            label: (
                <span>
                    <AppstoreOutlined /> {t('portfolio.correlation', 'Correlation')}
                </span>
            ),
            children: (
                <CorrelationCard
                    correlation={result.correlation}
                    t={t}
                />
            ),
        });
    }

    // 7. Optimization Tab
    if (showOptimization && available.hasOptimization && OptimizationCard) {
        tabItems.push({
            key: 'optimization',
            label: (
                <span>
                    <BulbOutlined /> {t('portfolio.optimization', 'Optimization')}
                </span>
            ),
            children: (
                <OptimizationCard
                    optimization={result.optimization}
                    currentWeights={result.weights}
                    tickers={result.tickers}
                    t={t}
                />
            ),
        });
    }

    // 8. Chart Tab (if plot_url available)
    if (showChart && available.hasChart) {
        tabItems.push({
            key: 'chart',
            label: (
                <span>
                    <PictureOutlined /> {t('portfolio.chart', 'Chart')}
                </span>
            ),
            children: (
                <div style={{ textAlign: 'center', padding: 16 }}>
                    <Image
                        src={result.plot_url}
                        alt="Backtest Chart"
                        style={{ maxWidth: '100%', maxHeight: 600 }}
                    />
                </div>
            ),
        });
    }

    return tabItems;
}

/**
 * Get the default active tab key based on available data.
 *
 * @param {Object} result - Portfolio backtest result
 * @returns {string} The key of the default active tab
 */
export function getDefaultTabKey(result) {
    const available = getAvailableData(result);

    // Priority: equity > rebalancing > contributions > trades > individual
    if (available.hasEquityCurve) return 'equity';
    if (available.hasRebalancing) return 'rebalancing';
    if (available.hasContributions) return 'contributions';
    if (available.hasTrades) return 'trades';
    if (available.hasIndividualResults) return 'individual';
    if (available.hasCorrelation) return 'correlation';
    if (available.hasOptimization) return 'optimization';
    if (available.hasChart) return 'chart';

    return 'equity'; // Fallback
}

export default buildPortfolioTabItems;
