import { useState } from 'react'
import { Modal, Tabs, Descriptions, Tag, Table, Card, Row, Col, Statistic, Empty, Button, message } from 'antd'
import { FileTextOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import dayjs from 'dayjs'
import { api } from '../../services/api'

function PortfolioDetailModal({ visible, portfolio, onClose }) {
    const { t } = useTranslation()
    const [reportLoading, setReportLoading] = useState(false)

    if (!portfolio) return null

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
        {
            title: t('history.trades'),
            dataIndex: 'total_trades',
            key: 'total_trades',
            render: (value) => value ?? 'N/A'
        }
    ]

    // Prepare individual results data
    const getIndividualResults = () => {
        if (!portfolio.individual_results) return []

        const results = []
        const individualResults = portfolio.individual_results

        // Handle both array format (from run_portfolio_backtest) and object format
        if (Array.isArray(individualResults)) {
            // Array format: [{ticker, success, weight, return, sharpe, drawdown, ...}, ...]
            individualResults.forEach((item, index) => {
                if (item && item.success) {
                    results.push({
                        key: item.ticker,
                        ticker: item.ticker,
                        weight: item.weight || 0,
                        total_return: item.return,  // Backend uses 'return' not 'total_return'
                        sharpe_ratio: item.sharpe,  // Backend uses 'sharpe' not 'sharpe_ratio'
                        max_drawdown: item.drawdown, // Backend uses 'drawdown' not 'max_drawdown'
                        total_trades: item.total_trades || 'N/A'
                    })
                }
            })
        } else {
            // Object format: {AAPL: {status: 'success', metrics: {...}}, ...}
            const weights = portfolio.weights || []
            Object.entries(individualResults).forEach(([ticker, data], index) => {
                if (data && data.status === 'success' && data.metrics) {
                    results.push({
                        key: ticker,
                        ticker,
                        weight: weights[index] || 0,
                        total_return: data.metrics.total_return,
                        sharpe_ratio: data.metrics.sharpe_ratio,
                        max_drawdown: data.metrics.max_drawdown,
                        total_trades: data.metrics.total_trades
                    })
                }
            })
        }
        return results
    }

    // Render correlation matrix
    const renderCorrelationMatrix = () => {
        // Backend returns 'correlation' field, not 'correlation_matrix'
        const correlationData = portfolio.correlation || portfolio.correlation_matrix
        if (!correlationData || !correlationData.matrix) {
            return <Empty description="No correlation data available" />
        }

        const { matrix, tickers } = correlationData

        const columns = [
            {
                title: '',
                dataIndex: 'ticker',
                key: 'ticker',
                fixed: 'left',
                width: 80,
                render: (ticker) => <strong>{ticker}</strong>
            },
            ...tickers.map((ticker, idx) => ({
                title: ticker,
                dataIndex: `col_${idx}`,
                key: `col_${idx}`,
                width: 80,
                render: (value) => {
                    if (value === null || value === undefined) return 'N/A'
                    const absValue = Math.abs(value)
                    let color = 'default'
                    if (absValue >= 0.7) color = value > 0 ? 'green' : 'red'
                    else if (absValue >= 0.4) color = value > 0 ? 'cyan' : 'orange'
                    return <Tag color={color}>{value.toFixed(2)}</Tag>
                }
            }))
        ]

        const data = tickers.map((ticker, rowIdx) => {
            const row = { key: ticker, ticker }
            matrix[rowIdx].forEach((value, colIdx) => {
                row[`col_${colIdx}`] = value
            })
            return row
        })

        return (
            <Table
                columns={columns}
                dataSource={data}
                pagination={false}
                size="small"
                scroll={{ x: 'max-content' }}
            />
        )
    }

    // Render optimization suggestions
    const renderOptimization = () => {
        // Backend returns 'optimization' field, not 'optimization_suggestion'
        const optimizationData = portfolio.optimization || portfolio.optimization_suggestion
        if (!optimizationData) {
            return <Empty description="No optimization suggestions available" />
        }

        const { optimal_weights, tickers, expected_return, expected_volatility, expected_sharpe } = optimizationData

        if (!optimal_weights || !tickers) {
            return <Empty description="Optimization data incomplete" />
        }

        const currentWeights = portfolio.weights || []

        const comparisonData = tickers.map((ticker, idx) => ({
            key: ticker,
            ticker,
            current: currentWeights[idx] || 0,
            optimal: optimal_weights[idx] || 0,
            diff: (optimal_weights[idx] || 0) - (currentWeights[idx] || 0)
        }))

        const columns = [
            {
                title: t('history.ticker'),
                dataIndex: 'ticker',
                key: 'ticker',
                render: (ticker) => <Tag color="blue">{ticker}</Tag>
            },
            {
                title: t('history.current_weights'),
                dataIndex: 'current',
                key: 'current',
                render: (value) => `${(value * 100).toFixed(1)}%`
            },
            {
                title: t('history.optimal_weights'),
                dataIndex: 'optimal',
                key: 'optimal',
                render: (value) => <Tag color="green">{(value * 100).toFixed(1)}%</Tag>
            },
            {
                title: 'Δ',
                dataIndex: 'diff',
                key: 'diff',
                render: (value) => {
                    const color = value > 0 ? 'green' : value < 0 ? 'red' : 'default'
                    const sign = value > 0 ? '+' : ''
                    return <Tag color={color}>{sign}{(value * 100).toFixed(1)}%</Tag>
                }
            }
        ]

        return (
            <div>
                <Row gutter={16} style={{ marginBottom: 16 }}>
                    {expected_return !== undefined && (
                        <Col span={8}>
                            <Card size="small">
                                <Statistic
                                    title={t('history.expected_return')}
                                    value={expected_return * 100}
                                    precision={2}
                                    suffix="%"
                                />
                            </Card>
                        </Col>
                    )}
                    {expected_volatility !== undefined && (
                        <Col span={8}>
                            <Card size="small">
                                <Statistic
                                    title={t('history.expected_volatility')}
                                    value={expected_volatility * 100}
                                    precision={2}
                                    suffix="%"
                                />
                            </Card>
                        </Col>
                    )}
                    {expected_sharpe !== undefined && (
                        <Col span={8}>
                            <Card size="small">
                                <Statistic
                                    title={t('history.sharpe')}
                                    value={expected_sharpe}
                                    precision={2}
                                />
                            </Card>
                        </Col>
                    )}
                </Row>
                <Table
                    columns={columns}
                    dataSource={comparisonData}
                    pagination={false}
                    size="small"
                />
            </div>
        )
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
                }
            })

            message.success(t('history.report_generating', 'Report generation started. You can view it in the Report Center.'))
        } catch (err) {
            console.error('Failed to generate report:', err)
            message.error(t('history.report_generation_failed', 'Failed to generate report'))
        } finally {
            setReportLoading(false)
        }
    }

    const tabItems = [
        {
            key: 'overview',
            label: t('history.tab_overview'),
            children: (
                <div>
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
                        <Descriptions.Item label={t('history.final_value')}>
                            ${portfolio.final_value?.toLocaleString() || 'N/A'}
                        </Descriptions.Item>
                        <Descriptions.Item label={t('history.return')}>
                            <Tag color={portfolio.total_return >= 0 ? 'green' : 'red'}>
                                {portfolio.total_return?.toFixed(2) || 'N/A'}%
                            </Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label={t('history.weighted_sharpe')}>
                            {portfolio.weighted_sharpe?.toFixed(2) || 'N/A'}
                        </Descriptions.Item>
                        <Descriptions.Item label={t('history.drawdown')}>
                            {portfolio.max_drawdown?.toFixed(2) || 'N/A'}%
                        </Descriptions.Item>
                        <Descriptions.Item label={t('history.strategy')}>
                            {portfolio.strategy_name || 'Default'}
                        </Descriptions.Item>
                    </Descriptions>
                </div>
            )
        },
        {
            key: 'metrics',
            label: t('history.tab_metrics'),
            children: (
                <div>
                    <h4 style={{ marginBottom: 16 }}>{t('history.individual_results')}</h4>
                    <Table
                        columns={assetColumns}
                        dataSource={getIndividualResults()}
                        pagination={false}
                        size="small"
                        locale={{ emptyText: 'No individual results available' }}
                    />
                </div>
            )
        },
        {
            key: 'chart',
            label: t('history.tab_chart'),
            children: (
                <div style={{ textAlign: 'center' }}>
                    {portfolio.plot_filename ? (
                        <img
                            src={`/images/${portfolio.plot_filename}`}
                            alt="Portfolio Chart"
                            style={{ maxWidth: '100%', maxHeight: '500px' }}
                        />
                    ) : (
                        <Empty description="No chart available" />
                    )}
                </div>
            )
        },
        {
            key: 'correlation',
            label: t('history.tab_correlation'),
            children: renderCorrelationMatrix()
        },
        {
            key: 'optimization',
            label: t('history.tab_optimization'),
            children: renderOptimization()
        }
    ]

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
            width={900}
            destroyOnClose
        >
            <Tabs items={tabItems} />
        </Modal>
    )
}

export default PortfolioDetailModal
