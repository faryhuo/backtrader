import React, { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import ReactECharts from 'echarts-for-react'
import { Card, Empty, Space, Descriptions, Typography } from 'antd'
import { BarChartOutlined } from '@ant-design/icons'

const { Text } = Typography

/**
 * ReturnsDistribution - Shows histogram of daily returns with statistics.
 */
const ReturnsDistribution = ({ data }) => {
    const { t } = useTranslation()

    const option = useMemo(() => {
        if (!data || !data.bins || !data.strategy_counts) {
            return null
        }

        const { bins, strategy_counts } = data

        // Create bin labels
        const binLabels = []
        for (let i = 0; i < bins.length - 1; i++) {
            binLabels.push(`${(bins[i] * 100).toFixed(2)}%`)
        }

        return {
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'shadow' },
                formatter: (params) => {
                    const idx = params[0].dataIndex
                    const pct1 = (bins[idx] * 100).toFixed(2)
                    const pct2 = (bins[idx + 1] * 100).toFixed(2)
                    return `${pct1}% ~ ${pct2}%<br/>${t('deep_analysis.count')}: ${strategy_counts[idx]}`
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
                    fontSize: 10,
                    interval: Math.floor(binLabels.length / 10)
                },
                name: t('deep_analysis.daily_return'),
                nameLocation: 'center',
                nameGap: 45
            },
            yAxis: {
                type: 'value',
                name: t('deep_analysis.count'),
                nameLocation: 'center',
                nameGap: 40
            },
            series: [{
                name: t('deep_analysis.returns_dist'),
                type: 'bar',
                data: strategy_counts,
                itemStyle: {
                    color: (params) => {
                        // Color based on bin position (negative = red, positive = green)
                        const idx = params.dataIndex
                        const binMid = (bins[idx] + bins[idx + 1]) / 2
                        return binMid < 0 ? '#ef4444' : '#22c55e'
                    }
                },
                barWidth: '90%'
            }]
        }
    }, [data, t])

    if (!data || !data.strategy_counts?.length) {
        return (
            <Card
                title={
                    <Space>
                        <BarChartOutlined />
                        {t('deep_analysis.returns_dist')}
                    </Space>
                }
            >
                <Empty description={t('deep_analysis.no_data')} />
            </Card>
        )
    }

    const stats = data.statistics || {}

    return (
        <Card
            title={
                <Space>
                    <BarChartOutlined />
                    {t('deep_analysis.returns_dist')}
                </Space>
            }
        >
            <ReactECharts
                option={option}
                style={{ height: 220 }}
                opts={{ renderer: 'svg' }}
            />
            <Descriptions
                size="small"
                column={{ xs: 2, sm: 3, md: 4 }}
                style={{ marginTop: 12 }}
            >
                <Descriptions.Item label={t('deep_analysis.mean_return')}>
                    <Text type={stats.mean >= 0 ? 'success' : 'danger'}>
                        {(stats.mean * 100).toFixed(3)}%
                    </Text>
                </Descriptions.Item>
                <Descriptions.Item label={t('deep_analysis.std_dev')}>
                    {(stats.std * 100).toFixed(3)}%
                </Descriptions.Item>
                <Descriptions.Item label={t('deep_analysis.skewness')}>
                    {stats.skewness?.toFixed(3) ?? 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label={t('deep_analysis.kurtosis')}>
                    {stats.kurtosis?.toFixed(3) ?? 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label={t('deep_analysis.var_95')}>
                    <Text type="danger">
                        {(stats.var_95 * 100).toFixed(3)}%
                    </Text>
                </Descriptions.Item>
                <Descriptions.Item label={t('deep_analysis.cvar_95')}>
                    <Text type="danger">
                        {(stats.cvar_95 * 100).toFixed(3)}%
                    </Text>
                </Descriptions.Item>
            </Descriptions>
        </Card>
    )
}

export default ReturnsDistribution
