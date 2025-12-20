import React from 'react'
import { useTranslation } from 'react-i18next'
import {
    Modal,
    Descriptions,
    Table,
    Tag,
    Tabs,
    Card,
    Row,
    Col,
    Statistic,
    Alert,
    Space,
    Typography
} from 'antd'
import {
    CheckCircleOutlined,
    ExclamationCircleOutlined,
    LineChartOutlined,
    TableOutlined,
    BarChartOutlined,
    HeatMapOutlined
} from '@ant-design/icons'
import OverfittingScoreCard from './OverfittingScoreCard'
import ParameterHeatmap from './ParameterHeatmap'
import Parameter3DSurface from './Parameter3DSurface'
import ParameterSensitivityTable from './ParameterSensitivityTable'

const { TabPane } = Tabs
const { Title, Text } = Typography

const WalkForwardDetailModal = ({ visible, optimization, onClose }) => {
    const { t } = useTranslation()

    if (!optimization) return null

    const { windows, overfitting_metrics, combined_test_metrics, param_grid, parameter_analysis } = optimization

    const windowColumns = [
        {
            title: t('walkforward.detail.windowId'),
            dataIndex: 'window_id',
            key: 'window_id',
            width: 80,
            align: 'center'
        },
        {
            title: t('walkforward.detail.trainPeriod'),
            key: 'train_period',
            width: 200,
            render: (_, record) => `${record.train_start} ~ ${record.train_end}`
        },
        {
            title: t('walkforward.detail.testPeriod'),
            key: 'test_period',
            width: 200,
            render: (_, record) => `${record.test_start} ~ ${record.test_end}`
        },
        {
            title: t('walkforward.detail.bestParams'),
            dataIndex: 'best_params',
            key: 'best_params',
            width: 200,
            render: (params) => (
                <Space direction="vertical" size="small">
                    {Object.entries(params || {}).map(([key, value]) => (
                        <Text key={key} code>{`${key}: ${value}`}</Text>
                    ))}
                </Space>
            )
        },
        {
            title: t('walkforward.detail.trainMetric'),
            key: 'train_metric',
            width: 120,
            align: 'right',
            render: (_, record) => {
                const metric = record.train_metrics?.[optimization.optimization_metric]
                return metric != null ? metric.toFixed(4) : '-'
            }
        },
        {
            title: t('walkforward.detail.testMetric'),
            key: 'test_metric',
            width: 120,
            align: 'right',
            render: (_, record) => {
                const metric = record.test_metrics?.[optimization.optimization_metric]
                return metric != null ? metric.toFixed(4) : '-'
            }
        },
        {
            title: t('walkforward.detail.degradation'),
            key: 'degradation',
            width: 100,
            align: 'right',
            render: (_, record) => {
                const trainVal = record.train_metrics?.[optimization.optimization_metric] || 0
                const testVal = record.test_metrics?.[optimization.optimization_metric] || 0
                if (trainVal === 0) return '-'
                const degradation = ((trainVal - testVal) / Math.abs(trainVal)) * 100
                const color = Math.abs(degradation) > 30 ? 'red' : Math.abs(degradation) > 20 ? 'orange' : 'green'
                return <Text style={{ color }}>{degradation.toFixed(2)}%</Text>
            }
        }
    ]

    const renderOverfittingAlert = () => {
        if (!overfitting_metrics) return null

        const isOverfitting = overfitting_metrics.overfitting_detected

        return (
            <Alert
                message={isOverfitting ? t('walkforward.detail.overfittingDetected') : t('walkforward.detail.noOverfitting')}
                description={
                    isOverfitting
                        ? t('walkforward.detail.overfittingDescription')
                        : t('walkforward.detail.noOverfittingDescription')
                }
                type={isOverfitting ? 'warning' : 'success'}
                icon={isOverfitting ? <ExclamationCircleOutlined /> : <CheckCircleOutlined />}
                showIcon
                style={{ marginBottom: 24 }}
            />
        )
    }

    const renderOverfittingMetrics = () => {
        if (!overfitting_metrics) return null

        return (
            <Row gutter={[16, 16]}>
                <Col span={8}>
                    <Card>
                        <Statistic
                            title={t('walkforward.detail.trainTestCorrelation')}
                            value={overfitting_metrics.train_test_correlation}
                            precision={4}
                            valueStyle={{
                                color: overfitting_metrics.train_test_correlation > 0.5 ? '#3f8600' : '#cf1322'
                            }}
                        />
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic
                            title={t('walkforward.detail.avgDegradation')}
                            value={overfitting_metrics.avg_degradation_pct}
                            precision={2}
                            suffix="%"
                            valueStyle={{
                                color: Math.abs(overfitting_metrics.avg_degradation_pct) < 20 ? '#3f8600' : '#cf1322'
                            }}
                        />
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic
                            title={t('walkforward.detail.consistencyScore')}
                            value={overfitting_metrics.consistency_score}
                            precision={2}
                            suffix="%"
                            valueStyle={{
                                color: overfitting_metrics.consistency_score > 70 ? '#3f8600' : '#cf1322'
                            }}
                        />
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic
                            title={t('walkforward.detail.avgTrainPerformance')}
                            value={overfitting_metrics.avg_train_performance}
                            precision={4}
                        />
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic
                            title={t('walkforward.detail.avgTestPerformance')}
                            value={overfitting_metrics.avg_test_performance}
                            precision={4}
                        />
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic
                            title={t('walkforward.detail.degradationStd')}
                            value={overfitting_metrics.degradation_std}
                            precision={2}
                        />
                    </Card>
                </Col>
            </Row>
        )
    }

    const renderCombinedMetrics = () => {
        if (!combined_test_metrics) return null

        return (
            <Row gutter={[16, 16]}>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title={t('walkforward.detail.totalReturn')}
                            value={combined_test_metrics.total_return}
                            precision={2}
                            suffix="%"
                            valueStyle={{ color: combined_test_metrics.total_return > 0 ? '#3f8600' : '#cf1322' }}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title={t('walkforward.detail.avgSharpeRatio')}
                            value={combined_test_metrics.avg_sharpe_ratio}
                            precision={4}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title={t('walkforward.detail.avgMaxDrawdown')}
                            value={combined_test_metrics.avg_max_drawdown}
                            precision={2}
                            suffix="%"
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title={t('walkforward.detail.winRate')}
                            value={combined_test_metrics.win_rate}
                            precision={2}
                            suffix="%"
                            valueStyle={{ color: combined_test_metrics.win_rate > 50 ? '#3f8600' : '#cf1322' }}
                        />
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic
                            title={t('walkforward.detail.totalTrades')}
                            value={combined_test_metrics.total_trades}
                        />
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic
                            title={t('walkforward.detail.winningTrades')}
                            value={combined_test_metrics.winning_trades}
                            valueStyle={{ color: '#3f8600' }}
                        />
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic
                            title={t('walkforward.detail.losingTrades')}
                            value={combined_test_metrics.losing_trades}
                            valueStyle={{ color: '#cf1322' }}
                        />
                    </Card>
                </Col>
            </Row>
        )
    }

    const renderConfiguration = () => {
        return (
            <Descriptions bordered column={2}>
                <Descriptions.Item label={t('walkforward.detail.strategy')}>
                    {optimization.strategy_name}
                </Descriptions.Item>
                <Descriptions.Item label={t('walkforward.detail.ticker')}>
                    {optimization.ticker}
                </Descriptions.Item>
                <Descriptions.Item label={t('walkforward.detail.dateRange')}>
                    {optimization.start_date} ~ {optimization.end_date}
                </Descriptions.Item>
                <Descriptions.Item label={t('walkforward.detail.numWindows')}>
                    {windows?.length || 0}
                </Descriptions.Item>
                <Descriptions.Item label={t('walkforward.detail.trainPeriodDays')}>
                    {optimization.train_period_days} {t('walkforward.config.days')}
                </Descriptions.Item>
                <Descriptions.Item label={t('walkforward.detail.testPeriodDays')}>
                    {optimization.test_period_days} {t('walkforward.config.days')}
                </Descriptions.Item>
                <Descriptions.Item label={t('walkforward.detail.windowType')}>
                    {optimization.anchored ? t('walkforward.config.anchoredYes') : t('walkforward.config.anchoredNo')}
                </Descriptions.Item>
                <Descriptions.Item label={t('walkforward.detail.optimizationMetric')}>
                    {optimization.optimization_metric}
                </Descriptions.Item>
                <Descriptions.Item label={t('walkforward.detail.parameterGrid')} span={2}>
                    <Space direction="vertical">
                        {Object.entries(param_grid || {}).map(([key, values]) => (
                            <Text key={key} code>
                                {key}: [{values.join(', ')}]
                            </Text>
                        ))}
                    </Space>
                </Descriptions.Item>
            </Descriptions>
        )
    }

    return (
        <Modal
            title={t('walkforward.detail.title')}
            open={visible}
            onCancel={onClose}
            width={1200}
            footer={null}
        >
            <Tabs defaultActiveKey="overview">
                <TabPane
                    tab={
                        <span>
                            <LineChartOutlined />
                            {t('walkforward.detail.overview')}
                        </span>
                    }
                    key="overview"
                >
                    {renderOverfittingAlert()}
                    <Title level={5}>{t('walkforward.detail.overfittingMetrics')}</Title>
                    {renderOverfittingMetrics()}
                    <Title level={5} style={{ marginTop: 24 }}>
                        {t('walkforward.detail.combinedTestMetrics')}
                    </Title>
                    {renderCombinedMetrics()}
                </TabPane>

                <TabPane
                    tab={
                        <span>
                            <TableOutlined />
                            {t('walkforward.detail.windowResults')}
                        </span>
                    }
                    key="windows"
                >
                    <Table
                        columns={windowColumns}
                        dataSource={windows}
                        rowKey="window_id"
                        pagination={false}
                        scroll={{ x: 1000 }}
                    />
                </TabPane>

                <TabPane
                    tab={
                        <span>
                            <BarChartOutlined />
                            {t('walkforward.detail.configuration')}
                        </span>
                    }
                    key="config"
                >
                    {renderConfiguration()}
                </TabPane>

                <TabPane
                    tab={
                        <span>
                            <HeatMapOutlined />
                            {t('walkforward.detail.parameterAnalysis', 'Parameter Analysis')}
                        </span>
                    }
                    key="analysis"
                >
                    {parameter_analysis && (
                        <>
                            <OverfittingScoreCard
                                overfittingScore={parameter_analysis.overfitting_score}
                            />
                            <ParameterSensitivityTable
                                sensitivityRanking={parameter_analysis.sensitivity_ranking}
                            />
                            <ParameterHeatmap
                                heatmapData={parameter_analysis.heatmap}
                                metricName={optimization.optimization_metric}
                            />
                            <Parameter3DSurface
                                surfaceData={parameter_analysis.surface3d}
                                metricName={optimization.optimization_metric}
                            />
                        </>
                    )}
                    {!parameter_analysis && (
                        <Alert
                            message={t('walkforward.analysis.noData', 'No Parameter Analysis')}
                            description={t('walkforward.analysis.noDataDesc', 'Parameter analysis data is not available for this optimization.')}
                            type="info"
                            showIcon
                        />
                    )}
                </TabPane>
            </Tabs>
        </Modal>
    )
}

export default WalkForwardDetailModal
