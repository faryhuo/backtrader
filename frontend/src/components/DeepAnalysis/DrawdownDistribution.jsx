import React, { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import ReactECharts from 'echarts-for-react'
import { Card, Empty, Space, Row, Col, Statistic, Table, Typography } from 'antd'
import { FallOutlined } from '@ant-design/icons'

const { Text } = Typography

/**
 * DrawdownDistribution - Shows drawdown histogram and top drawdown periods.
 */
const DrawdownDistribution = ({ data }) => {
    const { t } = useTranslation()

    const histogramOption = useMemo(() => {
        if (!data || !data.bins || !data.counts) {
            return null
        }

        const { bins, counts } = data

        // Create bin labels
        const binLabels = []
        for (let i = 0; i < bins.length - 1; i++) {
            binLabels.push(`${(bins[i] * 100).toFixed(1)}%`)
        }

        return {
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'shadow' },
                formatter: (params) => {
                    const idx = params[0].dataIndex
                    const pct1 = (bins[idx] * 100).toFixed(2)
                    const pct2 = (bins[idx + 1] * 100).toFixed(2)
                    return `${pct1}% ~ ${pct2}%<br/>${t('deep_analysis.days')}: ${counts[idx]}`
                }
            },
            grid: {
                left: '10%',
                right: '5%',
                bottom: '20%',
                top: '10%'
            },
            xAxis: {
                type: 'category',
                data: binLabels,
                axisLabel: {
                    rotate: 45,
                    fontSize: 10
                },
                name: t('deep_analysis.drawdown_depth'),
                nameLocation: 'center',
                nameGap: 45
            },
            yAxis: {
                type: 'value',
                name: t('deep_analysis.days'),
                nameLocation: 'center',
                nameGap: 35
            },
            series: [{
                name: t('deep_analysis.drawdown_dist'),
                type: 'bar',
                data: counts,
                itemStyle: {
                    color: '#ef4444'
                },
                barWidth: '80%'
            }]
        }
    }, [data, t])

    const columns = useMemo(() => [
        {
            title: t('deep_analysis.period'),
            dataIndex: 'period',
            key: 'period',
            render: (_, record) => `${record.start} ~ ${record.end}`
        },
        {
            title: t('deep_analysis.depth'),
            dataIndex: 'depth',
            key: 'depth',
            render: (val) => (
                <Text type="danger">{(val * 100).toFixed(2)}%</Text>
            ),
            sorter: (a, b) => a.depth - b.depth
        },
        {
            title: t('deep_analysis.duration_days'),
            dataIndex: 'duration',
            key: 'duration',
            render: (val) => `${val} ${t('deep_analysis.days')}`,
            sorter: (a, b) => a.duration - b.duration
        },
        {
            title: t('deep_analysis.status'),
            dataIndex: 'ongoing',
            key: 'ongoing',
            render: (val) => val ? (
                <Text type="warning">{t('deep_analysis.ongoing')}</Text>
            ) : (
                <Text type="success">{t('deep_analysis.recovered')}</Text>
            )
        }
    ], [t])

    if (!data || !data.counts?.length) {
        return (
            <Card
                title={
                    <Space>
                        <FallOutlined />
                        {t('deep_analysis.drawdown_dist')}
                    </Space>
                }
            >
                <Empty description={t('deep_analysis.no_data')} />
            </Card>
        )
    }

    const { max_drawdown, avg_drawdown, drawdown_periods } = data

    return (
        <Card
            title={
                <Space>
                    <FallOutlined />
                    {t('deep_analysis.drawdown_dist')}
                </Space>
            }
        >
            <Row gutter={24}>
                <Col xs={24} md={10}>
                    <Row gutter={16} style={{ marginBottom: 16 }}>
                        <Col span={12}>
                            <Statistic
                                title={t('deep_analysis.max_drawdown')}
                                value={(max_drawdown * 100).toFixed(2)}
                                suffix="%"
                                valueStyle={{ color: '#ef4444' }}
                            />
                        </Col>
                        <Col span={12}>
                            <Statistic
                                title={t('deep_analysis.avg_drawdown')}
                                value={(avg_drawdown * 100).toFixed(2)}
                                suffix="%"
                                valueStyle={{ color: '#f97316' }}
                            />
                        </Col>
                    </Row>
                    <ReactECharts
                        option={histogramOption}
                        style={{ height: 200 }}
                        opts={{ renderer: 'svg' }}
                    />
                </Col>
                <Col xs={24} md={14}>
                    <Text strong style={{ marginBottom: 8, display: 'block' }}>
                        {t('deep_analysis.top_drawdown_periods')}
                    </Text>
                    <Table
                        dataSource={drawdown_periods?.map((p, idx) => ({ ...p, key: idx }))}
                        columns={columns}
                        size="small"
                        pagination={false}
                        scroll={{ y: 240 }}
                    />
                </Col>
            </Row>
        </Card>
    )
}

export default DrawdownDistribution
