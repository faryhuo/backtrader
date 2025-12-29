import { useState } from 'react'
import { Modal, Tabs, Descriptions, Tag, Table, Card, Row, Col, Statistic, Empty, Button, message, Space } from 'antd'
import {
    FileTextOutlined,
    LineChartOutlined,
    SyncOutlined,
    PieChartOutlined,
    TableOutlined,
    AppstoreOutlined,
    BulbOutlined,
    PictureOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import dayjs from 'dayjs'
import { api } from '../../services/api'

// Import reusable components from PortfolioBacktest
import PortfolioMetricsCard from '../PortfolioBacktest/PortfolioMetricsCard'
import EquityCurveChart from '../PortfolioBacktest/EquityCurveChart'
import RebalancingTimeline from '../PortfolioBacktest/RebalancingTimeline'
import AssetContributionChart from '../PortfolioBacktest/AssetContributionChart'
import CorrelationCard from '../PortfolioBacktest/CorrelationCard'
import OptimizationCard from '../PortfolioBacktest/OptimizationCard'

import './PortfolioDetailModal.css'

function PortfolioDetailModal({ visible, portfolio, onClose }) {
    const { t, i18n } = useTranslation()
    const [reportLoading, setReportLoading] = useState(false)

    if (!portfolio) return null

    // Check for available data
    const hasEquityCurve = portfolio.equity_curve && Object.keys(portfolio.equity_curve).length > 0
    const hasRebalancing = portfolio.rebalancing_events && portfolio.rebalancing_events.length > 0
    const hasContributions = portfolio.asset_contributions && Object.keys(portfolio.asset_contributions).length > 0
    const hasCorrelation = portfolio.correlation && !portfolio.correlation.error
    const hasOptimization = portfolio.optimization && !portfolio.optimization.error

    // Individual asset results table columns
    const assetColumns = [
        {
            title: t('history.ticker'),
            dataIndex: 'ticker',
            key: 'ticker',
            render: (ticker) => <Tag color="blue">{ticker}</Tag>
        },
        {
            title: t('history.weights'),
            dataIndex: 'weight',
            key: 'weight',
            render: (weight) => `${(weight * 100).toFixed(1)}%`
        },
        {
            title: t('history.return'),
            dataIndex: 'total_return',
            key: 'total_return',
            render: (value) => {
                if (value === null || value === undefined) return 'N/A'
                const color = value >= 0 ? 'green' : 'red'
                return <Tag color={color}>{value.toFixed(2)}%</Tag>
            }
        },
        {
            title: t('history.sharpe'),
            dataIndex: 'sharpe_ratio',
            key: 'sharpe_ratio',
            render: (value) => value !== null && value !== undefined ? value.toFixed(2) : 'N/A'
        },
        {
            title: t('history.drawdown'),
            dataIndex: 'max_drawdown',
            key: 'max_drawdown',
            render: (value) => value !== null && value !== undefined ? `${value.toFixed(2)}%` : 'N/A'
        },
    ]

    // Prepare individual results data
    const getIndividualResults = () => {
        return (portfolio.individual_results || [])
            .filter(item => item && item.success !== false)
            .map(item => ({
                key: item.ticker,
                ticker: item.ticker,
                weight: item.weight || 0,
                total_return: item.total_return,
                sharpe_ratio: item.sharpe_ratio,
                max_drawdown: item.max_drawdown,
            }))
    }

    const handleGenerateReport = async () => {
        if (!portfolio || !portfolio.portfolio_id) {
            return
        }
        setReportLoading(true)

        try {
            const reportTitle = `Portfolio: ${portfolio.tickers?.join(', ')} (${portfolio.start_date} ~ ${portfolio.end_date})`

            await api.generateReport({
                report_type: 'portfolio',
                title: reportTitle,
                source_ids: [portfolio.portfolio_id],
                config: {
                    include_correlation: true,
                    include_optimization: true
                },
                language: i18n.language?.startsWith('zh') ? 'zh' : 'en'
            })

            message.success(t('history.report_generating', 'Report generation started. You can view it in the Report Center.'))
        } catch (err) {
            console.error('Failed to generate report:', err)
            message.error(t('history.report_generation_failed', 'Failed to generate report'))
        } finally {
            setReportLoading(false)
        }
    }

    // Build tab items
    const tabItems = [
        {
            key: 'overview',
            label: (
                <span>
                    <AppstoreOutlined />
                    {t('history.tab_overview')}
                </span>
            ),
            children: (
                <div className="overview-tab">
                    <PortfolioMetricsCard
                        t={t}
                        metrics={{
                            final_value: portfolio.final_value,
                            total_return: portfolio.total_return,
                            weighted_sharpe: portfolio.weighted_sharpe,
                            max_drawdown: portfolio.max_drawdown,
                        }}
                    />
                    <Card className="overview-info-card" size="small">
                        <Descriptions bordered column={2} size="small">
                            <Descriptions.Item label={t('history.tickers')}>
                                {portfolio.tickers?.map(ticker => (
                                    <Tag key={ticker} color="blue">{ticker}</Tag>
                                ))}
                            </Descriptions.Item>
                            <Descriptions.Item label={t('history.num_assets')}>
                                {portfolio.num_assets || portfolio.tickers?.length || 0}
                            </Descriptions.Item>
                            <Descriptions.Item label={t('history.period')}>
                                {portfolio.start_date} ~ {portfolio.end_date}
                            </Descriptions.Item>
                            <Descriptions.Item label={t('history.run_date')}>
                                {portfolio.created_at ? dayjs(portfolio.created_at).format('YYYY-MM-DD HH:mm') : 'N/A'}
                            </Descriptions.Item>
                            <Descriptions.Item label={t('history.initial_cash')}>
                                ${portfolio.initial_cash?.toLocaleString() || 'N/A'}
                            </Descriptions.Item>
                            <Descriptions.Item label={t('history.strategy')}>
                                {portfolio.strategy_name || t('portfolio.default_strategy', 'Buy & Hold')}
                            </Descriptions.Item>
                        </Descriptions>
                    </Card>
                </div>
            )
        },
    ]

    // Add equity curve tab if data available
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
                    equityCurve={portfolio.equity_curve}
                    rebalancingEvents={portfolio.rebalancing_events}
                    t={t}
                />
            ),
        })
    }

    // Add rebalancing tab if events exist
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
                    rebalancingEvents={portfolio.rebalancing_events}
                    t={t}
                />
            ),
        })
    }

    // Add contributions tab if data available
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
                    assetContributions={portfolio.asset_contributions}
                    weights={portfolio.weights}
                    t={t}
                />
            ),
        })
    }

    // Add individual results tab
    tabItems.push({
        key: 'individual',
        label: (
            <span>
                <TableOutlined />
                {t('history.tab_metrics')}
            </span>
        ),
        children: (
            <Card size="small">
                <Table
                    columns={assetColumns}
                    dataSource={getIndividualResults()}
                    pagination={false}
                    size="small"
                    locale={{ emptyText: 'No individual results available' }}
                />
            </Card>
        ),
    })

    // Add correlation tab
    if (hasCorrelation) {
        tabItems.push({
            key: 'correlation',
            label: (
                <span>
                    <AppstoreOutlined />
                    {t('history.tab_correlation')}
                </span>
            ),
            children: (
                <CorrelationCard t={t} correlation={portfolio.correlation} />
            ),
        })
    }

    // Add optimization tab
    if (hasOptimization) {
        tabItems.push({
            key: 'optimization',
            label: (
                <span>
                    <BulbOutlined />
                    {t('history.tab_optimization')}
                </span>
            ),
            children: (
                <OptimizationCard t={t} optimization={portfolio.optimization} />
            ),
        })
    }

    // Add chart tab if image available
    if (portfolio.plot_filename) {
        tabItems.push({
            key: 'chart',
            label: (
                <span>
                    <PictureOutlined />
                    {t('history.tab_chart')}
                </span>
            ),
            children: (
                <div style={{ textAlign: 'center' }}>
                    <img
                        src={`/images/${portfolio.plot_filename}`}
                        alt="Portfolio Chart"
                        style={{ maxWidth: '100%', maxHeight: '500px', borderRadius: 8 }}
                    />
                </div>
            ),
        })
    }

    return (
        <Modal
            title={t('history.portfolio_detail_title')}
            open={visible}
            onCancel={onClose}
            footer={[
                <Button
                    key="generate-report"
                    type="primary"
                    icon={<FileTextOutlined />}
                    onClick={handleGenerateReport}
                    loading={reportLoading}
                >
                    {t('history.generate_report', 'Generate Report')}
                </Button>,
                <Button key="close" onClick={onClose}>
                    {t('common.close', 'Close')}
                </Button>
            ]}
            width={1100}
            destroyOnClose
            className="portfolio-detail-modal"
        >
            <Tabs items={tabItems} defaultActiveKey="overview" />
        </Modal>
    )
}

export default PortfolioDetailModal
